"""Implementation of the `hotpass run` subcommand."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rich.prompt import Confirm

from hotpass.artifacts import create_refined_archive
from hotpass.config import load_industry_profile
from hotpass.pipeline import PipelineConfig, run_pipeline
from hotpass.pipeline.base import ExcelReadOptions

from ..builder import CLICommand, SharedParsers
from ..configuration import CLIProfile
from ..progress import (
    DEFAULT_SENSITIVE_FIELD_TOKENS,
    PipelineProgress,
    StructuredLogger,
    render_progress,
)
from ..shared import infer_report_format, load_config, normalise_sensitive_fields


@dataclass(slots=True)
class RunOptions:
    """Resolved options driving the core pipeline run."""

    input_dir: Path
    output_path: Path
    expectation_suite_name: str
    country_code: str
    archive: bool
    dist_dir: Path
    log_format: str
    report_path: Path | None
    report_format: str | None
    party_store_path: Path | None
    config_paths: list[Path]
    excel_chunk_size: int | None
    excel_engine: str | None
    excel_stage_dir: Path | None
    sensitive_fields: tuple[str, ...]
    interactive: bool | None
    qa_mode: str
    observability: bool | None
    profile_name: str | None
    features: dict[str, bool]
    industry_profile: str | None


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

    interactive = options.interactive
    if interactive is None:
        interactive = console is not None and sys.stdin.isatty()

    if not options.input_dir.exists():
        logger.log_error(f"Input directory does not exist: {options.input_dir}")
        logger.log_error("Please create the directory or specify a different path with --input-dir")
        return 1
    if not options.input_dir.is_dir():
        logger.log_error(f"Input path is not a directory: {options.input_dir}")
        return 1

    excel_files = list(options.input_dir.glob("*.xlsx")) + list(options.input_dir.glob("*.xls"))
    if not excel_files:
        logger.log_error(f"No Excel files found in: {options.input_dir}")
        logger.log_error("Please add Excel files to the input directory")
        return 1

    if console:
        console.print("[bold cyan]Hotpass Data Refinement Pipeline[/bold cyan]")
        console.print(f"[dim]Profile:[/dim] {options.profile_name or 'default'}")
        console.print(f"[dim]Input directory:[/dim] {options.input_dir}")
        console.print(f"[dim]Output path:[/dim] {options.output_path}")
        console.print(f"[dim]Found {len(excel_files)} Excel file(s)[/dim]")
        console.print()

    excel_options = None
    if any(
        value is not None
        for value in (options.excel_chunk_size, options.excel_engine, options.excel_stage_dir)
    ):
        excel_options = ExcelReadOptions(
            chunk_size=options.excel_chunk_size,
            engine=options.excel_engine,
            stage_to_parquet=options.excel_stage_dir is not None,
            stage_dir=options.excel_stage_dir,
        )

    industry_profile = None
    if options.industry_profile:
        industry_profile = load_industry_profile(options.industry_profile)

    progress_context = render_progress(console)
    with progress_context as progress:
        listener = progress.handle_event if isinstance(progress, PipelineProgress) else None
        config = PipelineConfig(
            input_dir=options.input_dir,
            output_path=options.output_path,
            expectation_suite_name=options.expectation_suite_name,
            country_code=options.country_code,
            excel_options=excel_options,
            progress_listener=listener,
            industry_profile=industry_profile,
        )
        if options.qa_mode == "relaxed":
            config.enable_audit_trail = False
            config.enable_recommendations = False
        elif options.qa_mode == "strict":
            config.enable_audit_trail = True
            config.enable_recommendations = True

        try:
            result = run_pipeline(config)
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
        console.print(f"[dim]Refined data written to:[/dim] {options.output_path}")

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

    if options.archive:
        options.dist_dir.mkdir(parents=True, exist_ok=True)
        archive_path = create_refined_archive(options.output_path, options.dist_dir)
        logger.log_archive(archive_path)

    return 0


def _resolve_options(namespace: argparse.Namespace, profile: CLIProfile | None) -> RunOptions:
    defaults: dict[str, Any] = {
        "input_dir": Path.cwd() / "data",
        "output_path": None,
        "expectation_suite_name": "default",
        "country_code": "ZA",
        "archive": False,
        "dist_dir": Path.cwd() / "dist",
        "log_format": "rich",
        "report_path": None,
        "report_format": None,
        "party_store_path": None,
        "excel_chunk_size": None,
        "excel_engine": None,
        "excel_stage_dir": None,
        "sensitive_fields": None,
        "interactive": None,
        "qa_mode": "default",
        "observability": None,
    }

    profile_name = profile.name if profile else None
    features: dict[str, bool] = profile.feature_payload() if profile else {}
    industry_profile = profile.industry_profile if profile else None

    if profile is not None:
        defaults = profile.apply(defaults)

    config_paths: list[Path] = []
    if profile is not None:
        config_paths.extend(profile.resolved_config_files())
    cli_config_paths = getattr(namespace, "config_paths", None)
    if cli_config_paths:
        config_paths.extend(Path(path) for path in cli_config_paths)

    config_values: dict[str, Any] = {}
    for config_path in config_paths:
        if not config_path.exists():
            msg = f"Configuration file not found: {config_path}"
            raise FileNotFoundError(msg)
        config_values.update(load_config(config_path))

    options = {**defaults, **config_values}

    _apply_cli_override(options, namespace, "input_dir", converter=Path)
    _apply_cli_override(options, namespace, "output_path", converter=Path)
    _apply_cli_override(options, namespace, "expectation_suite_name")
    _apply_cli_override(options, namespace, "country_code")
    _apply_cli_override(options, namespace, "dist_dir", converter=Path)
    _apply_cli_override(options, namespace, "party_store_path", converter=Path)
    _apply_cli_override(options, namespace, "log_format")
    _apply_cli_override(options, namespace, "report_path", converter=Path)
    _apply_cli_override(options, namespace, "report_format")
    _apply_cli_override(options, namespace, "excel_chunk_size", converter=int)
    _apply_cli_override(options, namespace, "excel_engine")
    _apply_cli_override(options, namespace, "excel_stage_dir", converter=Path)
    _apply_cli_override(options, namespace, "interactive")
    _apply_cli_override(options, namespace, "qa_mode")
    _apply_cli_override(options, namespace, "observability")

    archive_flag = getattr(namespace, "archive", None)
    if archive_flag is not None:
        options["archive"] = bool(archive_flag)
    sensitive_cli = getattr(namespace, "sensitive_fields", None)
    if sensitive_cli is not None:
        options["sensitive_fields"] = list(sensitive_cli)

    input_dir = Path(options["input_dir"])
    output_path = (
        Path(options["output_path"])
        if options.get("output_path")
        else input_dir / "refined_data.xlsx"
    )
    dist_dir = Path(options.get("dist_dir", Path.cwd() / "dist"))
    report_path = Path(options["report_path"]) if options.get("report_path") else None
    party_store_path = (
        Path(options["party_store_path"]) if options.get("party_store_path") else None
    )
    stage_dir = Path(options["excel_stage_dir"]) if options.get("excel_stage_dir") else None

    chunk_size_value = options.get("excel_chunk_size")
    chunk_size = None
    if chunk_size_value is not None:
        chunk_size = int(chunk_size_value)
        if chunk_size <= 0:
            msg = "--excel-chunk-size must be greater than zero"
            raise ValueError(msg)

    report_format = options.get("report_format")
    if isinstance(report_format, str):
        report_format = report_format.lower()
    if report_format is None and report_path is not None:
        report_format = infer_report_format(report_path)
    elif report_format is not None and report_format not in {"markdown", "html"}:
        msg = f"Unsupported report format: {report_format}"
        raise ValueError(msg)

    log_format = str(options.get("log_format", "rich")).lower()
    if log_format not in {"json", "rich"}:
        msg = f"Unsupported log format: {log_format}"
        raise ValueError(msg)

    qa_mode = options.get("qa_mode", "default")
    if qa_mode not in {"default", "strict", "relaxed"}:
        msg = f"Unsupported QA mode: {qa_mode}"
        raise ValueError(msg)

    archive = bool(options.get("archive", False))
    interactive = options.get("interactive")
    if not isinstance(interactive, (bool, type(None))):
        interactive = bool(interactive)

    observability = options.get("observability")
    if isinstance(observability, str):
        observability = observability.lower() in {"1", "true", "yes", "on"}

    sensitive_field_values = options.get("sensitive_fields")
    sensitive_values_iter: Iterable[str] | None = None
    if isinstance(sensitive_field_values, str):
        sensitive_values_iter = [sensitive_field_values]
    elif isinstance(sensitive_field_values, Iterable):
        sensitive_values_iter = [
            str(value) for value in sensitive_field_values if value is not None
        ]
    elif sensitive_field_values is not None:
        sensitive_values_iter = [str(sensitive_field_values)]
    sensitive_fields = normalise_sensitive_fields(
        sensitive_values_iter, DEFAULT_SENSITIVE_FIELD_TOKENS
    )

    excel_engine = options.get("excel_engine")
    if isinstance(excel_engine, str) and not excel_engine:
        excel_engine = None

    return RunOptions(
        input_dir=input_dir,
        output_path=output_path,
        expectation_suite_name=str(options["expectation_suite_name"]),
        country_code=str(options["country_code"]),
        archive=archive,
        dist_dir=dist_dir,
        log_format=log_format,
        report_path=report_path,
        report_format=report_format,
        party_store_path=party_store_path,
        config_paths=[path for path in config_paths if path.exists()],
        excel_chunk_size=chunk_size,
        excel_engine=excel_engine,
        excel_stage_dir=stage_dir,
        sensitive_fields=sensitive_fields,
        interactive=interactive if isinstance(interactive, (bool, type(None))) else None,
        qa_mode=qa_mode,
        observability=observability if isinstance(observability, (bool, type(None))) else None,
        profile_name=profile_name,
        features=features,
        industry_profile=industry_profile,
    )


def _apply_cli_override(
    options: dict[str, Any],
    namespace: argparse.Namespace,
    field_name: str,
    *,
    converter: Callable[[Any], Any] | None = None,
) -> None:
    value = getattr(namespace, field_name, None)
    if value is None:
        return
    options[field_name] = converter(value) if converter is not None else value


__all__ = ["register", "build", "RunOptions"]
