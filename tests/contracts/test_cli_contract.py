"""Contract tests ensuring CLI matches declared interface."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from hotpass import cli


def _contract_path() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / "contracts" / "hotpass-cli-contract.yaml"
        if candidate.exists():
            return candidate
    msg = "Unable to locate CLI contract specification"
    raise FileNotFoundError(msg)


def load_contract() -> dict[str, Any]:
    with open(_contract_path(), encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def extract_options(parser: argparse.ArgumentParser) -> dict[str, argparse.Action]:
    return {action.option_strings[0]: action for action in parser._actions if action.option_strings}


def test_cli_contract_matches_spec() -> None:
    contract = load_contract()
    parser = cli.build_parser()
    options = extract_options(parser)

    option_specs: list[dict[str, Any]] = contract["options"]

    for option in option_specs:
        opt_name = option["name"]
        assert opt_name in options, f"Option {opt_name} missing from parser"
        action = options[opt_name]
        required = option.get("required", False)
        assert action.required == required
