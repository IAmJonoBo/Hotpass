"""Implementation of the `hotpass deploy` subcommand."""

from __future__ import annotations

import argparse
from collections.abc import Iterable
from dataclasses import dataclass

from hotpass.orchestration import deploy_pipeline

from ..builder import CLICommand, SharedParsers
from ..configuration import CLIProfile
from ..progress import DEFAULT_SENSITIVE_FIELD_TOKENS, StructuredLogger
from ..shared import normalise_sensitive_fields


@dataclass(slots=True)
class DeployOptions:
    name: str
    schedule: str | None
    work_pool: str | None
    log_format: str
    sensitive_fields: tuple[str, ...]


def build(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser], shared: SharedParsers
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "deploy",
        help="Deploy the Hotpass pipeline to Prefect",
        description="Create or update a Prefect deployment for the refinement pipeline.",
        parents=[shared.base],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--name", default="hotpass-refinement", help="Prefect deployment name")
    parser.add_argument("--schedule", help="Cron schedule (e.g., '0 2 * * *' for daily at 2am)")
    parser.add_argument("--work-pool", help="Prefect work pool name")
    return parser


def register() -> CLICommand:
    return CLICommand(
        name="deploy",
        help="Deploy the Hotpass pipeline",
        builder=build,
        handler=_command_handler,
    )


def _command_handler(namespace: argparse.Namespace, profile: CLIProfile | None) -> int:
    options = _resolve_options(namespace, profile)
    logger = StructuredLogger(options.log_format, options.sensitive_fields)
    console = logger.console if options.log_format == "rich" else None

    if console:
        console.print("[bold cyan]Deploying pipeline to Prefect...[/bold cyan]")
        console.print(f"[dim]Deployment name:[/dim] {options.name}")
        if options.schedule:
            console.print(f"[dim]Schedule:[/dim] {options.schedule}")
        if options.work_pool:
            console.print(f"[dim]Work pool:[/dim] {options.work_pool}")

    try:
        deploy_pipeline(
            name=options.name, cron_schedule=options.schedule, work_pool=options.work_pool
        )
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.log_error(f"Deployment failed: {exc}")
        return 1

    logger.log_event(
        "deploy.completed",
        {
            "name": options.name,
            "schedule": options.schedule,
            "work_pool": options.work_pool,
        },
    )
    if console:
        console.print("[bold green]✓[/bold green] Pipeline deployed successfully!")
    return 0


def _resolve_options(namespace: argparse.Namespace, profile: CLIProfile | None) -> DeployOptions:
    log_format_value: str | None = getattr(namespace, "log_format", None)
    if log_format_value is None and profile is not None:
        log_format_value = profile.log_format
    log_format = (log_format_value or "rich").lower()
    if log_format not in {"json", "rich"}:
        msg = f"Unsupported log format: {log_format}"
        raise ValueError(msg)

    raw_sensitive = getattr(namespace, "sensitive_fields", None)
    if raw_sensitive is None and profile is not None:
        raw_sensitive = profile.options.get("sensitive_fields")
    sensitive_iter: Iterable[str] | None = None
    if isinstance(raw_sensitive, str):
        sensitive_iter = [raw_sensitive]
    elif isinstance(raw_sensitive, Iterable):
        sensitive_iter = [str(value) for value in raw_sensitive if value is not None]
    elif raw_sensitive is not None:
        sensitive_iter = [str(raw_sensitive)]
    sensitive_fields = normalise_sensitive_fields(sensitive_iter, DEFAULT_SENSITIVE_FIELD_TOKENS)

    return DeployOptions(
        name=str(namespace.name),
        schedule=namespace.schedule,
        work_pool=namespace.work_pool,
        log_format=log_format,
        sensitive_fields=sensitive_fields,
    )


__all__ = ["register", "build"]
