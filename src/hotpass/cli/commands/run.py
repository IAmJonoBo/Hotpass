"""Implementation of the `hotpass run` subcommand."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from rich.prompt import Confirm

from hotpass.artifacts import create_refined_archive
from hotpass.automation.hooks import dispatch_webhooks, push_crm_updates
from hotpass.config import load_industry_profile
from hotpass.config_schema import HotpassConfig
from hotpass.pipeline import default_feature_bundle
from hotpass.pipeline.orchestrator import PipelineExecutionConfig, PipelineOrchestrator

from ..builder import CLICommand, SharedParsers
from ..configuration import CLIProfile
from ..progress import (
    DEFAULT_SENSITIVE_FIELD_TOKENS,
    PipelineProgress,
    StructuredLogger,
    render_progress,
)
from ..shared import infer_report_format, load_config, normalise_sensitive_fields

LEGACY_PIPELINE_KEYS: frozenset[str] = frozenset(
    {
        "input_dir",
        "output_path",
        "dist_dir",
        "archive",
        "expectation_suite",
        "country_code",
        "party_store_path",
        "log_format",
        "report_path",
        "report_format",
        "excel_chunk_size",
        "excel_engine",
        "excel_stage_dir",
        "qa_mode",
        "observability",
        "sensitive_fields",
    }
)


@dataclass(slots=True)
class RunOptions:
    """Resolved options driving the core pipeline run."""

    canonical_config: HotpassConfig
    log_format: str
    report_path: Path | None
    report_format: str | None
    party_store_path: Path | None
    sensitive_fields: tuple[str, ...]
    interactive: bool | None
    profile_name: str | None


def build(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser], shared: SharedParsers
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "run",
        help="Run the Hotpass refinement pipeline",
        description=(
            "Validate, normalise, and publish refined workbooks with optional archiving "
            "and reporting."
        ),
        parents=[shared.base, shared.pipeline, shared.reporting, shared.excel],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    return parser


def register() -> CLICommand:
    return CLICommand(
        name="run",
        help="Run the Hotpass refinement pipeline",
        builder=build,
        handler=_command_handler,
        is_default=True,
    )


def _command_handler(namespace: argparse.Namespace, profile: CLIProfile | None) -> int:
    options = _resolve_options(namespace, profile)
    logger = StructuredLogger(options.log_format, options.sensitive_fields)
    console = logger.console if options.log_format == "rich" else None

    config = options.canonical_config

    interactive = options.interactive
    if interactive is None:
        interactive = console is not None and sys.stdin.isatty()

    input_dir = config.pipeline.input_dir
    output_path = config.pipeline.output_path

    if not input_dir.exists():
        logger.log_error(f"Input directory does not exist: {input_dir}")
        logger.log_error("Please create the directory or specify a different path with --input-dir")
        return 1
    if not input_dir.is_dir():
        logger.log_error(f"Input path is not a directory: {input_dir}")
        return 1

    excel_files = list(input_dir.glob("*.xlsx")) + list(input_dir.glob("*.xls"))
    if not excel_files:
        logger.log_error(f"No Excel files found in: {input_dir}")
        logger.log_error("Please add Excel files to the input directory")
        return 1

    if console:
        console.print("[bold cyan]Hotpass Data Refinement Pipeline[/bold cyan]")
        console.print(f"[dim]Profile:[/dim] {options.profile_name or 'default'}")
        console.print(f"[dim]Input directory:[/dim] {input_dir}")
        console.print(f"[dim]Output path:[/dim] {output_path}")
        console.print(f"[dim]Found {len(excel_files)} Excel file(s)[/dim]")
        console.print()

    progress_context = render_progress(console)
    with progress_context as progress:
        listener = progress.handle_event if isinstance(progress, PipelineProgress) else None

        base_config = config.to_pipeline_config(progress_listener=listener)
        enhanced_config = config.to_enhanced_config()
        orchestrator = PipelineOrchestrator()
        execution = PipelineExecutionConfig(
            base_config=base_config,
            enhanced_config=enhanced_config,
            features=default_feature_bundle(),
        )

        try:
            result = orchestrator.run(execution)
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.log_error(str(exc))
            if console:
                console.print("[bold red]Pipeline failed with error:[/bold red]")
                console.print_exception()
            return 1

    report = result.quality_report
    logger.log_summary(report)

    if console:
        console.print()
        console.print("[bold green]✓[/bold green] Pipeline completed successfully!")
        console.print(f"[dim]Refined data written to:[/dim] {output_path}")

    if interactive and console and report.recommendations:
        console.print()
        if Confirm.ask("View top recommendations now?", default=True):
            console.print("[bold]Top recommendations:[/bold]")
            for recommendation in report.recommendations[:3]:
                console.print(f"  • {recommendation}")

    if options.report_path is not None:
        options.report_path.parent.mkdir(parents=True, exist_ok=True)
        if options.report_format == "html":
            options.report_path.write_text(report.to_html(), encoding="utf-8")
        else:
            options.report_path.write_text(report.to_markdown(), encoding="utf-8")
        logger.log_report_write(options.report_path, options.report_format)

    if options.party_store_path is not None and result.party_store is not None:
        options.party_store_path.parent.mkdir(parents=True, exist_ok=True)
        payload = result.party_store.as_dict()
        options.party_store_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        logger.log_party_store(options.party_store_path)

    if config.pipeline.intent_digest_path is not None and result.intent_digest is not None:
        logger.log_intent_digest(
            config.pipeline.intent_digest_path,
            int(result.intent_digest.shape[0]),
        )

    digest_df = result.intent_digest
    daily_list_df = result.daily_list

    effective_digest = digest_df
    if effective_digest is None:
        if daily_list_df is not None:
            effective_digest = daily_list_df
        else:
            effective_digest = pd.DataFrame()

    if config.pipeline.intent_webhooks:
        dispatch_webhooks(
            effective_digest,
            webhooks=config.pipeline.intent_webhooks,
            daily_list=daily_list_df,
            logger=logger,
        )

    if daily_list_df is not None and config.pipeline.crm_endpoint:
        push_crm_updates(
            daily_list_df,
            config.pipeline.crm_endpoint,
            token=config.pipeline.crm_token,
            logger=logger,
        )

    store_path = config.pipeline.intent_signal_store_path
    if store_path is not None and not store_path.exists():
        store_path.parent.mkdir(parents=True, exist_ok=True)
        store_path.write_text("[]\n", encoding="utf-8")

    if config.pipeline.archive:
        config.pipeline.dist_dir.mkdir(parents=True, exist_ok=True)
        archive_path = create_refined_archive(output_path, config.pipeline.dist_dir)
        logger.log_archive(archive_path)

    return 0


def _resolve_options(namespace: argparse.Namespace, profile: CLIProfile | None) -> RunOptions:
    canonical = HotpassConfig()
    profile_name = profile.name if profile else None

    if profile is not None:
        canonical = profile.apply_to_config(canonical)

    config_paths: list[Path] = []
    if profile is not None:
        config_paths.extend(profile.resolved_config_files())
        if profile.industry_profile:
            industry = load_industry_profile(profile.industry_profile)
            canonical = canonical.merge({"profile": industry.to_dict()})

    cli_config_paths = getattr(namespace, "config_paths", None)
    if cli_config_paths:
        config_paths.extend(Path(path) for path in cli_config_paths)

    for config_path in config_paths:
        if not config_path.exists():
            msg = f"Configuration file not found: {config_path}"
            raise FileNotFoundError(msg)
        payload = _normalise_config_payload(load_config(config_path))
        canonical = canonical.merge(payload)

    pipeline_updates: dict[str, Any] = {}

    if namespace.input_dir is not None:
        pipeline_updates["input_dir"] = Path(namespace.input_dir)
    if namespace.output_path is not None:
        pipeline_updates["output_path"] = Path(namespace.output_path)
    if namespace.expectation_suite_name is not None:
        pipeline_updates["expectation_suite"] = namespace.expectation_suite_name
    if namespace.country_code is not None:
        pipeline_updates["country_code"] = namespace.country_code
    if namespace.dist_dir is not None:
        pipeline_updates["dist_dir"] = Path(namespace.dist_dir)
    if namespace.party_store_path is not None:
        pipeline_updates["party_store_path"] = Path(namespace.party_store_path)
    if getattr(namespace, "intent_digest_path", None) is not None:
        pipeline_updates["intent_digest_path"] = Path(namespace.intent_digest_path)
    if getattr(namespace, "intent_signal_store", None) is not None:
        pipeline_updates["intent_signal_store_path"] = Path(namespace.intent_signal_store)
    if getattr(namespace, "daily_list_path", None) is not None:
        pipeline_updates["daily_list_path"] = Path(namespace.daily_list_path)
    if getattr(namespace, "daily_list_size", None) is not None:
        pipeline_updates["daily_list_size"] = int(namespace.daily_list_size)
    if getattr(namespace, "intent_webhooks", None):
        pipeline_updates["intent_webhooks"] = [
            str(value) for value in namespace.intent_webhooks if value is not None
        ]
    if getattr(namespace, "crm_endpoint", None) is not None:
        pipeline_updates["crm_endpoint"] = namespace.crm_endpoint
    if getattr(namespace, "crm_token", None) is not None:
        pipeline_updates["crm_token"] = namespace.crm_token
    if namespace.log_format is not None:
        pipeline_updates["log_format"] = namespace.log_format
    if namespace.report_path is not None:
        pipeline_updates["report_path"] = Path(namespace.report_path)
    if namespace.report_format is not None:
        pipeline_updates["report_format"] = namespace.report_format
    if getattr(namespace, "excel_chunk_size", None) is not None:
        pipeline_updates["excel_chunk_size"] = int(namespace.excel_chunk_size)
    if getattr(namespace, "excel_engine", None):
        pipeline_updates["excel_engine"] = namespace.excel_engine
    if getattr(namespace, "excel_stage_dir", None) is not None:
        pipeline_updates["excel_stage_dir"] = Path(namespace.excel_stage_dir)
    if getattr(namespace, "qa_mode", None) is not None:
        pipeline_updates["qa_mode"] = namespace.qa_mode
    if getattr(namespace, "observability", None) is not None:
        pipeline_updates["observability"] = bool(namespace.observability)
    if getattr(namespace, "archive", None) is not None:
        pipeline_updates["archive"] = bool(namespace.archive)

    updates: dict[str, Any] = {}
    if pipeline_updates:
        updates["pipeline"] = pipeline_updates

    if updates:
        canonical = canonical.merge(updates)

    sensitive_cli = getattr(namespace, "sensitive_fields", None)
    if sensitive_cli is not None:
        canonical = canonical.merge(
            {
                "pipeline": {
                    "sensitive_fields": [str(value) for value in sensitive_cli],
                }
            }
        )

    log_format = canonical.pipeline.log_format
    sensitive_fields = normalise_sensitive_fields(
        canonical.pipeline.sensitive_fields,
        DEFAULT_SENSITIVE_FIELD_TOKENS,
    )

    interactive = getattr(namespace, "interactive", None)
    if not isinstance(interactive, (bool, type(None))):
        interactive = bool(interactive)

    report_path = canonical.pipeline.report_path
    report_format = canonical.pipeline.report_format or (
        infer_report_format(report_path) if report_path else None
    )
    party_store_path = canonical.pipeline.party_store_path

    return RunOptions(
        canonical_config=canonical,
        log_format=log_format,
        report_path=report_path,
        report_format=report_format,
        party_store_path=party_store_path,
        sensitive_fields=sensitive_fields,
        interactive=interactive,
        profile_name=profile_name,
    )


def _normalise_config_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Upgrade legacy flat payloads to canonical structure for merging."""

    upgraded: dict[str, Any] = dict(payload)
    pipeline_payload: dict[str, Any] = dict(upgraded.get("pipeline", {}))

    changed = False
    for key in list(upgraded.keys()):
        if key in LEGACY_PIPELINE_KEYS:
            pipeline_payload.setdefault(key, upgraded.pop(key))
            changed = True

    if changed:
        upgraded["pipeline"] = pipeline_payload

    return upgraded


__all__ = ["register", "build", "RunOptions"]
