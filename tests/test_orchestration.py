"""Tests for Prefect orchestration module."""

# ruff: noqa: E402

import importlib
import sys
import types
import zipfile
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pandas as pd
import pytest

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

if not TYPE_CHECKING:
    PipelineRunOptionsType = PipelineRunOptions  # type: ignore[assignment]
    PipelineRunSummaryType = PipelineRunSummary  # type: ignore[assignment]


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

    assert summary.success is True
    assert summary.total_records == 3
    assert summary.archive_path == tmp_path / "dist" / "archive.zip"


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

        assert result["success"] is True
        assert result["total_records"] == 3
        assert "elapsed_seconds" in result
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
        patch("hotpass.orchestration.create_refined_archive", side_effect=ValueError("boom")),
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


def test_deploy_pipeline_without_prefect(monkeypatch):
    """Deploying without Prefect installed should raise a runtime error."""

    monkeypatch.setattr(orchestration, "PREFECT_AVAILABLE", False, raising=False)

    with pytest.raises(RuntimeError, match="Prefect is not installed"):
        orchestration.deploy_pipeline()


def test_deploy_pipeline_invokes_prefect_serve(monkeypatch):
    """Deploy pipeline should call Prefect's serve helper when available."""

    monkeypatch.setattr(orchestration, "PREFECT_AVAILABLE", True, raising=False)

    fake_prefect = types.ModuleType("prefect")
    fake_deployments = types.ModuleType("prefect.deployments")
    serve_calls: list[SimpleNamespace] = []

    def fake_serve(deployment: SimpleNamespace) -> None:
        serve_calls.append(deployment)

    fake_deployments.serve = fake_serve

    monkeypatch.setitem(sys.modules, "prefect", fake_prefect)
    monkeypatch.setitem(sys.modules, "prefect.deployments", fake_deployments)

    class DummyFlow:
        def to_deployment(self, name: str) -> SimpleNamespace:
            return SimpleNamespace(
                name=name,
                work_pool_name=None,
                schedule=None,
            )

    monkeypatch.setattr(orchestration, "refinement_pipeline_flow", DummyFlow(), raising=False)

    schedule_module = types.SimpleNamespace(CronSchedule=SimpleNamespace)
    monkeypatch.setitem(sys.modules, "prefect.server.schemas.schedules", schedule_module)

    orchestration.deploy_pipeline(name="demo", work_pool="inbox", cron_schedule="0 12 * * *")

    assert serve_calls
    deployment = serve_calls[0]
    assert deployment.name == "demo"
    assert deployment.work_pool_name == "inbox"
    assert deployment.schedule.cron == "0 12 * * *"


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
        {"pipeline": {"output_path": tmp_path / "outputs" / "refined.xlsx", "archive": False}}
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
        archive_root, date.fromisoformat(run_info["run_date"]), run_info["version"], payload="fresh"
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

    assert len(calls) == 1
    assert result["metrics"]["total_runs"] == 1
