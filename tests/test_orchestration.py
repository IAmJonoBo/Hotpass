"""Tests for Prefect orchestration module."""

# ruff: noqa: E402

import importlib
import sys
import types
import zipfile
from collections.abc import Callable
from contextlib import asynccontextmanager
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import anyio
import pandas as pd
import pytest

_pandera_stub = types.ModuleType("pandera")
_pandera_pandas = types.ModuleType("pandera.pandas")
_pandera_errors = types.ModuleType("pandera.errors")


class _StubColumn:
    def __init__(self, *args, **kwargs) -> None:  # pragma: no cover - stub
        return


class _StubDataFrameSchema:
    def __init__(self, *args, **kwargs) -> None:  # pragma: no cover - stub
        return


_pandera_pandas.Column = _StubColumn
_pandera_pandas.DataFrameSchema = _StubDataFrameSchema
_pandera_stub.pandas = _pandera_pandas
_pandera_errors.SchemaErrors = type("SchemaErrors", (Exception,), {})
_pandera_stub.errors = _pandera_errors
sys.modules.setdefault("pandera", _pandera_stub)
sys.modules.setdefault("pandera.pandas", _pandera_pandas)
sys.modules.setdefault("pandera.errors", _pandera_errors)

_rapidfuzz_stub = types.ModuleType("rapidfuzz")
_rapidfuzz_fuzz = types.ModuleType("rapidfuzz.fuzz")
_rapidfuzz_fuzz.token_sort_ratio = lambda *args, **kwargs: 100.0
_rapidfuzz_fuzz.partial_ratio = lambda *args, **kwargs: 100.0
_rapidfuzz_fuzz.token_set_ratio = lambda *args, **kwargs: 100.0
_rapidfuzz_stub.fuzz = _rapidfuzz_fuzz
sys.modules.setdefault("rapidfuzz", _rapidfuzz_stub)
sys.modules.setdefault("rapidfuzz.fuzz", _rapidfuzz_fuzz)

from hotpass.config_schema import HotpassConfig

if TYPE_CHECKING:
    from hotpass.orchestration import PipelineRunOptions as PipelineRunOptionsType
    from hotpass.orchestration import PipelineRunSummary as PipelineRunSummaryType

pytest.importorskip("frictionless")

orchestration = importlib.import_module("hotpass.orchestration")

PipelineOrchestrationError = orchestration.PipelineOrchestrationError
PipelineRunOptions = orchestration.PipelineRunOptions
PipelineRunSummary = orchestration.PipelineRunSummary
backfill_pipeline_flow = orchestration.backfill_pipeline_flow
refinement_pipeline_flow = orchestration.refinement_pipeline_flow
run_pipeline_once = orchestration.run_pipeline_once
run_pipeline_task = orchestration.run_pipeline_task
_run_with_prefect_concurrency = orchestration._run_with_prefect_concurrency
_execute_with_concurrency = orchestration._execute_with_concurrency

if not TYPE_CHECKING:
    PipelineRunOptionsType = PipelineRunOptions  # type: ignore[assignment]
    PipelineRunSummaryType = PipelineRunSummary  # type: ignore[assignment]


def expect(condition: bool, message: str) -> None:
    """Raise a descriptive failure when the condition is false."""

    if not condition:
        pytest.fail(message)


@pytest.fixture(autouse=True)
def reset_orchestration(monkeypatch):
    """Ensure Prefect decorators do not retain state between tests."""

    monkeypatch.setattr(orchestration, "flow", orchestration.flow, raising=False)
    monkeypatch.setattr(orchestration, "task", orchestration.task, raising=False)


@pytest.fixture(autouse=True)
def disable_prefect_concurrency(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent tests from starting ephemeral Prefect servers."""

    @asynccontextmanager
    async def _noop_concurrency(*_args, **_kwargs):  # pragma: no cover - helper
        yield

    monkeypatch.setattr(
        orchestration,
        "prefect_concurrency",
        _noop_concurrency,
        raising=False,
    )


@pytest.fixture
def mock_pipeline_result():
    """Create a mock pipeline result."""
    result = Mock()
    result.refined = pd.DataFrame({"col": [1, 2, 3]})
    result.quality_report = Mock()
    result.quality_report.to_dict = Mock(return_value={"test": "data"})
    result.quality_report.expectations_passed = True
    return result


def test_run_pipeline_once_success(mock_pipeline_result, tmp_path):
    """The orchestration helper returns a structured summary on success."""
    config = HotpassConfig().merge(
        {
            "pipeline": {
                "input_dir": tmp_path,
                "output_path": tmp_path / "out.xlsx",
                "archive": True,
                "dist_dir": tmp_path / "dist",
            }
        }
    )
    options = PipelineRunOptions(config=config, profile_name="aviation")

    with (
        patch("hotpass.orchestration.run_pipeline") as mock_run,
        patch("hotpass.orchestration.create_refined_archive") as mock_archive,
    ):
        mock_run.return_value = mock_pipeline_result
        mock_archive.return_value = tmp_path / "dist" / "archive.zip"

        summary = run_pipeline_once(options)

    expect(summary.success is True, "Pipeline summary should mark execution as successful")
    expect(summary.total_records == 3, "Expected three records in the refined output")
    expect(
        summary.archive_path == tmp_path / "dist" / "archive.zip",
        "Archive path should include the dist directory",
    )


def test_run_pipeline_task_success(mock_pipeline_result, tmp_path):
    """Test successful pipeline task execution."""
    mock_config = Mock()
    mock_config.input_dir = Path("/tmp")
    mock_config.output_path = Path("/tmp/output.xlsx")

    with (
        patch("hotpass.orchestration.run_pipeline") as mock_run,
        patch("hotpass.orchestration.get_default_profile") as mock_profile,
    ):
        mock_run.return_value = mock_pipeline_result
        mock_profile.return_value = Mock()

        result = run_pipeline_task(mock_config)

        expect(result["success"] is True, "Task helper should mark execution as successful")
        assert result["total_records"] == 3
        assert "elapsed_seconds" in result
        assert result["backfill"] is False
        assert result["incremental"] is False
        assert result.get("since") is None
        assert "quality_report" in result


def test_run_pipeline_task_validation_failure(mock_pipeline_result):
    """Test pipeline task with validation failure."""
    mock_config = Mock()
    mock_config.input_dir = Path("/tmp")
    mock_config.output_path = Path("/tmp/output.xlsx")
    mock_pipeline_result.quality_report.expectations_passed = False

    with patch("hotpass.orchestration.run_pipeline") as mock_run:
        mock_run.return_value = mock_pipeline_result

        result = run_pipeline_task(mock_config)

        assert result["success"] is False


def test_run_pipeline_once_archiving_error(mock_pipeline_result, tmp_path):
    """Archiving failures raise a structured orchestration error."""
    config = HotpassConfig().merge(
        {
            "pipeline": {
                "input_dir": tmp_path,
                "output_path": tmp_path / "out.xlsx",
                "archive": True,
                "dist_dir": tmp_path / "dist",
            }
        }
    )
    options = PipelineRunOptions(config=config, profile_name="aviation")

    with (
        patch("hotpass.orchestration.run_pipeline") as mock_run,
        patch(
            "hotpass.orchestration.create_refined_archive",
            side_effect=ValueError("boom"),
        ),
    ):
        mock_run.return_value = mock_pipeline_result

        with pytest.raises(PipelineOrchestrationError) as exc:
            run_pipeline_once(options)

    assert "Failed to create archive" in str(exc.value)


def test_refinement_pipeline_flow(mock_pipeline_result, tmp_path):
    """Test the complete pipeline flow."""
    with (
        patch("hotpass.orchestration.run_pipeline") as mock_run,
        patch("hotpass.orchestration.get_default_profile") as mock_profile,
    ):
        mock_run.return_value = mock_pipeline_result
        mock_profile.return_value = Mock()

        result = refinement_pipeline_flow(
            input_dir=str(tmp_path),
            output_path=str(tmp_path / "output.xlsx"),
            profile_name="aviation",
        )

        assert result["success"] is True
        assert result["total_records"] == 3
        assert "elapsed_seconds" in result


def test_refinement_pipeline_flow_with_options(mock_pipeline_result, tmp_path):
    """Test pipeline flow with optional parameters."""
    with (
        patch("hotpass.orchestration.run_pipeline") as mock_run,
        patch("hotpass.orchestration.get_default_profile") as mock_profile,
        patch("hotpass.orchestration.create_refined_archive") as mock_archive,
    ):
        mock_run.return_value = mock_pipeline_result
        mock_profile.return_value = Mock()
        mock_archive.return_value = tmp_path / "dist" / "archive.zip"

        result = refinement_pipeline_flow(
            input_dir=str(tmp_path),
            output_path=str(tmp_path / "output.xlsx"),
            profile_name="generic",
            excel_chunk_size=1000,
            archive=True,
            dist_dir=str(tmp_path / "dist"),
        )

        assert result["success"] is True
        mock_run.assert_called_once()

        # Verify config was built with correct options
        config_arg = mock_run.call_args[0][0]
        assert config_arg.excel_options.chunk_size == 1000
        assert config_arg.backfill is False
        assert config_arg.incremental is False
        assert config_arg.since is None


def test_refinement_pipeline_flow_propagates_runtime_overrides(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Runtime flags should populate the canonical pipeline configuration."""

    captured: list[PipelineRunOptionsType] = []

    def _record_run(
        options: PipelineRunOptionsType,
    ) -> PipelineRunSummaryType:
        captured.append(options)
        return PipelineRunSummary(
            success=True,
            total_records=1,
            elapsed_seconds=0.25,
            output_path=tmp_path / "outputs" / "refined.xlsx",
            quality_report={"rows": 1},
        )

    monkeypatch.setattr(orchestration, "run_pipeline_once", _record_run)
    monkeypatch.setattr(
        orchestration,
        "get_default_profile",
        lambda _name: SimpleNamespace(model_dump=lambda: {"profile": "aviation"}),
    )
    monkeypatch.setattr(
        orchestration,
        "create_refined_archive",
        lambda *_args, **_kwargs: tmp_path / "dist" / "archive.zip",
    )

    since_iso = "2024-01-01T05:06:07+00:00"
    result = refinement_pipeline_flow(
        input_dir=str(tmp_path / "inputs"),
        output_path=str(tmp_path / "outputs" / "refined.xlsx"),
        profile_name="aviation",
        backfill=True,
        incremental=True,
        since=since_iso,
        telemetry_enabled=True,
        telemetry_exporters=["console"],
        telemetry_service_name="hotpass-prefect",
        telemetry_environment="staging",
        telemetry_resource_attributes={"deployment": "prefect"},
        telemetry_otlp_endpoint="http://localhost:4317",
        telemetry_otlp_metrics_endpoint="http://localhost:4318",
        telemetry_otlp_headers={"authorization": "token"},
        telemetry_otlp_insecure=True,
        telemetry_otlp_timeout=5.5,
    )

    expect(result["success"] is True, "Flow should surface success from pipeline summary.")
    expect(len(captured) == 1, "Pipeline should execute exactly once.")

    options = captured[0]
    config = options.config

    expect(config.pipeline.backfill is True, "Backfill flag should propagate to pipeline config.")
    expect(
        config.pipeline.incremental is True,
        "Incremental flag should propagate to pipeline config.",
    )
    expected_since = datetime.fromisoformat(since_iso)
    expect(
        config.pipeline.since == expected_since,
        "Since value should be parsed into a datetime instance.",
    )
    expect(config.telemetry.enabled is True, "Telemetry enabled flag should propagate.")
    expect(
        config.telemetry.exporters == ("console",),
        "Telemetry exporters should include the console exporter.",
    )
    expect(
        config.telemetry.service_name == "hotpass-prefect",
        "Telemetry service name should propagate to config.",
    )
    expect(
        config.telemetry.environment == "staging",
        "Telemetry environment should propagate to config.",
    )
    expect(
        config.telemetry.resource_attributes["deployment"] == "prefect",
        "Telemetry resource attributes should include deployment marker.",
    )
    expect(
        config.telemetry.otlp_endpoint == "http://localhost:4317",
        "OTLP endpoint should propagate to telemetry settings.",
    )
    expect(
        config.telemetry.otlp_metrics_endpoint == "http://localhost:4318",
        "OTLP metrics endpoint should propagate to telemetry settings.",
    )
    expect(
        config.telemetry.otlp_headers["authorization"] == "token",
        "Telemetry headers should propagate to telemetry settings.",
    )
    expect(
        config.telemetry.otlp_insecure is True,
        "Telemetry insecure flag should propagate to telemetry settings.",
    )
    expect(
        config.telemetry.otlp_timeout == 5.5,
        "Telemetry timeout should propagate to telemetry settings.",
    )
    expect(
        options.telemetry_context["hotpass.flow"] == "hotpass-refinement-pipeline",
        "Telemetry context should include flow identifier.",
    )
    expect(
        options.telemetry_context["hotpass.command"] == "prefect.refinement_flow",
        "Telemetry context should include command identifier.",
    )


def _write_archive(
    archive_root: Path, run_date: date, version: str, payload: str = "sample"
) -> Path:
    archive_root.mkdir(parents=True, exist_ok=True)
    archive_path = archive_root / f"hotpass-inputs-{run_date:%Y%m%d}-v{version}.zip"
    staging_dir = archive_root / f"staging-{run_date:%Y%m%d}-{version}"
    staging_dir.mkdir(exist_ok=True)
    source_file = staging_dir / "input.csv"
    source_file.write_text(payload)
    with zipfile.ZipFile(archive_path, "w") as zip_handle:
        zip_handle.write(source_file, arcname="input.csv")
    return archive_path


def test_backfill_flow_processes_multiple_runs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    archive_root = tmp_path / "archives"
    restore_root = tmp_path / "rehydrated"
    base_config = HotpassConfig().merge(
        {
            "pipeline": {
                "output_path": tmp_path / "outputs" / "refined.xlsx",
                "archive": False,
            }
        }
    )
    runs = [
        {"run_date": "2024-01-01", "version": "v1"},
        {"run_date": "2024-01-02", "version": "v2"},
    ]
    for run in runs:
        _write_archive(
            archive_root,
            date.fromisoformat(run["run_date"]),
            run["version"],
            payload=run["version"],
        )

    captured_configs: list[HotpassConfig] = []

    def fake_run_pipeline_once(
        options: PipelineRunOptionsType,
    ) -> PipelineRunSummaryType:
        captured_configs.append(options.config)
        pipeline_output = options.config.pipeline.output_path
        return PipelineRunSummary(
            success=True,
            total_records=5,
            elapsed_seconds=1.5,
            output_path=pipeline_output,
            quality_report={"rows": 5},
        )

    monkeypatch.setattr(orchestration, "run_pipeline_once", fake_run_pipeline_once)

    result = backfill_pipeline_flow(
        runs=runs,
        archive_root=str(archive_root),
        restore_root=str(restore_root),
        base_config=base_config.model_dump(mode="python"),
    )

    assert len(captured_configs) == 2
    assert result["metrics"]["total_runs"] == 2
    assert result["metrics"]["successful_runs"] == 2
    assert result["metrics"]["total_records"] == 10

    for run, config in zip(runs, captured_configs, strict=True):
        extracted = restore_root / f"{run['run_date']}--{run['version']}"
        assert config.pipeline.input_dir == extracted
        assert (extracted / "input.csv").read_text() == run["version"]
        expected_output = (
            restore_root / "outputs" / f"refined-{run['run_date']}-{run['version']}.xlsx"
        )
        assert config.pipeline.output_path == expected_output

    assert all(run_entry["success"] for run_entry in result["runs"])


def test_backfill_flow_is_idempotent(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    archive_root = tmp_path / "archives"
    restore_root = tmp_path / "rehydrated"
    run_info = {"run_date": "2024-02-01", "version": "baseline"}
    _write_archive(
        archive_root,
        date.fromisoformat(run_info["run_date"]),
        run_info["version"],
        payload="initial",
    )

    call_paths: list[Path] = []

    def fake_run_pipeline_once(
        options: PipelineRunOptionsType,
    ) -> PipelineRunSummaryType:
        call_paths.append(options.config.pipeline.input_dir)
        return PipelineRunSummary(
            success=True,
            total_records=3,
            elapsed_seconds=1.0,
            output_path=options.config.pipeline.output_path,
            quality_report={"rows": 3},
        )

    monkeypatch.setattr(orchestration, "run_pipeline_once", fake_run_pipeline_once)

    backfill_pipeline_flow(
        runs=[run_info],
        archive_root=str(archive_root),
        restore_root=str(restore_root),
        base_config=HotpassConfig().model_dump(mode="python"),
    )

    extracted = call_paths[0]
    marker = extracted / "leftover.txt"
    marker.write_text("stale")

    # Update archive payload to ensure rehydration refreshes content
    _write_archive(
        archive_root,
        date.fromisoformat(run_info["run_date"]),
        run_info["version"],
        payload="fresh",
    )

    backfill_pipeline_flow(
        runs=[run_info],
        archive_root=str(archive_root),
        restore_root=str(restore_root),
        base_config=HotpassConfig().model_dump(mode="python"),
    )

    assert marker.exists() is False
    assert (extracted / "input.csv").read_text() == "fresh"
    assert len(call_paths) == 2


def test_backfill_flow_missing_archive(tmp_path: Path) -> None:
    restore_root = tmp_path / "rehydrated"

    with pytest.raises(PipelineOrchestrationError):
        backfill_pipeline_flow(
            runs=[{"run_date": "2024-03-01", "version": "unknown"}],
            archive_root=str(tmp_path / "archives"),
            restore_root=str(restore_root),
        )


def test_backfill_flow_falls_back_when_concurrency_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive_root = tmp_path / "archives"
    restore_root = tmp_path / "rehydrated"
    run_info = {"run_date": "2024-04-01", "version": "replay"}
    _write_archive(archive_root, date.fromisoformat(run_info["run_date"]), run_info["version"])

    calls: list[Path] = []

    def fake_run_pipeline_once(
        options: PipelineRunOptionsType,
    ) -> PipelineRunSummaryType:
        calls.append(options.config.pipeline.input_dir)
        return PipelineRunSummary(
            success=True,
            total_records=2,
            elapsed_seconds=0.5,
            output_path=options.config.pipeline.output_path,
            quality_report={"rows": 2},
        )

    @asynccontextmanager
    async def _failing_concurrency(*_args, **_kwargs):
        raise RuntimeError("test concurrency failure")
        yield

    monkeypatch.setattr(orchestration, "run_pipeline_once", fake_run_pipeline_once)
    monkeypatch.setattr(orchestration, "prefect_concurrency", _failing_concurrency, raising=False)

    result = backfill_pipeline_flow(
        runs=[run_info],
        archive_root=str(archive_root),
        restore_root=str(restore_root),
        concurrency_limit=1,
    )

    expect(len(calls) == 1, "Backfill flow should invoke the pipeline exactly once")
    expect(
        result["metrics"]["total_runs"] == 1,
        "Metrics should reflect a single run when concurrency fails",
    )


@pytest.mark.asyncio
async def test_run_with_prefect_concurrency_acquires_and_releases(
    tmp_path: Path,
) -> None:
    events: list[tuple[str, ...]] = []

    summary = PipelineRunSummary(
        success=True,
        total_records=5,
        elapsed_seconds=0.25,
        output_path=tmp_path / "refined.xlsx",
        quality_report={"rows": 5},
    )

    @asynccontextmanager
    async def _tracking_concurrency(key: str, occupy: int):
        events.append(("enter", key, str(occupy)))
        try:
            yield
        finally:
            events.append(("exit", key, str(occupy)))

    async def _run_sync(
        func: Callable[[], PipelineRunSummaryType],
        *_args: object,
        **_kwargs: object,
    ) -> PipelineRunSummaryType:
        events.append(("run_sync",))
        return func()

    def _callback() -> PipelineRunSummaryType:
        events.append(("callback",))
        return summary

    result = await _run_with_prefect_concurrency(
        _tracking_concurrency,
        "hotpass/tests",
        2,
        _callback,
        run_sync=_run_sync,
    )

    expect(result is summary, "Expected concurrency helper to return callback result")
    expect(("callback",) in events, "Callback should execute within the concurrency guard")
    expect(("enter", "hotpass/tests", "2") in events, "Concurrency context should be entered")
    expect(("exit", "hotpass/tests", "2") in events, "Concurrency context should be exited")


@pytest.mark.asyncio
async def test_run_with_prefect_concurrency_falls_back_on_error(
    tmp_path: Path,
) -> None:
    events: list[str] = []

    summary = PipelineRunSummary(
        success=True,
        total_records=1,
        elapsed_seconds=0.1,
        output_path=tmp_path / "fallback.xlsx",
        quality_report={"rows": 1},
    )

    @asynccontextmanager
    async def _failing_concurrency(*_args: object, **_kwargs: object):
        raise RuntimeError("boom")
        yield

    async def _run_sync(
        func: Callable[[], PipelineRunSummaryType],
        *_args: object,
        **_kwargs: object,
    ) -> PipelineRunSummaryType:
        events.append("run_sync")
        return func()

    def _callback() -> PipelineRunSummaryType:
        events.append("callback")
        return summary

    result = await _run_with_prefect_concurrency(
        _failing_concurrency,
        "hotpass/tests",
        1,
        _callback,
        run_sync=_run_sync,
    )

    expect(result is summary, "Concurrency fallback should return callback result")
    expect(events.count("run_sync") == 1, "Thread runner should execute once when falling back")
    expect("callback" in events, "Callback must still execute when concurrency acquisition fails")


def test_execute_with_concurrency_uses_async_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    events: list[tuple[str, ...]] = []

    summary = PipelineRunSummary(
        success=True,
        total_records=4,
        elapsed_seconds=0.4,
        output_path=tmp_path / "concurrency.xlsx",
        quality_report={"rows": 4},
    )

    @asynccontextmanager
    async def _tracking_concurrency(key: str, occupy: int):
        events.append(("enter", key, str(occupy)))
        try:
            yield
        finally:
            events.append(("exit", key, str(occupy)))

    async def _run_sync(
        func: Callable[[], PipelineRunSummaryType],
        *_args: object,
        **_kwargs: object,
    ) -> PipelineRunSummaryType:
        events.append(("run_sync",))
        return func()

    def _callback() -> PipelineRunSummaryType:
        events.append(("callback",))
        return summary

    monkeypatch.setattr(orchestration, "prefect_concurrency", _tracking_concurrency, raising=False)
    monkeypatch.setattr(anyio.to_thread, "run_sync", _run_sync)

    result = _execute_with_concurrency("hotpass/tests", 3, _callback)

    expect(result is summary, "Execute with concurrency should return callback result")
    expect(("callback",) in events, "Callback should execute through async runner")
    expect(("enter", "hotpass/tests", "3") in events, "Concurrency context should be entered")
    expect(("exit", "hotpass/tests", "3") in events, "Concurrency context should be exited")
