"""Command line interface for running the Hotpass refinement pipeline."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import tomllib
from rich.console import Console
from rich.table import Table

from hotpass.artifacts import create_refined_archive
from hotpass.data_sources import ExcelReadOptions
from hotpass.pipeline import PipelineConfig, QualityReport, run_pipeline


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
    config_paths: list[Path]
    excel_chunk_size: int | None
    excel_engine: str | None
    excel_stage_dir: Path | None


_PERFORMANCE_FIELDS: list[tuple[str, str]] = [
    ("Load seconds", "load_seconds"),
    ("Aggregation seconds", "aggregation_seconds"),
    ("Expectations seconds", "expectations_seconds"),
    ("Write seconds", "write_seconds"),
    ("Total seconds", "total_seconds"),
    ("Rows per second", "rows_per_second"),
    ("Load rows per second", "load_rows_per_second"),
]


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
    parser.set_defaults(archive=None)
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
        "excel_chunk_size": None,
        "excel_engine": None,
        "excel_stage_dir": None,
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
        "excel_chunk_size",
        "excel_engine",
        "excel_stage_dir",
    ):
        value = getattr(namespace, field, None)
        if value is not None:
            options[field] = value

    input_dir = Path(options["input_dir"])
    if options["output_path"]:
        output_path = Path(options["output_path"])
    else:
        output_path = input_dir / "refined_data.xlsx"
    dist_dir = Path(options["dist_dir"])
    report_path = Path(options["report_path"]) if options.get("report_path") else None
    stage_dir = Path(options["excel_stage_dir"]) if options.get("excel_stage_dir") else None

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
        config_paths=list(namespace.config_paths),
        excel_chunk_size=chunk_size,
        excel_engine=str(options["excel_engine"]) if options.get("excel_engine") else None,
        excel_stage_dir=stage_dir,
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


class StructuredLogger:
    def __init__(self, log_format: str) -> None:
        self.log_format = log_format
        self.console: Console | None = Console() if log_format == "rich" else None

    def _get_console(self) -> Console:
        if self.console is None:  # pragma: no cover - defensive safeguard
            msg = "Rich console not initialised"
            raise RuntimeError(msg)
        return self.console

    def _emit_json(self, event: str, data: dict[str, Any]) -> None:
        serialisable = {
            "event": event,
            "data": _convert_paths(data),
        }
        print(json.dumps(serialisable))

    def log_summary(self, report: QualityReport) -> None:
        if self.log_format == "json":
            self._emit_json("pipeline.summary", report.to_dict())
            return

        console = self._get_console()
        table = Table(title="Hotpass Quality Report", show_header=True, header_style="bold magenta")
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

    logger = StructuredLogger(options.log_format)

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

    config = PipelineConfig(
        input_dir=options.input_dir,
        output_path=options.output_path,
        expectation_suite_name=options.expectation_suite_name,
        country_code=options.country_code,
        excel_options=excel_options,
    )

    try:
        result = run_pipeline(config)
    except Exception as exc:  # pragma: no cover - surface runtime failures
        logger.log_error(str(exc))
        return 1

    report = result.quality_report
    logger.log_summary(report)

    if options.report_path is not None:
        options.report_path.parent.mkdir(parents=True, exist_ok=True)
        if options.report_format == "html":
            options.report_path.write_text(report.to_html(), encoding="utf-8")
        else:
            options.report_path.write_text(report.to_markdown(), encoding="utf-8")
        logger.log_report_write(options.report_path, options.report_format)

    if options.archive:
        options.dist_dir.mkdir(parents=True, exist_ok=True)
        archive_path = create_refined_archive(options.output_path, options.dist_dir)
        logger.log_archive(archive_path)

    return 0


if __name__ == "__main__":  # pragma: no cover - console entry point
    raise SystemExit(main())
