"""Prefect orchestration for the Hotpass refinement pipeline.

The flow layer coordinates retries, logging, and archiving behaviour around
the core pipeline runner. When Prefect is unavailable the module exposes
lightweight no-op decorators so CLI workflows can continue operating during
unit tests or constrained deployments.
"""

from __future__ import annotations

import logging
import os
import shutil
import time
import zipfile
from collections.abc import Callable, Mapping, MutableSequence, Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar, cast

from .artifacts import create_refined_archive
from .config import get_default_profile
from .pipeline import PipelineConfig, run_pipeline

if TYPE_CHECKING:  # pragma: no cover - typing aids
    from hotpass.config_schema import HotpassConfig

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


prefect_concurrency: Callable[..., Any] | None

try:  # pragma: no cover - optional Prefect feature
    from prefect.concurrency.asyncio import concurrency as _prefect_concurrency
except Exception:  # pragma: no cover - Prefect may be unavailable in tests
    prefect_concurrency = None
else:
    prefect_concurrency = cast(Callable[..., Any], _prefect_concurrency)


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


class AgentApprovalError(PipelineOrchestrationError):
    """Raised when agent requests fail policy or approval checks."""


@dataclass(frozen=True, slots=True)
class PipelineRunOptions:
    """Configuration required to execute the pipeline once."""

    config: HotpassConfig
    profile_name: str | None = None
    runner: Callable[..., Any] | None = None
    runner_kwargs: Mapping[str, Any] | None = None


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


@dataclass(frozen=True, slots=True)
class AgenticRequest:
    """Model a brokered MCP request handed to Prefect."""

    request_id: str
    agent_name: str
    role: str
    tool: str
    action: str
    parameters: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class AgentToolPolicy:
    """Allowed tools per role and auto-approval rules."""

    allowed_tools_by_role: Mapping[str, frozenset[str]]
    auto_approved_roles: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        normalised = {
            role: frozenset(tools) for role, tools in self.allowed_tools_by_role.items()
        }
        object.__setattr__(self, "allowed_tools_by_role", normalised)
        object.__setattr__(
            self, "auto_approved_roles", frozenset(self.auto_approved_roles)
        )

    def is_tool_allowed(self, role: str, tool: str) -> bool:
        allowed = self.allowed_tools_by_role.get(role)
        if not allowed:
            return False
        return "*" in allowed or tool in allowed

    def requires_manual_approval(self, role: str) -> bool:
        return role not in self.auto_approved_roles


@dataclass(frozen=True, slots=True)
class AgentApprovalDecision:
    """Outcome of a manual review for an agent request."""

    approved: bool
    approver: str
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class AgentAuditRecord:
    """Audit trail entry produced for each agent action."""

    request_id: str
    agent_name: str
    role: str
    tool: str
    action: str
    status: str
    approved: bool
    approver: str
    timestamp: datetime
    notes: str | None = None
    result: Mapping[str, Any] | None = None


def _normalise_parameters(parameters: Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(parameters, dict):
        return parameters
    return {key: parameters[key] for key in parameters}


def _pipeline_options_from_request(request: AgenticRequest) -> PipelineRunOptions:
    parameters = _normalise_parameters(request.parameters)
    pipeline_payload = parameters.get("pipeline")
    if not isinstance(pipeline_payload, Mapping):
        raise AgentApprovalError("Agent request missing pipeline configuration payload")

    payload = _normalise_parameters(pipeline_payload)
    try:
        input_dir = Path(str(payload["input_dir"]))
        output_path = Path(str(payload["output_path"]))
        profile_name = str(payload.get("profile_name", "aviation"))
    except KeyError as exc:  # pragma: no cover - defensive, asserted via tests
        raise AgentApprovalError(f"Missing pipeline parameter: {exc.args[0]}") from exc

    archive = bool(payload.get("archive", False))
    archive_dir_value = payload.get("archive_dir")
    excel_chunk_size_value = payload.get("excel_chunk_size")

    config_updates: dict[str, Any] = {
        "pipeline": {
            "input_dir": input_dir,
            "output_path": output_path,
            "archive": archive,
        }
    }

    if archive_dir_value is not None:
        config_updates["pipeline"]["dist_dir"] = Path(str(archive_dir_value))
    if excel_chunk_size_value is not None:
        config_updates["pipeline"]["excel_chunk_size"] = int(excel_chunk_size_value)

    from hotpass.config_schema import HotpassConfig

    config = HotpassConfig().merge(config_updates)

    if profile_name:
        industry = get_default_profile(profile_name)
        config = config.merge({"profile": industry.to_dict()})

    return PipelineRunOptions(config=config, profile_name=profile_name)


@task(name="evaluate-agent-request", retries=0)
def evaluate_agent_request(
    request: AgenticRequest,
    policy: AgentToolPolicy,
    approval: AgentApprovalDecision | None = None,
) -> AgentApprovalDecision:
    """Validate the agent request against the policy and manual approvals."""

    logger = get_run_logger()
    if not policy.is_tool_allowed(request.role, request.tool):
        reason = f"Role '{request.role}' is not permitted to use tool '{request.tool}'"
        _safe_log(logger, logging.WARNING, reason)
        raise AgentApprovalError(reason)

    if policy.requires_manual_approval(request.role):
        if approval is None or not approval.approved:
            reason = "Manual approval required for role"
            _safe_log(logger, logging.WARNING, reason)
            raise AgentApprovalError(reason)
        return approval

    if approval is not None:
        if not approval.approved:
            reason = approval.notes or "Manual approval denied"
            _safe_log(logger, logging.WARNING, reason)
            raise AgentApprovalError(reason)
        return approval

    auto_approver = f"policy:{request.role}"
    _safe_log(
        logger, logging.INFO, "Auto-approving agent request %s", request.request_id
    )
    return AgentApprovalDecision(
        approved=True,
        approver=auto_approver,
        notes="Auto-approved by policy",
    )


@task(name="log-agent-action", retries=0)
def log_agent_action(
    record: AgentAuditRecord,
    log_sink: MutableSequence[AgentAuditRecord] | None = None,
) -> AgentAuditRecord:
    """Persist agent audit records to a sink and Prefect logs."""

    logger = get_run_logger()
    _safe_log(
        logger,
        logging.INFO,
        "Agent %s performed %s (status=%s, approved=%s)",
        record.agent_name,
        record.action,
        record.status,
        record.approved,
    )
    if log_sink is not None:
        log_sink.append(record)
    return record


def broker_agent_run(
    request: AgenticRequest,
    policy: AgentToolPolicy,
    *,
    approval: AgentApprovalDecision | None = None,
    log_sink: MutableSequence[AgentAuditRecord] | None = None,
) -> PipelineRunSummary:
    """Broker an agent-triggered pipeline execution with approvals and logging."""

    timestamp = datetime.now(tz=UTC)
    try:
        decision = evaluate_agent_request(
            request=request, policy=policy, approval=approval
        )
    except AgentApprovalError as exc:
        log_agent_action(
            AgentAuditRecord(
                request_id=request.request_id,
                agent_name=request.agent_name,
                role=request.role,
                tool=request.tool,
                action=request.action,
                status="denied",
                approved=False,
                approver=(
                    "manual"
                    if policy.requires_manual_approval(request.role)
                    else "policy"
                ),
                timestamp=timestamp,
                notes=str(exc),
            ),
            log_sink,
        )
        raise

    log_agent_action(
        AgentAuditRecord(
            request_id=request.request_id,
            agent_name=request.agent_name,
            role=request.role,
            tool=request.tool,
            action=request.action,
            status="approved",
            approved=True,
            approver=decision.approver,
            timestamp=timestamp,
            notes=decision.notes,
        ),
        log_sink,
    )

    options = _pipeline_options_from_request(request)

    try:
        summary = run_pipeline_once(options)
    except Exception as exc:  # pragma: no cover - exercised via unit tests
        log_agent_action(
            AgentAuditRecord(
                request_id=request.request_id,
                agent_name=request.agent_name,
                role=request.role,
                tool=request.tool,
                action=request.action,
                status="failed",
                approved=True,
                approver=decision.approver,
                timestamp=datetime.now(tz=UTC),
                notes=str(exc),
            ),
            log_sink,
        )
        raise

    log_agent_action(
        AgentAuditRecord(
            request_id=request.request_id,
            agent_name=request.agent_name,
            role=request.role,
            tool=request.tool,
            action=request.action,
            status="executed",
            approved=True,
            approver=decision.approver,
            timestamp=datetime.now(tz=UTC),
            result=summary.to_payload(),
        ),
        log_sink,
    )

    return summary


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
            raise PipelineOrchestrationError(
                f"Failed to create archive: {exc}"
            ) from exc

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

    config = options.config
    runner = options.runner or run_pipeline
    pipeline_config = config.to_pipeline_config()

    return _execute_pipeline(
        pipeline_config,
        runner=runner,
        runner_kwargs=options.runner_kwargs,
        archive=config.pipeline.archive,
        archive_dir=config.pipeline.dist_dir,
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
    _safe_log(
        logger, logging.INFO, "Running pipeline with input_dir=%s", config.input_dir
    )

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

    payload = summary.to_payload()

    def _coerce_flag(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, int | float):
            return bool(value)
        return False

    payload["backfill"] = _coerce_flag(getattr(config, "backfill", False))
    payload["incremental"] = _coerce_flag(getattr(config, "incremental", False))

    since_value = getattr(config, "since", None)
    if isinstance(since_value, datetime):
        payload["since"] = since_value.isoformat()
    elif isinstance(since_value, str):
        payload["since"] = since_value

    return payload


def _lookup_nested(
    mapping: Mapping[str, Any] | None, keys: tuple[str, ...]
) -> Any | None:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, Mapping) or key not in current:
            return None
        current = current[key]
    return current


def _sanitise_component(value: str) -> str:
    cleaned = value.replace("\\", "-").replace("/", "-").strip()
    return cleaned or "default"


def _format_archive_path(
    root: Path, pattern: str, run_date: date, version: str
) -> Path:
    try:
        relative = pattern.format(date=run_date, version=version)
    except Exception as exc:  # pragma: no cover - formatting errors are unexpected
        msg = f"Invalid archive pattern '{pattern}': {exc}"
        raise PipelineOrchestrationError(msg) from exc
    return (root / Path(relative)).expanduser()


@task(name="rehydrate-archive", retries=2, retry_delay_seconds=5)
def rehydrate_archive_task(archive_path: Path, restore_dir: Path) -> Path:
    if not archive_path.exists():
        msg = f"Archive not found: {archive_path}"
        raise FileNotFoundError(msg)
    if restore_dir.exists():
        shutil.rmtree(restore_dir)
    restore_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "r") as zip_handle:
        zip_handle.extractall(restore_dir)
    return restore_dir


def _execute_with_concurrency(
    key: str,
    slots: int,
    callback: Callable[[], PipelineRunSummary],
) -> PipelineRunSummary:
    if prefect_concurrency is None or slots <= 0:
        return callback()

    try:
        import anyio
    except Exception:  # pragma: no cover - fallback when anyio missing
        return callback()

    async def _runner() -> PipelineRunSummary:
        try:
            async with prefect_concurrency(key, occupy=slots):  # type: ignore[misc]
                return await anyio.to_thread.run_sync(callback)
        except Exception as exc:  # pragma: no cover - concurrency fallback
            _safe_log(
                logger,
                logging.WARNING,
                "Prefect concurrency unavailable for key %s (%s); running synchronously.",
                key,
                exc,
            )
            return await anyio.to_thread.run_sync(callback)

    try:
        return anyio.run(_runner)
    except Exception as exc:  # pragma: no cover - execution fallback
        _safe_log(
            logger,
            logging.WARNING,
            "Failed to acquire Prefect concurrency for key %s (%s); running synchronously.",
            key,
            exc,
        )
        return callback()


def _coerce_run_date(raw: str | date) -> date:
    if isinstance(raw, date):
        return raw
    try:
        return date.fromisoformat(str(raw))
    except ValueError as exc:
        msg = f"Invalid run_date value: {raw}"
        raise PipelineOrchestrationError(msg) from exc


def _coerce_since(raw: datetime | str | None) -> datetime | None:
    if raw is None:
        return None
    if isinstance(raw, datetime):
        candidate = raw
    else:
        try:
            candidate = datetime.fromisoformat(str(raw))
        except ValueError as exc:
            msg = f"Invalid since value: {raw}"
            raise PipelineOrchestrationError(msg) from exc
    if candidate.tzinfo is None:
        candidate = candidate.replace(tzinfo=UTC)
    return candidate


@flow(name="hotpass-backfill", log_prints=True, validate_parameters=False)
def backfill_pipeline_flow(
    runs: Sequence[Mapping[str, Any]] | Sequence[dict[str, Any]],
    *,
    archive_root: str,
    restore_root: str,
    archive_pattern: str = "hotpass-inputs-{date:%Y%m%d}-v{version}.zip",
    base_config: Mapping[str, Any] | None = None,
    parameters: Mapping[str, Any] | None = None,
    concurrency_limit: int = 1,
    concurrency_key: str = "hotpass/backfill",
) -> dict[str, Any]:
    logger = get_run_logger()

    runs_normalised: list[dict[str, str]] = []
    for entry in runs:
        run_date_raw = entry.get("run_date")
        version_raw = entry.get("version")
        if run_date_raw is None or version_raw is None:
            msg = "Each run must include 'run_date' and 'version' keys"
            raise PipelineOrchestrationError(msg)
        run_date_value = _coerce_run_date(run_date_raw)
        version_value = str(version_raw)
        runs_normalised.append(
            {"run_date": run_date_value.isoformat(), "version": version_value}
        )

    archive_root_path = Path(archive_root)
    restore_root_path = Path(restore_root)
    restore_root_path.mkdir(parents=True, exist_ok=True)
    outputs_root = restore_root_path / "outputs"
    outputs_root.mkdir(parents=True, exist_ok=True)

    from hotpass.config_schema import HotpassConfig

    if base_config is None:
        base_payload: Mapping[str, Any] = HotpassConfig().model_dump(mode="python")
    elif isinstance(base_config, Mapping):
        base_payload = base_config
    else:
        msg = "base_config must be a mapping if provided"
        raise PipelineOrchestrationError(msg)

    total_records = 0
    total_elapsed = 0.0
    successes = 0
    run_payloads: list[dict[str, Any]] = []

    for run in runs_normalised:
        iso_date = run["run_date"]
        version = run["version"]
        run_date_value = _coerce_run_date(iso_date)
        archive_path = _format_archive_path(
            archive_root_path,
            archive_pattern,
            run_date_value,
            version,
        )
        restore_dir = restore_root_path / f"{iso_date}--{_sanitise_component(version)}"

        _safe_log(
            logger,
            logging.INFO,
            "Rehydrating archive %s to %s",
            archive_path,
            restore_dir,
        )

        try:
            extracted = rehydrate_archive_task(archive_path, restore_dir)
        except FileNotFoundError as exc:
            msg = f"Archived inputs not found for {iso_date} version {version}: {archive_path}"
            raise PipelineOrchestrationError(msg) from exc
        except Exception as exc:  # pragma: no cover - defensive guard
            msg = f"Failed to extract archive for {iso_date} version {version}: {exc}"
            raise PipelineOrchestrationError(msg) from exc

        config_model = HotpassConfig.model_validate(dict(base_payload))
        if parameters:
            config_model = config_model.merge(parameters)

        output_path = (
            outputs_root / f"refined-{iso_date}-{_sanitise_component(version)}.xlsx"
        )
        run_updates: dict[str, Any] = {
            "pipeline": {
                "input_dir": extracted,
                "output_path": output_path,
                "dist_dir": outputs_root,
                "backfill": True,
                "incremental": False,
                "run_id": f"backfill-{iso_date}-{_sanitise_component(version)}",
            }
        }
        if _lookup_nested(parameters, ("pipeline", "archive")) is None:
            run_updates["pipeline"]["archive"] = False
        if _lookup_nested(parameters, ("pipeline", "since")) is None:
            run_updates["pipeline"]["since"] = datetime.combine(
                run_date_value, datetime.min.time(), tzinfo=UTC
            )

        config_model = config_model.merge(run_updates)

        def _invoke(
            config_snapshot: HotpassConfig = config_model,
        ) -> PipelineRunSummary:
            profile_name = None
            profile = getattr(config_snapshot, "profile", None)
            if profile is not None:
                profile_name = getattr(profile, "name", None)
            return run_pipeline_once(
                PipelineRunOptions(
                    config=config_snapshot,
                    profile_name=profile_name,
                )
            )

        summary = _execute_with_concurrency(concurrency_key, concurrency_limit, _invoke)

        total_records += summary.total_records
        total_elapsed += summary.elapsed_seconds
        if summary.success:
            successes += 1

        run_payload = summary.to_payload()
        run_payload.update({"run_date": iso_date, "version": version})
        run_payloads.append(run_payload)

    metrics = {
        "total_runs": len(run_payloads),
        "successful_runs": successes,
        "failed_runs": len(run_payloads) - successes,
        "total_records": total_records,
        "total_elapsed_seconds": total_elapsed,
    }

    _safe_log(
        logger,
        logging.INFO,
        "Completed backfill window - %d runs, %d successes",
        metrics["total_runs"],
        metrics["successful_runs"],
    )

    return {"runs": run_payloads, "metrics": metrics}


@flow(name="hotpass-refinement-pipeline", log_prints=True, validate_parameters=False)
def refinement_pipeline_flow(
    input_dir: str = "./data",
    output_path: str = "./data/refined_data.xlsx",
    profile_name: str = "aviation",
    excel_chunk_size: int | None = None,
    archive: bool = False,
    dist_dir: str = "./dist",
    backfill: bool = False,
    incremental: bool = False,
    since: datetime | str | None = None,
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
        "Starting Hotpass refinement pipeline (profile=%s, backfill=%s, incremental=%s, since=%s)",
        profile_name,
        backfill,
        incremental,
        since,
    )

    from hotpass.config_schema import HotpassConfig

    resolved_since = _coerce_since(since)

    run_id = None
    flow_run_name = None
    scheduled_start_time = None
    try:
        from prefect.runtime import flow_run

        run_id = getattr(flow_run, "id", None)
        flow_run_name = getattr(flow_run, "name", None)
        scheduled_start_time = getattr(flow_run, "expected_start_time", None)
        _safe_log(
            logger,
            logging.DEBUG,
            "Prefect runtime resolved (run_id=%s, name=%s, scheduled=%s)",
            run_id,
            flow_run_name,
            scheduled_start_time,
        )
    except Exception:  # pragma: no cover - runtime availability only
        pass

    config_updates: dict[str, Any] = {
        "pipeline": {
            "input_dir": Path(input_dir),
            "output_path": Path(output_path),
            "archive": archive,
            "dist_dir": Path(dist_dir),
            "backfill": bool(backfill),
            "incremental": bool(incremental),
        }
    }
    if resolved_since is not None:
        config_updates["pipeline"]["since"] = resolved_since
    if run_id:
        config_updates["pipeline"]["run_id"] = run_id
    if flow_run_name:
        config_updates.setdefault("orchestrator", {})[
            "run_name_template"
        ] = flow_run_name

    if excel_chunk_size is not None:
        config_updates["pipeline"]["excel_chunk_size"] = int(excel_chunk_size)

    config = HotpassConfig().merge(config_updates)
    profile = get_default_profile(profile_name)

    profile_payload: Mapping[str, Any] | None = None
    model_dump = getattr(profile, "model_dump", None)
    if callable(model_dump):
        candidate = model_dump()
        if isinstance(candidate, Mapping):
            profile_payload = candidate
    if profile_payload is None and hasattr(profile, "to_dict"):
        candidate = profile.to_dict()
        if isinstance(candidate, Mapping):
            profile_payload = candidate
    if profile_payload is None and isinstance(profile, Mapping):
        profile_payload = profile

    if profile_payload is not None:
        config = config.merge({"profile": profile_payload})

    summary = run_pipeline_once(
        PipelineRunOptions(config=config, profile_name=profile_name)
    )

    payload = summary.to_payload()
    if run_id:
        payload["run_id"] = run_id
    if resolved_since is not None:
        payload["since"] = resolved_since.isoformat()
    payload["backfill"] = bool(backfill)
    payload["incremental"] = bool(incremental)

    _safe_log(
        logger,
        logging.INFO,
        "Pipeline flow completed - Status: %s",
        "SUCCESS" if summary.success else "VALIDATION_FAILED",
    )

    return payload


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
