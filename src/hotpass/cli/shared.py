"""Shared helper functions and parent parsers for CLI commands."""

from __future__ import annotations

import argparse
import json
import tomllib
from collections.abc import Iterable
from pathlib import Path
from typing import Any


def make_base_parser() -> argparse.ArgumentParser:
    """Create the base parser with configuration/profile options."""

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--profile",
        help="Configuration profile name or path",
    )
    parser.add_argument(
        "--profile-search-path",
        dest="profile_search_paths",
        action="append",
        type=Path,
        help="Additional directory to search for named profiles",
    )
    parser.add_argument(
        "--config",
        dest="config_paths",
        action="append",
        type=Path,
        help="Configuration file merged before command-line flags (TOML/JSON)",
    )
    parser.add_argument(
        "--log-format",
        choices=["json", "rich"],
        help="Structured logging format to use",
    )
    parser.add_argument(
        "--sensitive-field",
        dest="sensitive_fields",
        action="append",
        help="Field name to redact from structured logs (repeat for multiple fields)",
    )
    parser.add_argument(
        "--interactive",
        dest="interactive",
        action="store_true",
        help="Force interactive prompts even when stdout is not a TTY",
    )
    parser.add_argument(
        "--no-interactive",
        dest="interactive",
        action="store_false",
        help="Disable interactive prompts and confirmation dialogs",
    )
    parser.add_argument(
        "--qa-mode",
        choices=["default", "strict", "relaxed"],
        help="QA controls preset (strict enables guardrails, relaxed minimises prompts)",
    )
    parser.add_argument(
        "--observability",
        dest="observability",
        action="store_true",
        help="Emit observability telemetry (OpenTelemetry exporters, structured events)",
    )
    parser.add_argument(
        "--no-observability",
        dest="observability",
        action="store_false",
        help="Disable observability exporters regardless of profile settings",
    )
    parser.set_defaults(interactive=None, observability=None)
    return parser


def make_pipeline_parser() -> argparse.ArgumentParser:
    """Create parser containing pipeline input/output options."""

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--input-dir",
        type=Path,
        help="Directory containing raw source spreadsheets",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        help="Destination path for the refined Excel workbook",
    )
    parser.add_argument(
        "--expectation-suite",
        dest="expectation_suite_name",
        help="Named expectation suite to execute",
    )
    parser.add_argument(
        "--country-code",
        help="ISO country code applied when normalising contact data",
    )
    parser.add_argument(
        "--dist-dir",
        type=Path,
        help="Directory to write packaged archives when --archive is enabled",
    )
    parser.add_argument(
        "--intent-digest-path",
        type=Path,
        help="Optional path to write the daily intent digest export",
    )
    parser.add_argument(
        "--intent-signal-store",
        type=Path,
        help="Persist raw intent signals to the given path for reuse",
    )
    parser.add_argument(
        "--daily-list-path",
        type=Path,
        help="Path to write the generated daily lead list",
    )
    parser.add_argument(
        "--daily-list-size",
        type=int,
        help="Maximum number of prospects to include in the daily list",
    )
    parser.add_argument(
        "--intent-webhook",
        dest="intent_webhooks",
        action="append",
        help="Webhook URL notified after intent digest generation (repeatable)",
    )
    parser.add_argument(
        "--crm-endpoint",
        help="CRM endpoint to receive the daily list payload",
    )
    parser.add_argument(
        "--crm-token",
        help="Authentication token passed to the CRM endpoint",
    )
    parser.add_argument(
        "--automation-http-timeout",
        type=float,
        help="Timeout in seconds for automation webhook and CRM deliveries",
    )
    parser.add_argument(
        "--automation-http-retries",
        type=int,
        help="Maximum retry attempts for automation deliveries",
    )
    parser.add_argument(
        "--automation-http-backoff",
        dest="automation_http_backoff",
        type=float,
        help="Exponential backoff factor applied between automation retries",
    )
    parser.add_argument(
        "--automation-http-backoff-max",
        dest="automation_http_backoff_max",
        type=float,
        help="Maximum backoff interval in seconds for automation retries",
    )
    parser.add_argument(
        "--automation-http-circuit-threshold",
        dest="automation_http_circuit_threshold",
        type=int,
        help="Consecutive failures before the automation circuit opens",
    )
    parser.add_argument(
        "--automation-http-circuit-reset",
        dest="automation_http_circuit_reset",
        type=float,
        help="Duration in seconds before automation circuit half-opens",
    )
    parser.add_argument(
        "--automation-http-idempotency-header",
        help="Custom header name used when generating idempotency keys",
    )
    parser.add_argument(
        "--automation-http-dead-letter",
        type=Path,
        help="Path to append failed automation payloads as newline-delimited JSON",
    )
    parser.add_argument(
        "--automation-http-dead-letter-enabled",
        dest="automation_http_dead_letter_enabled",
        action="store_true",
        help="Enable dead-letter persistence for automation failures",
    )
    parser.add_argument(
        "--no-automation-http-dead-letter",
        dest="automation_http_dead_letter_enabled",
        action="store_false",
        help="Disable dead-letter persistence even if configured",
    )
    parser.add_argument(
        "--party-store-path",
        type=Path,
        help="Optional path to write the canonical party store as JSON",
    )
    parser.add_argument(
        "--archive",
        dest="archive",
        action="store_true",
        help="Package the refined workbook into a timestamped archive",
    )
    parser.add_argument(
        "--no-archive",
        dest="archive",
        action="store_false",
        help="Disable archive packaging even if configured by profiles",
    )
    parser.set_defaults(archive=None, automation_http_dead_letter_enabled=None)
    return parser


def make_reporting_parser() -> argparse.ArgumentParser:
    """Create parser containing reporting-related options."""

    parser = argparse.ArgumentParser(add_help=False)
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
    return parser


def make_excel_parser() -> argparse.ArgumentParser:
    """Create parser exposing Excel ingestion tuning options."""

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--excel-chunk-size",
        type=int,
        help="Chunk size for streaming Excel sheets (enables chunked reading)",
    )
    parser.add_argument(
        "--excel-engine",
        help="Explicit pandas Excel engine to use (e.g. openpyxl, pyxlsb)",
    )
    parser.add_argument(
        "--excel-stage-dir",
        type=Path,
        help="Directory to stage chunked Excel reads to parquet for reuse",
    )
    return parser


def load_config(path: Path) -> dict[str, Any]:
    """Load a configuration file supporting TOML and JSON."""

    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    if suffix in {".toml", ".tml"}:
        return tomllib.loads(text)
    if suffix == ".json":
        return json.loads(text)
    msg = f"Unsupported configuration format: {path}"
    raise ValueError(msg)


def infer_report_format(report_path: Path) -> str | None:
    """Infer report format from file suffix."""

    suffix = report_path.suffix.lower()
    if suffix in {".md", ".markdown"}:
        return "markdown"
    if suffix in {".html", ".htm"}:
        return "html"
    return None


def normalise_sensitive_fields(
    raw_values: Iterable[str] | None,
    default_tokens: Iterable[str],
) -> tuple[str, ...]:
    """Normalise sensitive field tokens to a deterministic, deduplicated tuple."""

    tokens = list(default_tokens)
    if raw_values is not None:
        for value in raw_values:
            cleaned = value.strip()
            if cleaned:
                tokens.append(cleaned)
    normalised = [token.lower() for token in tokens]
    return tuple(dict.fromkeys(normalised))


__all__ = [
    "infer_report_format",
    "load_config",
    "make_base_parser",
    "make_excel_parser",
    "make_pipeline_parser",
    "make_reporting_parser",
    "normalise_sensitive_fields",
]
