"""Tests for CLI enhanced module."""

import argparse

from hotpass.cli_enhanced import build_enhanced_parser


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
