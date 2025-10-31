"""Overview command - display available Hotpass commands and system status."""

from __future__ import annotations

import argparse
from importlib.metadata import version as get_version

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..builder import CLICommand, SharedParsers
from ..configuration import CLIProfile


def build(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    shared: SharedParsers,
) -> argparse.ArgumentParser:
    """Build the overview command parser."""
    parser = subparsers.add_parser(
        "overview",
        help="Display available Hotpass commands and system status",
        description=(
            "Show an overview of Hotpass capabilities, available commands, and system status."
        ),
        parents=[shared.base],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    return parser


def register() -> CLICommand:
    return CLICommand(
        name="overview",
        help="Display available Hotpass commands and system status",
        builder=build,
        handler=_command_handler,
    )


def _command_handler(namespace: argparse.Namespace, profile: CLIProfile | None) -> int:
    """Handle the overview command execution."""
    console = Console()
    _ = profile  # unused but required by interface

    try:
        hotpass_version = get_version("hotpass")
    except Exception:
        hotpass_version = "unknown"

    # Create commands table
    table = Table(
        title="Available Hotpass Commands",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Command", style="cyan", width=15)
    table.add_column("Description", style="white")

    commands = [
        ("overview", "Display this overview of Hotpass commands and status"),
        ("refine", "Run the Hotpass refinement pipeline on input data"),
        ("enrich", "Enrich refined data with additional information"),
        ("qa", "Run quality assurance checks and validation"),
        ("contracts", "Emit data contracts and schemas for a profile"),
        ("setup", "Run the guided staging wizard (deps, tunnels, contexts, env)"),
        ("net", "Manage SSH/SSM tunnels to staging services"),
        ("aws", "Verify AWS credentials and optional EKS access"),
        ("ctx", "Bootstrap Prefect profiles and kube contexts"),
        ("env", "Generate .env files aligned with active tunnels"),
        ("arc", "Verify GitHub ARC runner scale sets"),
        ("distro", "Bundle documentation assets under dist/docs"),
        ("run", "Run the Hotpass refinement pipeline (alias for refine)"),
        ("backfill", "Replay archived inputs through the pipeline"),
        ("doctor", "Run configuration and environment diagnostics"),
        ("orchestrate", "Run pipeline with Prefect orchestration"),
        ("resolve", "Run entity resolution on existing datasets"),
        ("dashboard", "Launch the Hotpass monitoring dashboard"),
        ("deploy", "Deploy the pipeline to Prefect"),
        ("init", "Bootstrap a project workspace"),
        ("version", "Manage dataset versions with DVC"),
    ]

    for cmd, desc in commands:
        table.add_row(cmd, desc)

    # Display overview
    console.print()
    console.print(
        Panel.fit(
            f"[bold cyan]Hotpass Data Refinement Platform[/bold cyan]\n"
            f"Version: {hotpass_version}\n\n"
            f"Hotpass transforms messy spreadsheets into a governed single source of truth.",
            title="About Hotpass",
            border_style="cyan",
        )
    )
    console.print()
    console.print(table)
    console.print()

    # Usage examples
    refine_cmd = (
        "uv run hotpass refine --input-dir ./data "
        "--output-path ./dist/refined.xlsx --profile aviation"
    )
    enrich_cmd = (
        "uv run hotpass enrich --input ./dist/refined.xlsx "
        "--output ./dist/enriched.xlsx --profile aviation"
    )
    console.print(
        Panel.fit(
            "[bold]Common workflows:[/bold]\n\n"
            "1. Refine a spreadsheet:\n"
            f"   [cyan]{refine_cmd}[/cyan]\n\n"
            "2. Enrich refined data:\n"
            f"   [cyan]{enrich_cmd}[/cyan]\n\n"
            "3. Run quality checks:\n"
            "   [cyan]uv run hotpass qa all[/cyan]\n\n"
            "4. Get help on any command:\n"
            "   [cyan]uv run hotpass <command> --help[/cyan]",
            title="Quick Start",
            border_style="green",
        )
    )
    console.print()

    return 0
