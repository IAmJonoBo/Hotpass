"""Prefect orchestration for the Hotpass refinement pipeline.

The flow layer coordinates retries, logging, and archiving behaviour around
the core pipeline runner. When Prefect is unavailable the module exposes
lightweight no-op decorators so CLI workflows can continue operating during
unit tests or constrained deployments.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
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
_prefect_handlers: Any = None


def _noop_prefect_decorator(*_args: Any, **_kwargs: Any) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        return func

    return decorator


try:  # pragma: no cover - verified via unit tests
    from prefect import flow as prefect_flow_decorator
    from prefect import task as prefect_task_decorator
    from prefect.logging import get_run_logger as prefect_get_run_logger
    from prefect.logging import handlers as prefect_handlers
except ImportError:  # pragma: no cover - exercised in fallback tests
    PREFECT_AVAILABLE = False
else:
    PREFECT_AVAILABLE = True
    _prefect_flow_decorator = prefect_flow_decorator
    _prefect_task_decorator = prefect_task_decorator
    _prefect_get_run_logger = prefect_get_run_logger
    _prefect_handlers = prefect_handlers
    _console_handler_cls = None
    if _prefect_handlers is not None:
        _console_handler_cls = getattr(_prefect_handlers, "ConsoleHandler", None)
        if _console_handler_cls is None:
            _console_handler_cls = getattr(
                _prefect_handlers, "PrefectConsoleHandler", None
            )

    if _console_handler_cls is not None:
        _prefect_console_emit = _console_handler_cls.emit

        def _safe_console_emit(self: Any, record: logging.LogRecord) -> None:
            console = getattr(self, "console", None)
            file_obj = getattr(console, "file", None)
            if getattr(file_obj, "closed", False):
                return None

            try:
                _prefect_console_emit(self, record)
            except ValueError:  # pragma: no cover - depends on runtime shutdown
                return None

        _console_handler_cls.emit = _safe_console_emit  # type: ignore[assignment]


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
    logger.info(f"Running pipeline with input_dir={config.input_dir}")

    start_time = time.time()

    result = run_pipeline(config)

    elapsed = time.time() - start_time

    logger.info(
        f"Pipeline completed in {elapsed:.2f} seconds - "
        f"{len(result.refined)} organizations processed"
    )

    return {
        "success": result.quality_report.expectations_passed,
        "total_records": len(result.refined),
        "elapsed_seconds": elapsed,
        "quality_report": result.quality_report.to_dict(),
        "output_path": str(config.output_path),
    }


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
    logger.info(f"Starting Hotpass refinement pipeline (profile: {profile_name})")

    # Load the profile
    profile = get_default_profile(profile_name)

    # Build configuration
    config = PipelineConfig(
        input_dir=Path(input_dir),
        output_path=Path(output_path),
        industry_profile=profile,
        excel_options=ExcelReadOptions(chunk_size=excel_chunk_size),
    )

    # Handle archive settings manually since PipelineConfig doesn't have these fields
    # We'll need to call archiving separately if needed

    # Execute pipeline
    result = run_pipeline_task(config)

    # Handle archiving if requested
    if archive:
        logger.info("Creating archive from output file...")
        try:
            archive_dir = Path(dist_dir)
            archive_dir.mkdir(parents=True, exist_ok=True)
            archive_path = create_refined_archive(
                excel_path=Path(result["output_path"]),
                archive_dir=archive_dir,
            )
            logger.info(f"Archive created: {archive_path}")
            result["archive_path"] = str(archive_path)
        except Exception as e:
            logger.error(f"Failed to create archive: {e}")
            # Don't fail the entire flow for archiving errors
            result["archive_error"] = str(e)

    logger.info(
        f"Pipeline flow completed - "
        f"Status: {'SUCCESS' if result['success'] else 'VALIDATION_FAILED'}"
    )

    return result


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

    serve(deployment)  # type: ignore


if __name__ == "__main__":
    # Run the flow directly for testing
    result = refinement_pipeline_flow()
    print(f"\nPipeline execution result: {result}")
