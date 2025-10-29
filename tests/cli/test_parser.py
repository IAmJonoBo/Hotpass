"""Tests covering the top-level Hotpass CLI parser construction."""

from __future__ import annotations

import argparse

from hotpass import cli


def _get_subcommands(
    parser: argparse.ArgumentParser,
) -> dict[str, argparse.ArgumentParser]:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return action.choices  # type: ignore[return-value]
    raise AssertionError("Parser is missing subcommands")


def _extract_options(parser: argparse.ArgumentParser) -> set[str]:
    option_names: set[str] = set()
    for action_group in parser._action_groups:
        for action in action_group._group_actions:
            option_names.update(action.option_strings)
    return option_names


def test_build_parser_registers_expected_commands() -> None:
    parser = cli.build_parser()
    subcommands = _get_subcommands(parser)

    assert {
        "run",
        "orchestrate",
        "resolve",
        "dashboard",
        "deploy",
        "doctor",
        "init",
    }.issubset(set(subcommands))


def test_build_parser_sets_run_as_default_command() -> None:
    parser = cli.build_parser()
    args = parser.parse_args([])

    assert args.command == "run"
    assert callable(getattr(args, "handler", None))


def test_run_command_exposes_core_pipeline_options() -> None:
    parser = cli.build_parser()
    run_parser = _get_subcommands(parser)["run"]

    option_names = _extract_options(run_parser)
    expected = {
        "--input-dir",
        "--output-path",
        "--archive",
        "--log-format",
        "--excel-chunk-size",
        "--excel-stage-dir",
        "--report-path",
    }

    assert expected.issubset(option_names)
