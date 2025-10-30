"""Refine command - alias for run command with refined semantics."""

from __future__ import annotations

import argparse

from ..builder import CLICommand, SharedParsers
from ..configuration import CLIProfile
from .run import _command_handler as run_handler


def build(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    shared: SharedParsers,
) -> argparse.ArgumentParser:
    """Build the refine command parser - reuses run command structure."""
    parser = subparsers.add_parser(
        "refine",
        help="Run the Hotpass refinement pipeline",
        description=(
            "Refine input spreadsheets into a governed single source of truth. "
            "This command processes data through normalization, deduplication, "
            "validation, and quality scoring. This is an alias for the 'run' command."
        ),
        parents=[shared.base, shared.pipeline, shared.reporting, shared.excel],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    return parser


def register() -> CLICommand:
    return CLICommand(
        name="refine",
        help="Run the Hotpass refinement pipeline",
        builder=build,
        handler=_command_handler,
    )


def _command_handler(namespace: argparse.Namespace, profile: CLIProfile | None) -> int:
    """Handle the refine command - delegates to run command handler."""
    return run_handler(namespace, profile)
