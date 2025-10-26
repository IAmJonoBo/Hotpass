"""Tests for CLI enhanced module."""

import argparse
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

pytest.importorskip("frictionless")

from hotpass import cli_enhanced as cli_enhanced_module  # noqa: E402
from hotpass.cli_enhanced import (  # noqa: E402
    PipelineOrchestrationError,
    build_enhanced_parser,
    cmd_dashboard,
    cmd_orchestrate,
)


def test_build_enhanced_parser():
    """Test building the enhanced parser."""
    parser = build_enhanced_parser()

    assert isinstance(parser, argparse.ArgumentParser)
    assert parser.prog == "hotpass-enhanced"


def test_orchestrate_command_defaults():
    """Test orchestrate command with default arguments."""
    parser = build_enhanced_parser()

    # Parse with defaults
    args = parser.parse_args(["orchestrate"])

    assert args.command == "orchestrate"
    assert str(args.input_dir) == "data"
    assert str(args.output_path) == "data/refined_data.xlsx"
    assert args.profile == "aviation"
    assert args.archive is False


def test_orchestrate_command_custom_args():
    """Test orchestrate command with custom arguments."""
    parser = build_enhanced_parser()

    args = parser.parse_args(
        [
            "orchestrate",
            "--input-dir",
            "/custom/path",
            "--output-path",
            "/output/data.xlsx",
            "--profile",
            "healthcare",
            "--chunk-size",
            "5000",
            "--archive",
        ]
    )

    assert args.command == "orchestrate"
    assert str(args.input_dir) == "/custom/path"
    assert str(args.output_path) == "/output/data.xlsx"
    assert args.profile == "healthcare"
    assert args.chunk_size == 5000
    assert args.archive is True


def test_resolve_command_required_args():
    """Test resolve command with required arguments."""
    parser = build_enhanced_parser()

    args = parser.parse_args(
        [
            "resolve",
            "--input-file",
            "input.xlsx",
            "--output-file",
            "output.xlsx",
        ]
    )

    assert args.command == "resolve"
    assert str(args.input_file) == "input.xlsx"
    assert str(args.output_file) == "output.xlsx"
    assert args.threshold == 0.75
    assert args.use_splink is False


def test_resolve_command_custom_threshold():
    """Test resolve command with custom threshold."""
    parser = build_enhanced_parser()

    args = parser.parse_args(
        [
            "resolve",
            "--input-file",
            "input.xlsx",
            "--output-file",
            "output.xlsx",
            "--threshold",
            "0.9",
            "--use-splink",
        ]
    )

    assert args.threshold == 0.9
    assert args.use_splink is True


def test_dashboard_command_defaults():
    """Test dashboard command with defaults."""
    parser = build_enhanced_parser()

    args = parser.parse_args(["dashboard"])

    assert args.command == "dashboard"
    assert args.port == 8501


def test_dashboard_command_custom_port():
    """Test dashboard command with custom port."""
    parser = build_enhanced_parser()

    args = parser.parse_args(["dashboard", "--port", "9000"])

    assert args.port == 9000


def test_deploy_command_defaults():
    """Test deploy command with defaults."""
    parser = build_enhanced_parser()

    args = parser.parse_args(
        [
            "deploy",
            "--name",
            "test-deployment",
        ]
    )

    assert args.command == "deploy"
    assert args.name == "test-deployment"
    assert args.schedule is None


def test_deploy_command_with_schedule():
    """Test deploy command with cron schedule."""
    parser = build_enhanced_parser()

    args = parser.parse_args(
        [
            "deploy",
            "--name",
            "test-deployment",
            "--schedule",
            "0 2 * * *",
        ]
    )

    assert args.schedule == "0 2 * * *"


def test_parser_no_command():
    """Test parser with no command."""
    parser = build_enhanced_parser()

    # Should parse successfully but have no command
    args = parser.parse_args([])

    assert args.command is None


def test_cmd_dashboard_missing_streamlit(monkeypatch):
    """Dashboard command fails gracefully when Streamlit is absent."""

    parser = build_enhanced_parser()
    args = parser.parse_args(["dashboard"])

    def _missing_import(_module: str):
        raise ModuleNotFoundError

    monkeypatch.setattr("hotpass.cli_enhanced.importlib.import_module", _missing_import)

    exit_code = cmd_dashboard(args)

    assert exit_code == 1


def test_cmd_orchestrate_success(monkeypatch, tmp_path):
    """Successful orchestrations delegate to the shared pipeline helper."""

    parser = build_enhanced_parser()
    args = parser.parse_args(
        [
            "orchestrate",
            "--input-dir",
            str(tmp_path),
            "--output-path",
            str(tmp_path / "out.xlsx"),
        ]
    )

    summary = Mock()
    summary.success = True
    summary.total_records = 5
    summary.elapsed_seconds = 1.2
    summary.archive_path = None
    summary.quality_report = {"expectations_passed": True}

    monkeypatch.setattr("hotpass.cli_enhanced.run_pipeline_once", lambda _opts: summary)

    exit_code = cmd_orchestrate(args)

    assert exit_code == 0


def test_cmd_orchestrate_handles_structured_errors(monkeypatch, tmp_path):
    """Structured orchestration errors surface as non-zero exit codes."""

    parser = build_enhanced_parser()
    args = parser.parse_args(
        [
            "orchestrate",
            "--input-dir",
            str(tmp_path),
            "--output-path",
            str(tmp_path / "out.xlsx"),
        ]
    )

    def _raise(_opts):
        raise PipelineOrchestrationError("failed to archive")

    monkeypatch.setattr("hotpass.cli_enhanced.run_pipeline_once", _raise)

    exit_code = cmd_orchestrate(args)

    assert exit_code == 1


def test_cmd_dashboard_invalid_host(monkeypatch):
    """Invalid host values are rejected before attempting to run Streamlit."""

    parser = build_enhanced_parser()
    args = parser.parse_args(["dashboard", "--host", "bad host"])

    runner_called = False

    def _runner(_command: list[str]) -> None:
        nonlocal runner_called
        runner_called = True

    monkeypatch.setattr(
        "hotpass.cli_enhanced.importlib.import_module",
        lambda _module: SimpleNamespace(main_run=_runner),
    )

    exit_code = cmd_dashboard(args)

    assert exit_code == 1
    assert runner_called is False


def test_cmd_dashboard_valid_invocation(monkeypatch):
    """Valid parameters invoke the Streamlit runner with expected arguments."""

    parser = build_enhanced_parser()
    args = parser.parse_args(["dashboard", "--port", "9000", "--host", "127.0.0.1"])

    captured: list[list[str]] = []

    def _runner(command: list[str]) -> None:
        captured.append(command)

    monkeypatch.setattr(
        "hotpass.cli_enhanced.importlib.import_module",
        lambda _module: SimpleNamespace(main_run=_runner),
    )

    exit_code = cmd_dashboard(args)

    assert exit_code == 0
    expected_path = str(Path(cli_enhanced_module.__file__).resolve().parent / "dashboard.py")

    assert captured == [
        [
            expected_path,
            "--server.port",
            "9000",
            "--server.address",
            "127.0.0.1",
        ]
    ]


def test_cmd_dashboard_non_zero_exit(monkeypatch):
    """Non-zero exits from the Streamlit runner propagate as return codes."""

    parser = build_enhanced_parser()
    args = parser.parse_args(["dashboard"])

    def _runner(_command: list[str]) -> None:
        raise SystemExit(2)

    monkeypatch.setattr(
        "hotpass.cli_enhanced.importlib.import_module",
        lambda _module: SimpleNamespace(main_run=_runner),
    )

    exit_code = cmd_dashboard(args)

    assert exit_code == 2
