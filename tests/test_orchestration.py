"""Tests for Prefect orchestration module."""

from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest

import hotpass.orchestration as orchestration
from hotpass.orchestration import refinement_pipeline_flow, run_pipeline_task


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


def test_run_pipeline_task_success(mock_pipeline_result):
    """Test successful pipeline task execution."""
    mock_config = Mock()
    mock_config.input_dir = Path("/tmp")
    mock_config.output_path = Path("/tmp/output.xlsx")

    with patch("hotpass.orchestration.run_pipeline") as mock_run:
        mock_run.return_value = mock_pipeline_result

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
    ):
        mock_run.return_value = mock_pipeline_result
        mock_profile.return_value = Mock()

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
