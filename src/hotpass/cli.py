"""Command line interface for running the Hotpass refinement pipeline."""

from __future__ import annotations

import argparse
import json
import sys
import time
import tomllib
from collections.abc import Callable, Iterable, Sequence
from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.prompt import Confirm
from rich.table import Table

from hotpass.artifacts import create_refined_archive
from hotpass.data_sources import ExcelReadOptions
from hotpass.pipeline import (
    PIPELINE_EVENT_AGGREGATE_COMPLETED,
    PIPELINE_EVENT_AGGREGATE_PROGRESS,
    PIPELINE_EVENT_AGGREGATE_STARTED,
    PIPELINE_EVENT_COMPLETED,
    PIPELINE_EVENT_EXPECTATIONS_COMPLETED,
    PIPELINE_EVENT_EXPECTATIONS_STARTED,
    PIPELINE_EVENT_LOAD_COMPLETED,
    PIPELINE_EVENT_LOAD_STARTED,
    PIPELINE_EVENT_SCHEMA_COMPLETED,
    PIPELINE_EVENT_SCHEMA_STARTED,
    PIPELINE_EVENT_START,
    PIPELINE_EVENT_WRITE_COMPLETED,
    PIPELINE_EVENT_WRITE_STARTED,
    PipelineConfig,
    QualityReport,
    run_pipeline,
)


@dataclass
class CLIOptions:
    input_dir: Path
    output_path: Path
    country_code: str
    expectation_suite_name: str
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


_PERFORMANCE_FIELDS: list[tuple[str, str]] = [
    ("Load seconds", "load_seconds"),
    ("Aggregation seconds", "aggregation_seconds"),
    ("Expectations seconds", "expectations_seconds"),
    ("Write seconds", "write_seconds"),
    ("Total seconds", "total_seconds"),
    ("Rows per second", "rows_per_second"),
    ("Load rows per second", "load_rows_per_second"),
]

DEFAULT_SENSITIVE_FIELD_TOKENS: tuple[str, ...] = (
    "email",
    "phone",
    "contact",
    "cell",
    "mobile",
    "whatsapp",
)
REDACTED_PLACEHOLDER = "***redacted***"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        type=Path,
        help="Directory containing the raw source Excel files (default: ./data)",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        help=(
            "Destination path for the refined Excel workbook "
            "(default: <input-dir>/refined_data.xlsx)"
        ),
    )
    parser.add_argument(
        "--country-code",
        type=str,
        help="ISO country code for normalising contact data (default: ZA)",
    )
    parser.add_argument(
        "--expectation-suite",
        dest="expectation_suite_name",
        type=str,
        help="Named expectation suite to run (default: default)",
    )
    parser.add_argument(
        "--config",
        dest="config_paths",
        type=Path,
        action="append",
        default=[],
        help="Optional TOML/JSON configuration file applied before CLI flags",
    )
    parser.add_argument(
        "--dist-dir",
        type=Path,
        help="Directory to write packaged archives when --archive is enabled (default: ./dist)",
    )
    parser.add_argument(
        "--log-format",
        choices=["json", "rich"],
        help="Structured logging format to use (default: rich)",
    )
    parser.add_argument(
        "--sensitive-field",
        dest="sensitive_fields",
        action="append",
        default=None,
        help=(
            "Field name to redact from structured logs. Repeat the flag to mask multiple fields."
        ),
    )
    parser.add_argument(
        "--interactive",
        dest="interactive",
        action="store_true",
        help="Force interactive prompts even when not connected to a TTY.",
    )
    parser.add_argument(
        "--no-interactive",
        dest="interactive",
        action="store_false",
        help="Disable interactive prompts even when using rich output.",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        help="Optional path to write the quality report (Markdown or HTML)",
    )
    parser.add_argument(
        "--report-format",
        choices=["markdown", "html"],
        help="Explicit format for the rendered quality report",
    )
    parser.add_argument(
        "--party-store-path",
        type=Path,
        help="Optional path to write the canonical party store as JSON",
    )
    parser.add_argument(
        "--excel-chunk-size",
        type=int,
        help="Chunk size for streaming Excel sheets (enables chunked reading when set)",
    )
    parser.add_argument(
        "--excel-engine",
        type=str,
        help="Explicit pandas Excel engine to use (e.g. openpyxl, pyxlsb)",
    )
    parser.add_argument(
        "--excel-stage-dir",
        type=Path,
        help="Directory to stage chunked Excel reads to parquet for reuse",
    )
    parser.set_defaults(archive=None, interactive=None)
    parser.add_argument(
        "--archive",
        dest="archive",
        action="store_true",
        help="Package the refined workbook into a timestamped zip archive",
    )
    parser.add_argument(
        "--no-archive",
        dest="archive",
        action="store_false",
        help="Disable archive packaging even if enabled via configuration",
    )
    return parser


def parse_args(argv: Sequence[str] | None = None) -> CLIOptions:
    parser = build_parser()
    namespace = parser.parse_args(argv)
    return _resolve_options(namespace)


def _resolve_options(namespace: argparse.Namespace) -> CLIOptions:
    defaults: dict[str, Any] = {
        "input_dir": Path.cwd() / "data",
        "output_path": None,
        "country_code": "ZA",
        "expectation_suite_name": "default",
        "archive": False,
        "dist_dir": Path.cwd() / "dist",
        "log_format": "rich",
        "report_path": None,
        "report_format": None,
        "party_store_path": None,
        "excel_chunk_size": None,
        "excel_engine": None,
        "excel_stage_dir": None,
        "sensitive_fields": list(DEFAULT_SENSITIVE_FIELD_TOKENS),
        "interactive": None,
    }

    config_values: dict[str, Any] = {}
    for config_path in namespace.config_paths:
        if not config_path.exists():
            msg = f"Configuration file not found: {config_path}"
            raise FileNotFoundError(msg)
        config_payload = _load_config(config_path)
        config_values.update(config_payload)

    options = {**defaults, **config_values}

    for field in (
        "input_dir",
        "output_path",
        "country_code",
        "expectation_suite_name",
        "archive",
        "dist_dir",
        "log_format",
        "report_path",
        "report_format",
        "party_store_path",
        "excel_chunk_size",
        "excel_engine",
        "excel_stage_dir",
    ):
        value = getattr(namespace, field, None)
        if value is not None:
            options[field] = value

    if namespace.sensitive_fields is not None:
        options["sensitive_fields"] = list(namespace.sensitive_fields)
    if getattr(namespace, "interactive", None) is not None:
        options["interactive"] = namespace.interactive

    input_dir = Path(options["input_dir"])
    if options["output_path"]:
        output_path = Path(options["output_path"])
    else:
        output_path = input_dir / "refined_data.xlsx"
    dist_dir = Path(options["dist_dir"])
    report_path = Path(options["report_path"]) if options.get("report_path") else None
    stage_dir = Path(options["excel_stage_dir"]) if options.get("excel_stage_dir") else None
    party_store_path = (
        Path(options["party_store_path"]) if options.get("party_store_path") else None
    )

    chunk_size = options.get("excel_chunk_size")
    if chunk_size is not None:
        chunk_size = int(chunk_size)
        if chunk_size <= 0:
            msg = "--excel-chunk-size must be greater than zero"
            raise ValueError(msg)

    report_format = options.get("report_format")
    if isinstance(report_format, str):
        report_format = report_format.lower()
    if report_format is None and report_path is not None:
        report_format = _infer_report_format(report_path)
    elif report_format is not None and report_format not in {"markdown", "html"}:
        msg = f"Unsupported report format: {report_format}"
        raise ValueError(msg)

    log_format = str(options.get("log_format", "rich")).lower()
    if log_format not in {"json", "rich"}:
        msg = f"Unsupported log format: {log_format}"
        raise ValueError(msg)

    archive = bool(options.get("archive", False))

    raw_sensitive = options.get("sensitive_fields")
    tokens: list[str] = []
    if raw_sensitive is None:
        tokens = list(DEFAULT_SENSITIVE_FIELD_TOKENS)
    elif isinstance(raw_sensitive, list | tuple | set):
        for value in raw_sensitive:
            if isinstance(value, str):
                cleaned = value.strip()
                if cleaned:
                    tokens.append(cleaned)
    else:
        cleaned = str(raw_sensitive).strip()
        if cleaned:
            tokens.append(cleaned)
    sensitive_fields = tuple(dict.fromkeys(token.lower() for token in tokens))

    interactive_option = options.get("interactive")
    interactive: bool | None
    if isinstance(interactive_option, bool) or interactive_option is None:
        interactive = interactive_option
    else:
        interactive = bool(interactive_option)

    return CLIOptions(
        input_dir=input_dir,
        output_path=output_path,
        country_code=str(options["country_code"]),
        expectation_suite_name=str(options["expectation_suite_name"]),
        archive=archive,
        dist_dir=dist_dir,
        log_format=log_format,
        report_path=report_path,
        report_format=report_format,
        party_store_path=party_store_path,
        config_paths=list(namespace.config_paths),
        excel_chunk_size=chunk_size,
        excel_engine=(str(options["excel_engine"]) if options.get("excel_engine") else None),
        excel_stage_dir=stage_dir,
        sensitive_fields=sensitive_fields,
        interactive=interactive,
    )


def _load_config(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    if suffix in {".toml", ".tml"}:
        return tomllib.loads(path.read_text())
    if suffix == ".json":
        return json.loads(path.read_text())
    msg = f"Unsupported configuration format: {path}"
    raise ValueError(msg)


def _infer_report_format(report_path: Path) -> str | None:
    suffix = report_path.suffix.lower()
    if suffix in {".md", ".markdown"}:
        return "markdown"
    if suffix in {".html", ".htm"}:
        return "html"
    return None


class PipelineProgress:
    def __init__(
        self,
        console: Console,
        *,
        progress_factory: Callable[..., Any] = Progress,
        throttle_seconds: float = 0.05,
    ) -> None:
        self._progress = progress_factory(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=True,
        )
        self._tasks: dict[str, TaskID] = {}
        self._aggregate_total = 0
        self._aggregate_progress_total = 1
        self._aggregate_last_completed = 0
        self._aggregate_last_update_time = 0.0
        self._aggregate_throttled_updates = 0
        self._throttle_seconds = max(0.0, throttle_seconds)

    def __enter__(self) -> PipelineProgress:
        self._progress.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - delegated cleanup
        self._progress.__exit__(exc_type, exc, tb)

    def handle_event(self, event: str, payload: dict[str, Any]) -> None:
        if event == PIPELINE_EVENT_START:
            self._progress.log("[bold cyan]Starting pipeline[/bold cyan]")
        elif event == PIPELINE_EVENT_LOAD_STARTED:
            self._start_task("load", "Loading source files")
        elif event == PIPELINE_EVENT_LOAD_COMPLETED:
            rows = int(payload.get("total_rows", 0))
            sources = payload.get("sources", []) or []
            message = f"[green]Loaded {rows} rows from {len(sources)} source(s)[/green]"
            self._complete_task("load", message)
        elif event == PIPELINE_EVENT_AGGREGATE_STARTED:
            total = int(payload.get("total", 0))
            self._aggregate_total = total if total > 0 else 0
            self._aggregate_progress_total = self._aggregate_total or 1
            self._aggregate_last_completed = 0
            self._aggregate_last_update_time = 0.0
            self._aggregate_throttled_updates = 0
            self._start_task(
                "aggregate",
                "Aggregating organisations",
                total=self._aggregate_progress_total,
            )
        elif event == PIPELINE_EVENT_AGGREGATE_PROGRESS:
            task_id = self._tasks.get("aggregate")
            if task_id is not None:
                if self._aggregate_total <= 0:
                    self._aggregate_last_completed = self._aggregate_progress_total
                    self._aggregate_last_update_time = time.perf_counter()
                    self._progress.update(task_id, completed=self._aggregate_progress_total)
                else:
                    completed = int(payload.get("completed", 0))
                    completed = max(0, min(completed, self._aggregate_progress_total))
                    now = time.perf_counter()
                    final_update = completed >= self._aggregate_progress_total
                    if not final_update and completed == self._aggregate_last_completed:
                        return
                    if (
                        not final_update
                        and self._throttle_seconds > 0.0
                        and now - self._aggregate_last_update_time < self._throttle_seconds
                    ):
                        self._aggregate_throttled_updates += 1
                        return
                    self._aggregate_last_update_time = now
                    self._aggregate_last_completed = completed
                    self._progress.update(task_id, completed=completed)
        elif event == PIPELINE_EVENT_AGGREGATE_COMPLETED:
            aggregated = int(payload.get("aggregated_records", 0))
            conflicts = int(payload.get("conflicts", 0))
            message = f"[green]Aggregated {aggregated} record(s)[/green]"
            if conflicts:
                message += f" with [yellow]{conflicts}[/yellow] conflict(s) resolved"
            self._complete_task("aggregate", message)
            self._emit_throttle_summary()
        elif event == PIPELINE_EVENT_SCHEMA_STARTED:
            self._start_task("schema", "Validating schema")
        elif event == PIPELINE_EVENT_SCHEMA_COMPLETED:
            errors = int(payload.get("errors", 0))
            if errors:
                message = f"[yellow]Schema validation reported {errors} issue(s)[/yellow]"
            else:
                message = "[green]Schema validation passed[/green]"
            self._complete_task("schema", message)
        elif event == PIPELINE_EVENT_EXPECTATIONS_STARTED:
            self._start_task("expectations", "Evaluating expectations")
        elif event == PIPELINE_EVENT_EXPECTATIONS_COMPLETED:
            success = bool(payload.get("success", False))
            failure_count = int(payload.get("failure_count", 0))
            if success:
                message = "[green]Expectations passed[/green]"
            else:
                message = f"[yellow]Expectations failed ({failure_count} issue(s))[/yellow]"
            self._complete_task("expectations", message)
        elif event == PIPELINE_EVENT_WRITE_STARTED:
            self._start_task("write", "Writing refined dataset")
        elif event == PIPELINE_EVENT_WRITE_COMPLETED:
            seconds = float(payload.get("write_seconds", 0.0))
            message = f"[green]Refined data persisted in {seconds:.2f}s[/green]"
            self._complete_task("write", message)
        elif event == PIPELINE_EVENT_COMPLETED:
            total = int(payload.get("total_records", 0))
            invalid = int(payload.get("invalid_records", 0))
            duration = float(payload.get("duration", 0.0))
            summary = (
                f"[bold green]Pipeline finished[/bold green]: {total} records, "
                f"{invalid} invalid, {duration:.2f}s"
            )
            self._progress.log(summary)

    def _start_task(self, name: str, description: str, *, total: int = 1) -> None:
        if name in self._tasks:
            return
        task_id = self._progress.add_task(description, total=total or 1)
        self._tasks[name] = task_id

    def _complete_task(self, name: str, message: str | None = None) -> None:
        task_id = self._tasks.pop(name, None)
        if task_id is not None:
            task = next((task for task in self._progress.tasks if task.id == task_id), None)
            total = task.total if task and task.total else 1
            self._progress.update(task_id, total=total, completed=total)
        if message:
            self._progress.log(message)

    def _emit_throttle_summary(self) -> None:
        if self._aggregate_throttled_updates:
            suppressed = self._aggregate_throttled_updates
            self._aggregate_throttled_updates = 0
            self._progress.log(f"[dim]Suppressed {suppressed} aggregate progress update(s)[/dim]")


class StructuredLogger:
    def __init__(self, log_format: str, sensitive_fields: Iterable[str] | None = None) -> None:
        self.log_format = log_format
        self.console: Console | None = Console() if log_format == "rich" else None
        tokens = (
            sensitive_fields if sensitive_fields is not None else DEFAULT_SENSITIVE_FIELD_TOKENS
        )
        self._sensitive_tokens = {token.lower() for token in tokens}

    def _get_console(self) -> Console:
        if self.console is None:  # pragma: no cover - defensive safeguard
            msg = "Rich console not initialised"
            raise RuntimeError(msg)
        return self.console

    def _emit_json(self, event: str, data: dict[str, Any]) -> None:
        serialisable = {
            "event": event,
            "data": _convert_paths(self._mask_payload(data)),
        }
        print(json.dumps(serialisable))

    def _mask_payload(self, data: dict[str, Any]) -> dict[str, Any]:
        return {key: self._redact_value(key, value) for key, value in data.items()}

    def _redact_value(self, key: str, value: Any) -> Any:
        if self._should_redact(key):
            if isinstance(value, list):
                return [REDACTED_PLACEHOLDER for _ in value]
            if isinstance(value, dict):
                return {nested_key: REDACTED_PLACEHOLDER for nested_key in value}
            return REDACTED_PLACEHOLDER
        if isinstance(value, dict):
            return {
                nested_key: self._redact_value(nested_key, nested_value)
                for nested_key, nested_value in value.items()
            }
        if isinstance(value, list):
            return [self._redact_value(key, item) for item in value]
        return value

    def _should_redact(self, key: str) -> bool:
        lowered = key.lower()
        return any(token in lowered for token in self._sensitive_tokens)

    def log_summary(self, report: QualityReport) -> None:
        if self.log_format == "json":
            self._emit_json("pipeline.summary", report.to_dict())
            return

        console = self._get_console()
        table = Table(
            title="Hotpass Quality Report",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")
        table.add_row("Total records", str(report.total_records))
        table.add_row("Invalid records", str(report.invalid_records))
        table.add_row("Expectations passed", "Yes" if report.expectations_passed else "No")
        mean_score = f"{report.data_quality_distribution.get('mean', 0.0):.2f}"
        min_score = f"{report.data_quality_distribution.get('min', 0.0):.2f}"
        max_score = f"{report.data_quality_distribution.get('max', 0.0):.2f}"
        table.add_row("Mean quality score", mean_score)
        table.add_row("Min quality score", min_score)
        table.add_row("Max quality score", max_score)
        console.print(table)

        if report.source_breakdown:
            breakdown = Table(title="Source Breakdown", show_header=True)
            breakdown.add_column("Source", style="cyan")
            breakdown.add_column("Records", justify="right")
            for source, count in sorted(report.source_breakdown.items()):
                breakdown.add_row(source, str(count))
            console.print(breakdown)

        if report.schema_validation_errors:
            console.print("[bold yellow]Schema Validation Errors:[/bold yellow]")
            for error in report.schema_validation_errors:
                console.print(f"  • {error}")
        if report.expectation_failures:
            console.print("[bold yellow]Expectation Failures:[/bold yellow]")
            for failure in report.expectation_failures:
                console.print(f"  • {failure}")

        if report.performance_metrics:
            metrics_table = Table(title="Performance Metrics", show_header=True)
            metrics_table.add_column("Metric", style="cyan")
            metrics_table.add_column("Value", justify="right")
            for label, key in _PERFORMANCE_FIELDS:
                value = report.performance_metrics.get(key)
                if value is None:
                    continue
                metrics_table.add_row(label, _format_metric_value(value))
            console.print(metrics_table)

            source_metrics = report.performance_metrics.get("source_load_seconds", {})
            if source_metrics:
                source_table = Table(title="Source Load Durations", show_header=True)
                source_table.add_column("Loader", style="cyan")
                source_table.add_column("Seconds", justify="right")
                for loader, seconds in sorted(source_metrics.items()):
                    source_table.add_row(loader, _format_metric_value(seconds))
                console.print(source_table)
        else:
            console.print("[italic]No performance metrics recorded.[/italic]")

    def log_archive(self, archive_path: Path) -> None:
        if self.log_format == "json":
            self._emit_json("archive.created", {"path": archive_path})
            return

        console = self._get_console()
        console.print(f"[green]Archive created:[/green] {archive_path}")

    def log_report_write(self, report_path: Path, report_format: str | None) -> None:
        data = {"path": report_path, "format": report_format}
        if self.log_format == "json":
            self._emit_json("report.write", data)
            return

        console = self._get_console()
        label = report_format or "auto"
        console.print(f"[green]Quality report written ({label}):[/green] {report_path}")

    def log_party_store(self, output_path: Path) -> None:
        if self.log_format == "json":
            self._emit_json("party_store.write", {"path": output_path})
            return

        console = self._get_console()
        console.print(f"[green]Party store exported:[/green] {output_path}")

    def log_error(self, message: str) -> None:
        if self.log_format == "json":
            self._emit_json("error", {"message": message})
            return

        console = self._get_console()
        console.print(f"[bold red]Error:[/bold red] {message}")


def _convert_paths(data: dict[str, Any]) -> dict[str, Any]:
    converted: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, Path):
            converted[key] = str(value)
        else:
            converted[key] = value
    return converted


def _format_metric_value(value: Any) -> str:
    if isinstance(value, int | float):
        return f"{float(value):.4f}"
    return str(value)


def main(argv: Sequence[str] | None = None) -> int:
    try:
        options = parse_args(argv)
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    logger = StructuredLogger(options.log_format, options.sensitive_fields)
    console = Console() if options.log_format == "rich" else None
    interactive = options.interactive
    if interactive is None:
        interactive = console is not None and sys.stdin.isatty()

    # Pre-flight validation
    if not options.input_dir.exists():
        logger.log_error(f"Input directory does not exist: {options.input_dir}")
        logger.log_error("Please create the directory or specify a different path with --input-dir")
        return 1

    if not options.input_dir.is_dir():
        logger.log_error(f"Input path is not a directory: {options.input_dir}")
        return 1

    # Check for Excel files
    excel_files = list(options.input_dir.glob("*.xlsx")) + list(options.input_dir.glob("*.xls"))
    if not excel_files:
        logger.log_error(f"No Excel files found in: {options.input_dir}")
        logger.log_error("Please add Excel files to the input directory")
        return 1

    # Log startup info
    if console:
        console.print("[bold cyan]Hotpass Data Refinement Pipeline[/bold cyan]")
        console.print(f"[dim]Input directory:[/dim] {options.input_dir}")
        console.print(f"[dim]Output path:[/dim] {options.output_path}")
        console.print(f"[dim]Found {len(excel_files)} Excel file(s)[/dim]")
        console.print()

    excel_options = None
    if any(
        value is not None
        for value in (
            options.excel_chunk_size,
            options.excel_engine,
            options.excel_stage_dir,
        )
    ):
        excel_options = ExcelReadOptions(
            chunk_size=options.excel_chunk_size,
            engine=options.excel_engine,
            stage_to_parquet=options.excel_stage_dir is not None,
            stage_dir=options.excel_stage_dir,
        )

    progress_context = PipelineProgress(console) if console else nullcontext(None)
    result = None
    with progress_context as progress:
        listener: Callable[[str, dict[str, Any]], None] | None
        if isinstance(progress, PipelineProgress):
            listener = progress.handle_event
        else:
            listener = None

        config = PipelineConfig(
            input_dir=options.input_dir,
            output_path=options.output_path,
            expectation_suite_name=options.expectation_suite_name,
            country_code=options.country_code,
            excel_options=excel_options,
            progress_listener=listener,
        )

        try:
            result = run_pipeline(config)
        except Exception as exc:  # pragma: no cover - surface runtime failures
            logger.log_error(str(exc))
            if console:
                console.print("[bold red]Pipeline failed with error:[/bold red]")
                console.print_exception()
            return 1

    if result is None:  # pragma: no cover - defensive safeguard
        msg = "Pipeline run did not return a result"
        raise RuntimeError(msg)

    report = result.quality_report
    logger.log_summary(report)

    # Success message
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
        options.party_store_path.write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )
        logger.log_party_store(options.party_store_path)

    if options.archive:
        options.dist_dir.mkdir(parents=True, exist_ok=True)
        archive_path = create_refined_archive(options.output_path, options.dist_dir)
        logger.log_archive(archive_path)

    return 0


if __name__ == "__main__":  # pragma: no cover - console entry point
    raise SystemExit(main())
