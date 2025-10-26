"""Tests for Prefect orchestration module."""

import sys
import types
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pandas as pd
import pytest

import hotpass.orchestration as orchestration
from hotpass.orchestration import (
    PipelineOrchestrationError,
    PipelineRunOptions,
    refinement_pipeline_flow,
    run_pipeline_once,
    run_pipeline_task,
)


@pytest.fixture(autouse=True)
def reset_orchestration(monkeypatch):
    """Ensure Prefect decorators do not retain state between tests."""

    monkeypatch.setattr(orchestration, "flow", orchestration.flow, raising=False)
    monkeypatch.setattr(orchestration, "task", orchestration.task, raising=False)


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
    config = PipelineRunOptions(
        input_dir=tmp_path,
        output_path=tmp_path / "out.xlsx",
        profile_name="aviation",
        excel_chunk_size=None,
        archive=True,
        archive_dir=tmp_path / "dist",
    )

    with (
        patch("hotpass.orchestration.get_default_profile") as mock_profile,
        patch("hotpass.orchestration.run_pipeline") as mock_run,
        patch("hotpass.orchestration.create_refined_archive") as mock_archive,
    ):
        mock_profile.return_value = Mock()
        mock_run.return_value = mock_pipeline_result
        mock_archive.return_value = tmp_path / "dist" / "archive.zip"

        summary = run_pipeline_once(config)

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
    config = PipelineRunOptions(
        input_dir=tmp_path,
        output_path=tmp_path / "out.xlsx",
        profile_name="aviation",
        excel_chunk_size=None,
        archive=True,
        archive_dir=tmp_path / "dist",
    )

    with (
        patch("hotpass.orchestration.get_default_profile") as mock_profile,
        patch("hotpass.orchestration.run_pipeline") as mock_run,
        patch("hotpass.orchestration.create_refined_archive", side_effect=ValueError("boom")),
    ):
        mock_profile.return_value = Mock()
        mock_run.return_value = mock_pipeline_result

        with pytest.raises(PipelineOrchestrationError) as exc:
            run_pipeline_once(config)

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
