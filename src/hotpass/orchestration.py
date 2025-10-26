"""Prefect orchestration for the Hotpass refinement pipeline.

The flow layer coordinates retries, logging, and archiving behaviour around
the core pipeline runner. When Prefect is unavailable the module exposes
lightweight no-op decorators so CLI workflows can continue operating during
unit tests or constrained deployments.
"""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar, cast

from .artifacts import create_refined_archive
from .config import get_default_profile
from .data_sources import ExcelReadOptions
from .pipeline import PipelineConfig, run_pipeline

F = TypeVar("F", bound=Callable[..., Any])

_prefect_flow_decorator: Callable[..., Callable[[F], F]] | None = None
_prefect_task_decorator: Callable[..., Callable[[F], F]] | None = None
_prefect_get_run_logger: Callable[..., Any] | None = None


def _noop_prefect_decorator(*_args: Any, **_kwargs: Any) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        return func

    return decorator


try:  # pragma: no cover - verified via unit tests
    from prefect import flow as prefect_flow_decorator
    from prefect import task as prefect_task_decorator
    from prefect.logging import get_run_logger as prefect_get_run_logger
except ImportError:  # pragma: no cover - exercised in fallback tests
    PREFECT_AVAILABLE = False
else:
    PREFECT_AVAILABLE = True
    _prefect_flow_decorator = prefect_flow_decorator
    _prefect_task_decorator = prefect_task_decorator
    _prefect_get_run_logger = prefect_get_run_logger

    if os.getenv("HOTPASS_ENABLE_PREFECT_RUNTIME", "0") != "1":
        PREFECT_AVAILABLE = False
        _prefect_flow_decorator = None
        _prefect_task_decorator = None
        _prefect_get_run_logger = None


if _prefect_flow_decorator is not None:
    flow: Callable[..., Callable[[F], F]] = cast(
        Callable[..., Callable[[F], F]], _prefect_flow_decorator
    )
else:

    def flow(*_args: Any, **_kwargs: Any) -> Callable[[F], F]:
        return _noop_prefect_decorator(*_args, **_kwargs)


if _prefect_task_decorator is not None:
    task: Callable[..., Callable[[F], F]] = cast(
        Callable[..., Callable[[F], F]], _prefect_task_decorator
    )
else:

    def task(*_args: Any, **_kwargs: Any) -> Callable[[F], F]:
        return _noop_prefect_decorator(*_args, **_kwargs)


if _prefect_get_run_logger is not None:

    def get_run_logger(*args: Any, **kwargs: Any) -> logging.Logger:
        """Proxy Prefect's logger helper while supporting the fallback stub."""

        logger_callable = _prefect_get_run_logger
        if logger_callable is None:  # pragma: no cover - defensive
            return logging.getLogger("hotpass.orchestration")

        logger_or_adapter = logger_callable(*args, **kwargs)
        if isinstance(logger_or_adapter, logging.Logger):
            return logger_or_adapter
        adapter_logger = getattr(logger_or_adapter, "logger", None)
        if isinstance(adapter_logger, logging.Logger):
            return adapter_logger
        return logging.getLogger("hotpass.orchestration")

else:

    def get_run_logger(*_args: Any, **_kwargs: Any) -> logging.Logger:
        return logging.getLogger("hotpass.orchestration")


logger = logging.getLogger(__name__)


class PipelineOrchestrationError(RuntimeError):
    """Raised when orchestration helpers encounter unrecoverable errors."""


@dataclass(frozen=True, slots=True)
class PipelineRunOptions:
    """Configuration required to execute the pipeline once."""

    input_dir: Path
    output_path: Path
    profile_name: str
    excel_chunk_size: int | None = None
    archive: bool = False
    archive_dir: Path | None = None
    runner: Callable[..., Any] | None = None
    runner_kwargs: Mapping[str, Any] | None = None
    profile_loader: Callable[[str], Any] | None = None


@dataclass(frozen=True, slots=True)
class PipelineRunSummary:
    """Structured payload describing a pipeline execution."""

    success: bool
    total_records: int
    elapsed_seconds: float
    output_path: Path
    quality_report: Mapping[str, Any]
    archive_path: Path | None = None

    def to_payload(self) -> dict[str, Any]:
        """Serialise the summary for CLI and Prefect consumers."""

        payload: dict[str, Any] = {
            "success": self.success,
            "total_records": self.total_records,
            "elapsed_seconds": self.elapsed_seconds,
            "quality_report": dict(self.quality_report),
            "output_path": str(self.output_path),
        }
        if self.archive_path is not None:
            payload["archive_path"] = str(self.archive_path)
        return payload


def _safe_log(logger_: logging.Logger, level: int, message: str, *args: Any) -> None:
    """Log a message while suppressing ValueErrors raised by closed handlers."""

    try:
        logger_.log(level, message, *args)
    except ValueError:  # pragma: no cover - depends on interpreter shutdown timing
        return None


def _execute_pipeline(
    config: PipelineConfig,
    *,
    runner: Callable[..., Any],
    runner_kwargs: Mapping[str, Any] | None,
    archive: bool,
    archive_dir: Path | None,
) -> PipelineRunSummary:
    """Execute the pipeline runner and return a structured summary."""

    start_time = time.time()
    result = runner(config, **(runner_kwargs or {}))
    elapsed = time.time() - start_time

    quality_report_dict: dict[str, Any] = {}
    success = True
    quality_report = getattr(result, "quality_report", None)
    if quality_report is not None:
        to_dict = getattr(quality_report, "to_dict", None)
        if callable(to_dict):
            quality_report_dict = cast(dict[str, Any], to_dict())
        success = bool(getattr(quality_report, "expectations_passed", True))

    archive_path: Path | None = None
    if archive:
        archive_root = archive_dir or config.output_path.parent
        try:
            archive_root = Path(archive_root)
            archive_root.mkdir(parents=True, exist_ok=True)
            archive_path = create_refined_archive(
                excel_path=config.output_path,
                archive_dir=archive_root,
            )
        except Exception as exc:  # pragma: no cover - exercised via unit tests
            raise PipelineOrchestrationError(f"Failed to create archive: {exc}") from exc

    total_records = len(getattr(result, "refined", []))

    return PipelineRunSummary(
        success=success,
        total_records=total_records,
        elapsed_seconds=elapsed,
        output_path=config.output_path,
        quality_report=quality_report_dict,
        archive_path=archive_path,
    )


def run_pipeline_once(options: PipelineRunOptions) -> PipelineRunSummary:
    """Execute the pipeline once using shared orchestration helpers."""

    profile_loader = options.profile_loader or get_default_profile
    profile = profile_loader(options.profile_name)

    config = PipelineConfig(
        input_dir=Path(options.input_dir),
        output_path=Path(options.output_path),
        industry_profile=profile,
        excel_options=ExcelReadOptions(chunk_size=options.excel_chunk_size),
    )

    runner = options.runner or run_pipeline

    return _execute_pipeline(
        config,
        runner=runner,
        runner_kwargs=options.runner_kwargs,
        archive=options.archive,
        archive_dir=options.archive_dir,
    )


@task(name="run-pipeline", retries=2, retry_delay_seconds=10)
def run_pipeline_task(
    config: PipelineConfig,
) -> dict[str, Any]:
    """Run the Hotpass pipeline as a Prefect task.

    Args:
        config: Pipeline configuration

    Returns:
        Pipeline execution results
    """
    logger = get_run_logger()
    _safe_log(logger, logging.INFO, "Running pipeline with input_dir=%s", config.input_dir)

    summary = _execute_pipeline(
        config,
        runner=run_pipeline,
        runner_kwargs=None,
        archive=False,
        archive_dir=None,
    )

    _safe_log(
        logger,
        logging.INFO,
        "Pipeline completed in %.2f seconds - %d organizations processed",
        summary.elapsed_seconds,
        summary.total_records,
    )

    return summary.to_payload()


@flow(name="hotpass-refinement-pipeline", log_prints=True, validate_parameters=False)
def refinement_pipeline_flow(
    input_dir: str = "./data",
    output_path: str = "./data/refined_data.xlsx",
    profile_name: str = "aviation",
    excel_chunk_size: int | None = None,
    archive: bool = False,
    dist_dir: str = "./dist",
) -> dict[str, Any]:
    """Main Hotpass refinement pipeline as a Prefect flow.

    Args:
        input_dir: Directory containing input Excel files
        output_path: Path for the output refined workbook
        profile_name: Name of the industry profile to use
        excel_chunk_size: Optional chunk size for Excel reading
        archive: Whether to create a packaged archive
        dist_dir: Directory for archive output

    Returns:
        Pipeline execution results dictionary
    """
    logger = get_run_logger()
    _safe_log(
        logger,
        logging.INFO,
        "Starting Hotpass refinement pipeline (profile: %s)",
        profile_name,
    )

    summary = run_pipeline_once(
        PipelineRunOptions(
            input_dir=Path(input_dir),
            output_path=Path(output_path),
            profile_name=profile_name,
            excel_chunk_size=excel_chunk_size,
            archive=archive,
            archive_dir=Path(dist_dir) if archive else None,
        )
    )

    _safe_log(
        logger,
        logging.INFO,
        "Pipeline flow completed - Status: %s",
        "SUCCESS" if summary.success else "VALIDATION_FAILED",
    )

    return summary.to_payload()


def deploy_pipeline(
    name: str = "hotpass-refinement",
    cron_schedule: str | None = None,
    work_pool: str | None = None,
) -> None:
    """Deploy the Hotpass pipeline to Prefect.

    Args:
        name: Deployment name
        cron_schedule: Optional cron schedule (e.g., "0 2 * * *" for daily at 2am)
        work_pool: Optional work pool name for execution
    """
    if not PREFECT_AVAILABLE:
        msg = "Prefect is not installed; deployment functionality is unavailable"
        logger.warning(msg)
        raise RuntimeError(msg)

    from prefect.deployments import serve

    # Note: deployment API may require adjustments based on Prefect version
    deployment = cast(Any, refinement_pipeline_flow).to_deployment(name=name)
    if work_pool:
        deployment.work_pool_name = work_pool  # type: ignore

    if cron_schedule:
        try:
            from prefect.server.schemas.schedules import CronSchedule
        except ImportError as exc:  # pragma: no cover - depends on Prefect extras
            raise RuntimeError("Prefect scheduling components are unavailable") from exc

        deployment.schedule = CronSchedule(cron=cron_schedule, timezone="UTC")  # type: ignore[attr-defined]

    serve(deployment)  # type: ignore


if __name__ == "__main__":
    # Run the flow directly for testing
    result = refinement_pipeline_flow()
    print(f"\nPipeline execution result: {result}")
