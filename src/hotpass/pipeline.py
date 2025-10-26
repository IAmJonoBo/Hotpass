"""Pipeline orchestration for producing the Hotpass SSOT workbook."""

from __future__ import annotations

import html
import json
import logging
import re
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import duckdb
import pandas as pd
import polars as pl
from pandera.errors import SchemaErrors

from .config import IndustryProfile, get_default_profile
from .data_sources import (
    ExcelReadOptions,
    load_contact_database,
    load_reachout_database,
    load_sacaa_cleaned,
)
from .domain.party import PartyStore, build_party_store_from_refined
from .formatting import OutputFormat, apply_excel_formatting, create_summary_sheet
from .normalization import clean_string, coalesce, normalize_province, slugify

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from .linkage import LinkageResult
from .pipeline_reporting import (
    collect_unique,
    generate_recommendations,
    html_performance_rows,
    html_source_performance,
)
from .quality import ExpectationSummary, build_ssot_schema, run_expectations
from .validation import load_schema_descriptor

# Set up module logger
logger = logging.getLogger(__name__)

ProgressListener = Callable[[str, dict[str, Any]], None]


PIPELINE_EVENT_START = "pipeline.start"
PIPELINE_EVENT_LOAD_STARTED = "load.started"
PIPELINE_EVENT_LOAD_COMPLETED = "load.completed"
PIPELINE_EVENT_AGGREGATE_STARTED = "aggregate.started"
PIPELINE_EVENT_AGGREGATE_PROGRESS = "aggregate.progress"
PIPELINE_EVENT_AGGREGATE_COMPLETED = "aggregate.completed"
PIPELINE_EVENT_SCHEMA_STARTED = "schema.started"
PIPELINE_EVENT_SCHEMA_COMPLETED = "schema.completed"
PIPELINE_EVENT_EXPECTATIONS_STARTED = "expectations.started"
PIPELINE_EVENT_EXPECTATIONS_COMPLETED = "expectations.completed"
PIPELINE_EVENT_WRITE_STARTED = "write.started"
PIPELINE_EVENT_WRITE_COMPLETED = "write.completed"
PIPELINE_EVENT_COMPLETED = "pipeline.completed"


SSOT_COLUMNS: list[str] = [
    "organization_name",
    "organization_slug",
    "province",
    "country",
    "area",
    "address_primary",
    "organization_category",
    "organization_type",
    "status",
    "website",
    "planes",
    "description",
    "notes",
    "source_datasets",
    "source_record_ids",
    "contact_primary_name",
    "contact_primary_role",
    "contact_primary_email",
    "contact_primary_phone",
    "contact_secondary_emails",
    "contact_secondary_phones",
    "data_quality_score",
    "data_quality_flags",
    "selection_provenance",
    "last_interaction_date",
    "priority",
    "privacy_basis",
]


SOURCE_PRIORITY: dict[str, int] = {
    "SACAA Cleaned": 3,
    "Reachout Database": 2,
    "Contact Database": 1,
}


def _write_csvw_metadata(output_path: Path) -> None:
    """Persist a CSVW sidecar aligned with the SSOT schema."""
    schema_descriptor = load_schema_descriptor("ssot.schema.json")
    sidecar = output_path.with_suffix(f"{output_path.suffix}-metadata.json")
    metadata = {
        "@context": "http://www.w3.org/ns/csvw",
        "url": output_path.name,
        "tableSchema": schema_descriptor,
    }
    with sidecar.open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)


@dataclass(frozen=True)
class RowMetadata:
    index: int
    source_dataset: str
    source_record_id: str | None
    source_priority: int
    quality_score: int
    last_interaction: pd.Timestamp | None


@dataclass(frozen=True)
class ValueSelection:
    value: str
    row_metadata: RowMetadata


def _parse_last_interaction(value: object | None) -> pd.Timestamp | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, pd.Timestamp):
        timestamp = pd.to_datetime(value, utc=True)
        return timestamp if pd.notna(timestamp) else None
    text = str(value).strip()
    if not text:
        return None
    prefer_dayfirst = not YEAR_FIRST_PATTERN.match(text)
    timestamp = pd.to_datetime(
        text,
        errors="coerce",
        dayfirst=prefer_dayfirst,
        utc=True,
    )
    if pd.isna(timestamp):
        timestamp = pd.to_datetime(
            text,
            errors="coerce",
            dayfirst=not prefer_dayfirst,
            utc=True,
        )
    if pd.isna(timestamp):
        return None
    return timestamp


def _value_present(value: object | None) -> bool:
    if isinstance(value, list):
        return any(_value_present(item) for item in value)
    return bool(clean_string(value))


def _row_quality_score(row: pd.Series) -> int:
    checks = [
        _value_present(row.get("contact_emails")),
        _value_present(row.get("contact_phones")),
        _value_present(row.get("website")),
        _value_present(row.get("province")),
        _value_present(row.get("address")),
    ]
    return sum(1 for present in checks if present)


@dataclass
class PipelineConfig:
    input_dir: Path
    output_path: Path
    expectation_suite_name: str = "default"
    country_code: str = "ZA"
    excel_options: ExcelReadOptions | None = None
    industry_profile: IndustryProfile | None = None
    output_format: OutputFormat | None = None
    enable_formatting: bool = True
    enable_audit_trail: bool = True
    enable_recommendations: bool = True
    progress_listener: ProgressListener | None = None


@dataclass
class QualityReport:
    total_records: int
    invalid_records: int
    schema_validation_errors: list[str]
    expectations_passed: bool
    expectation_failures: list[str]
    source_breakdown: dict[str, int]
    data_quality_distribution: dict[str, float]
    performance_metrics: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    audit_trail: list[dict[str, Any]] = field(default_factory=list)
    conflict_resolutions: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_records": self.total_records,
            "invalid_records": self.invalid_records,
            "schema_validation_errors": list(self.schema_validation_errors),
            "expectations_passed": self.expectations_passed,
            "expectation_failures": list(self.expectation_failures),
            "source_breakdown": dict(self.source_breakdown),
            "data_quality_distribution": dict(self.data_quality_distribution),
            "performance_metrics": dict(self.performance_metrics),
            "recommendations": list(self.recommendations),
            "audit_trail": list(self.audit_trail),
            "conflict_resolutions": list(self.conflict_resolutions),
        }

    def to_markdown(self) -> str:
        lines = ["# Hotpass Quality Report", ""]
        lines.extend(
            [
                "## Quality Metrics",
                "",
                "| Metric | Value |",
                "| --- | ---: |",
                f"| Total records | {self.total_records} |",
                f"| Invalid records | {self.invalid_records} |",
                f"| Expectations passed | {'Yes' if self.expectations_passed else 'No'} |",
                f"| Mean quality score | {self.data_quality_distribution.get('mean', 0.0):.2f} |",
                f"| Min quality score | {self.data_quality_distribution.get('min', 0.0):.2f} |",
                f"| Max quality score | {self.data_quality_distribution.get('max', 0.0):.2f} |",
                "",
            ]
        )

        lines.append("## Source Breakdown")
        lines.append("")
        if self.source_breakdown:
            lines.extend(["| Source | Records |", "| --- | ---: |"])
            for source, count in sorted(self.source_breakdown.items()):
                lines.append(f"| {source} | {count} |")
        else:
            lines.append("No source data recorded.")
        lines.append("")

        lines.append("## Schema Validation Errors")
        lines.append("")
        if self.schema_validation_errors:
            lines.extend(f"- {error}" for error in self.schema_validation_errors)
        else:
            lines.append("None")
        lines.append("")

        lines.append("## Expectation Failures")
        lines.append("")
        if self.expectation_failures:
            lines.extend(f"- {failure}" for failure in self.expectation_failures)
        else:
            lines.append("None")
        lines.append("")

        # Add recommendations section
        if self.recommendations:
            lines.append("## Recommendations")
            lines.append("")
            lines.extend(f"- {rec}" for rec in self.recommendations)
            lines.append("")

        # Add conflict resolution section
        if self.conflict_resolutions:
            lines.append("## Conflict Resolutions")
            lines.append("")
            lines.append("| Field | Chosen Source | Value | Alternatives |")
            lines.append("| --- | --- | --- | --- |")
            for conflict in self.conflict_resolutions[:10]:  # Limit to first 10
                field = conflict.get("field", "Unknown")
                source = conflict.get("chosen_source", "Unknown")
                value = str(conflict.get("value", ""))[:50]  # Truncate long values
                alt_count = len(conflict.get("alternatives", []))
                lines.append(f"| {field} | {source} | {value} | {alt_count} alternatives |")
            if len(self.conflict_resolutions) > 10:
                remaining = len(self.conflict_resolutions) - 10
                lines.append(f"| ... | ... | ... | {remaining} more conflicts |")
            lines.append("")

        lines.append("## Performance Metrics")
        lines.append("")
        if self.performance_metrics:
            lines.extend(["| Metric | Value |", "| --- | ---: |"])
            primary_metrics = [
                ("Load seconds", self.performance_metrics.get("load_seconds")),
                (
                    "Aggregation seconds",
                    self.performance_metrics.get("aggregation_seconds"),
                ),
                (
                    "Expectations seconds",
                    self.performance_metrics.get("expectations_seconds"),
                ),
                ("Write seconds", self.performance_metrics.get("write_seconds")),
                ("Total seconds", self.performance_metrics.get("total_seconds")),
                ("Rows per second", self.performance_metrics.get("rows_per_second")),
                (
                    "Load rows per second",
                    self.performance_metrics.get("load_rows_per_second"),
                ),
            ]
            for label, raw_value in primary_metrics:
                if raw_value is None:
                    continue
                if isinstance(raw_value, int | float):
                    value = f"{float(raw_value):.4f}"
                else:
                    value = str(raw_value)
                lines.append(f"| {label} | {value} |")
            lines.append("")

            source_metrics = self.performance_metrics.get("source_load_seconds", {})
            if source_metrics:
                lines.append("### Source Load Durations")
                lines.append("")
                lines.extend(["| Loader | Seconds |", "| --- | ---: |"])
                for loader, seconds in sorted(source_metrics.items()):
                    lines.append(f"| {loader} | {float(seconds):.4f} |")
                lines.append("")
        else:
            lines.append("No performance metrics recorded.")
            lines.append("")

        return "\n".join(lines) + "\n"

    def to_html(self) -> str:
        def _metrics_row(label: str, value: str) -> str:
            return (
                f'<tr><th scope="row">{html.escape(label)}</th><td>{html.escape(value)}</td></tr>'
            )

        quality_rows = [
            _metrics_row("Total records", str(self.total_records)),
            _metrics_row("Invalid records", str(self.invalid_records)),
            _metrics_row("Expectations passed", "Yes" if self.expectations_passed else "No"),
            _metrics_row(
                "Mean quality score",
                f"{self.data_quality_distribution.get('mean', 0.0):.2f}",
            ),
            _metrics_row(
                "Min quality score",
                f"{self.data_quality_distribution.get('min', 0.0):.2f}",
            ),
            _metrics_row(
                "Max quality score",
                f"{self.data_quality_distribution.get('max', 0.0):.2f}",
            ),
        ]

        source_rows = "".join(
            f"<tr><td>{html.escape(source)}</td><td>{count}</td></tr>"
            for source, count in sorted(self.source_breakdown.items())
        )
        if not source_rows:
            source_rows = '<tr><td colspan="2">No source data recorded.</td></tr>'

        schema_items = (
            "".join(f"<li>{html.escape(error)}</li>" for error in self.schema_validation_errors)
            or "<li>None</li>"
        )
        expectation_items = (
            "".join(f"<li>{html.escape(failure)}</li>" for failure in self.expectation_failures)
            or "<li>None</li>"
        )

        return (
            "<!DOCTYPE html>\n"
            '<html lang="en">\n'
            "<head>\n"
            '  <meta charset="utf-8" />\n'
            "  <title>Hotpass Quality Report</title>\n"
            "  <style>\n"
            "    body { font-family: Arial, sans-serif; margin: 2rem; }\n"
            "    table { border-collapse: collapse; width: 100%; margin-bottom: 1.5rem; }\n"
            "    th, td { border: 1px solid #ccc; padding: 0.5rem; text-align: left; }\n"
            "    th { background: #f7f7f7; }\n"
            "  </style>\n"
            "</head>\n"
            "<body>\n"
            "  <h1>Hotpass Quality Report</h1>\n"
            "  <h2>Quality Metrics</h2>\n"
            "  <table>\n"
            "    <tbody>\n"
            f"      {''.join(quality_rows)}\n"
            "    </tbody>\n"
            "  </table>\n"
            "  <h2>Source Breakdown</h2>\n"
            "  <table>\n"
            "    <thead><tr><th>Source</th><th>Records</th></tr></thead>\n"
            "    <tbody>\n"
            f"      {source_rows}\n"
            "    </tbody>\n"
            "  </table>\n"
            "  <h2>Schema Validation Errors</h2>\n"
            f"  <ul>{schema_items}</ul>\n"
            "  <h2>Expectation Failures</h2>\n"
            f"  <ul>{expectation_items}</ul>\n"
            "  <h2>Performance Metrics</h2>\n"
            "  <table>\n"
            f"    <tbody>{html_performance_rows(self.performance_metrics)}</tbody>\n"
            "  </table>\n"
            f"  {html_source_performance(self.performance_metrics)}"
            "</body>\n"
            "</html>\n"
        )


@dataclass
class PipelineResult:
    refined: pd.DataFrame
    quality_report: QualityReport
    performance_metrics: dict[str, Any]
    compliance_report: dict[str, Any] | None = None
    party_store: PartyStore | None = None
    linkage: LinkageResult | None = None


YEAR_FIRST_PATTERN = re.compile(r"^\s*\d{4}")


def _flatten_series_of_lists(series: pd.Series) -> list[str]:
    items: list[str] = []
    for value in series.dropna():
        if isinstance(value, list):
            for element in value:
                cleaned = clean_string(element)
                if cleaned:
                    items.append(cleaned)
        else:
            cleaned = clean_string(value)
            if cleaned:
                items.append(cleaned)
    return collect_unique(items)


def _latest_iso_date(values: Iterable[str | None]) -> str | None:
    candidates: list[object] = []
    for value in values:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            continue
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                continue
            candidates.append(stripped)
        else:
            candidates.append(value)

    if not candidates:
        return None

    parsed: list[pd.Timestamp] = []
    for candidate in candidates:
        if isinstance(candidate, pd.Timestamp):
            timestamp = pd.to_datetime(candidate, utc=True)
        else:
            text = str(candidate)
            prefer_dayfirst = not YEAR_FIRST_PATTERN.match(text)
            timestamp = pd.to_datetime(
                text,
                errors="coerce",
                dayfirst=prefer_dayfirst,
                utc=True,
            )
            if pd.isna(timestamp):
                timestamp = pd.to_datetime(
                    text,
                    errors="coerce",
                    dayfirst=not prefer_dayfirst,
                    utc=True,
                )
        if pd.notna(timestamp):
            parsed.append(timestamp)

    if not parsed:
        return None

    latest = max(parsed)
    if pd.isna(latest):
        return None
    return latest.date().isoformat()


def _summarise_quality(row: dict[str, str | None]) -> dict[str, object]:
    checks = {
        "contact_email": bool(row.get("contact_primary_email")),
        "contact_phone": bool(row.get("contact_primary_phone")),
        "website": bool(row.get("website")),
        "province": bool(row.get("province")),
        "address": bool(row.get("address_primary")),
    }
    score = sum(1 for flag in checks.values() if flag) / max(len(checks), 1)
    missing_flags = [f"missing_{name}" for name, present in checks.items() if not present]
    return {
        "score": round(score, 2),
        "flags": ";".join(missing_flags) if missing_flags else "none",
    }


def _aggregate_group(slug: str, group: pd.DataFrame) -> dict[str, object | None]:
    organization_name = coalesce(*group["organization_name"].tolist())
    group = group.reset_index(drop=True)

    row_metadata: list[RowMetadata] = []
    for idx, row in group.iterrows():
        raw_dataset = row.get("source_dataset")
        dataset = clean_string(raw_dataset)
        if not dataset:
            dataset = str(raw_dataset).strip() if raw_dataset else "Unknown"
        record_id = clean_string(row.get("source_record_id"))
        priority = SOURCE_PRIORITY.get(dataset, 0)
        last_interaction = _parse_last_interaction(row.get("last_interaction_date"))
        quality_score = _row_quality_score(row)
        row_metadata.append(
            RowMetadata(
                index=idx,
                source_dataset=dataset,
                source_record_id=record_id,
                source_priority=priority,
                quality_score=quality_score,
                last_interaction=last_interaction,
            )
        )

    def _sort_key(meta: RowMetadata) -> tuple[Any, ...]:
        timestamp_value = (
            meta.last_interaction.value
            if meta.last_interaction is not None
            else pd.Timestamp.min.value
        )
        return (
            meta.source_priority,
            meta.quality_score,
            timestamp_value,
            -meta.index,
            meta.source_record_id or "",
        )

    sorted_indices = sorted(
        range(len(row_metadata)),
        key=lambda idx: _sort_key(row_metadata[idx]),
        reverse=True,
    )

    provenance: dict[str, dict[str, Any]] = {}
    conflicts: list[dict[str, Any]] = []  # Track conflicts for reporting

    def _normalise_scalar(value: object | None) -> str | None:
        if isinstance(value, str):
            return clean_string(value)
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        return clean_string(str(value))

    def _iter_values(column: str, treat_list: bool = False) -> list[ValueSelection]:
        selections: list[ValueSelection] = []
        seen: set[str] = set()
        for idx in sorted_indices:
            row = group.iloc[idx]
            raw_value = row.get(column)
            values: Iterable[object | None]
            if treat_list and isinstance(raw_value, list):
                values = raw_value
            else:
                values = [raw_value]
            for raw in values:
                normalised = _normalise_scalar(raw)
                if not normalised:
                    continue
                if normalised in seen:
                    continue
                seen.add(normalised)
                selections.append(ValueSelection(normalised, row_metadata[idx]))
        return selections

    def _build_provenance(
        field: str, selection: ValueSelection, value: str | None
    ) -> dict[str, Any]:
        meta = selection.row_metadata
        return {
            "field": field,
            "value": value,
            "source_dataset": meta.source_dataset,
            "source_record_id": meta.source_record_id,
            "source_priority": meta.source_priority,
            "quality_score": meta.quality_score,
            "last_interaction_date": (
                meta.last_interaction.date().isoformat()
                if meta.last_interaction is not None
                else None
            ),
        }

    def _record_provenance(
        field: str, selections: list[ValueSelection], value: str | None
    ) -> ValueSelection | None:
        if not selections:
            return None
        primary_selection = next((sel for sel in selections if sel.value == value), selections[0])
        entry = _build_provenance(field, primary_selection, value)
        contributors = [sel for sel in selections if sel is not primary_selection]
        if contributors:
            entry["contributors"] = [
                {
                    "source_dataset": sel.row_metadata.source_dataset,
                    "source_record_id": sel.row_metadata.source_record_id,
                    "value": sel.value,
                }
                for sel in contributors
            ]
            # Track as conflict for reporting
            conflicts.append(
                {
                    "field": field,
                    "chosen_source": primary_selection.row_metadata.source_dataset,
                    "value": value,
                    "alternatives": [
                        {
                            "source": sel.row_metadata.source_dataset,
                            "value": sel.value,
                        }
                        for sel in contributors
                    ],
                }
            )
        provenance[field] = entry
        return primary_selection

    provinces = _iter_values("province")
    areas = _iter_values("area")
    addresses = _iter_values("address")
    categories = _iter_values("category")
    org_types = _iter_values("organization_type")
    statuses = _iter_values("status")
    websites = _iter_values("website")
    planes = _iter_values("planes")
    descriptions = _iter_values("description")
    notes = _iter_values("notes")
    priorities = _iter_values("priority")

    email_values = _iter_values("contact_emails", treat_list=True)
    phone_values = _iter_values("contact_phones", treat_list=True)
    name_values = _iter_values("contact_names", treat_list=True)
    role_values = _iter_values("contact_roles", treat_list=True)

    source_datasets = "; ".join(sorted(collect_unique(group["source_dataset"].tolist())))
    source_record_ids = "; ".join(sorted(collect_unique(group["source_record_id"].tolist())))

    province = provinces[0].value if provinces else None
    _record_provenance("province", provinces, province)

    area = areas[0].value if areas else None
    _record_provenance("area", areas, area)

    address_primary = addresses[0].value if addresses else None
    _record_provenance("address_primary", addresses, address_primary)

    organization_category = categories[0].value if categories else None
    _record_provenance("organization_category", categories, organization_category)

    organization_type = org_types[0].value if org_types else None
    _record_provenance("organization_type", org_types, organization_type)

    status = statuses[0].value if statuses else None
    _record_provenance("status", statuses, status)

    website = websites[0].value if websites else None
    _record_provenance("website", websites, website)

    planes_value = "; ".join(selection.value for selection in planes) if planes else None
    if planes_value:
        _record_provenance("planes", planes, planes_value)

    description_value = (
        "; ".join(selection.value for selection in descriptions) if descriptions else None
    )
    if description_value:
        _record_provenance("description", descriptions, description_value)

    notes_value = "; ".join(selection.value for selection in notes) if notes else None
    if notes_value:
        _record_provenance("notes", notes, notes_value)

    priority_value = priorities[0].value if priorities else None
    _record_provenance("priority", priorities, priority_value)

    primary_email_selection = _record_provenance(
        "contact_primary_email",
        email_values,
        email_values[0].value if email_values else None,
    )
    primary_email = primary_email_selection.value if primary_email_selection else None
    secondary_email_values = email_values[1:]
    secondary_emails = ";".join(selection.value for selection in secondary_email_values)
    if secondary_emails:
        _record_provenance("contact_secondary_emails", secondary_email_values, secondary_emails)

    primary_phone_selection = _record_provenance(
        "contact_primary_phone",
        phone_values,
        phone_values[0].value if phone_values else None,
    )
    primary_phone = primary_phone_selection.value if primary_phone_selection else None
    secondary_phone_values = phone_values[1:]
    secondary_phones = ";".join(selection.value for selection in secondary_phone_values)
    if secondary_phones:
        _record_provenance("contact_secondary_phones", secondary_phone_values, secondary_phones)

    def _first_value_from_row(selection: ValueSelection | None, column: str) -> str | None:
        if selection is None:
            return None
        row = group.iloc[selection.row_metadata.index]
        raw_value = row.get(column)
        if isinstance(raw_value, list):
            for item in raw_value:
                candidate = _normalise_scalar(item)
                if candidate:
                    return candidate
            return None
        return _normalise_scalar(raw_value)

    primary_contact_meta = primary_email_selection or primary_phone_selection
    primary_name = _first_value_from_row(primary_contact_meta, "contact_names")
    if primary_name:
        _record_provenance("contact_primary_name", name_values, primary_name)
    else:
        primary_name = name_values[0].value if name_values else None
        if primary_name:
            _record_provenance("contact_primary_name", name_values, primary_name)

    primary_role = _first_value_from_row(primary_contact_meta, "contact_roles")
    if primary_role:
        _record_provenance("contact_primary_role", role_values, primary_role)
    else:
        primary_role = role_values[0].value if role_values else None
        if primary_role:
            _record_provenance("contact_primary_role", role_values, primary_role)

    last_interaction = _latest_iso_date(group["last_interaction_date"].tolist())

    quality = _summarise_quality(
        {
            "contact_primary_email": primary_email,
            "contact_primary_phone": primary_phone,
            "website": website,
            "province": province,
            "address_primary": address_primary,
        }
    )

    selection_provenance = json.dumps(provenance, sort_keys=True)

    result = {
        "organization_name": organization_name,
        "organization_slug": slug,
        "province": province,
        "country": "South Africa",
        "area": area,
        "address_primary": address_primary,
        "organization_category": organization_category,
        "organization_type": organization_type,
        "status": status,
        "website": website,
        "planes": planes_value,
        "description": description_value,
        "notes": notes_value,
        "source_datasets": source_datasets,
        "source_record_ids": source_record_ids,
        "contact_primary_name": primary_name,
        "contact_primary_role": primary_role,
        "contact_primary_email": primary_email,
        "contact_primary_phone": primary_phone,
        "contact_secondary_emails": secondary_emails,
        "contact_secondary_phones": secondary_phones,
        "data_quality_score": quality["score"],
        "data_quality_flags": quality["flags"],
        "selection_provenance": selection_provenance,
        "last_interaction_date": last_interaction,
        "priority": priority_value,
        "privacy_basis": "Legitimate Interest",
        "_conflicts": conflicts,  # Internal field for conflict tracking
    }
    return result


def _load_sources(config: PipelineConfig) -> tuple[pd.DataFrame, dict[str, float]]:
    loaders = [load_reachout_database, load_contact_database, load_sacaa_cleaned]
    frames: list[pd.DataFrame] = []
    timings: dict[str, float] = {}
    for loader in loaders:
        start = time.perf_counter()
        try:
            frame = loader(config.input_dir, config.country_code, config.excel_options)
        except FileNotFoundError:
            timings[loader.__name__] = time.perf_counter() - start
            continue
        except (
            OSError,
            ValueError,
        ) as exc:  # pragma: no cover - defensive logging hook
            raise RuntimeError(f"Failed to load source via {loader.__name__}: {exc}") from exc
        duration = time.perf_counter() - start
        timings[loader.__name__] = duration
        if not frame.empty:
            frames.append(frame)
    if not frames:
        empty = pd.DataFrame(
            columns=[
                "organization_name",
                "source_dataset",
                "source_record_id",
                "province",
                "area",
                "address",
                "category",
                "organization_type",
                "status",
                "website",
                "planes",
                "description",
                "notes",
                "last_interaction_date",
                "priority",
                "contact_names",
                "contact_roles",
                "contact_emails",
                "contact_phones",
            ]
        )
        return empty, timings
    combined = pd.concat(frames, ignore_index=True, sort=False)
    combined["organization_slug"] = combined["organization_name"].apply(slugify)
    combined["province"] = combined["province"].apply(normalize_province)
    return combined, timings


def run_pipeline(config: PipelineConfig) -> PipelineResult:
    # Initialize profile if not provided
    if config.industry_profile is None:
        config.industry_profile = get_default_profile("generic")

    # Initialize output format if not provided
    if config.output_format is None:
        config.output_format = OutputFormat()

    pipeline_start = time.perf_counter()
    audit_trail: list[dict[str, Any]] = []

    _notify_progress(
        config,
        PIPELINE_EVENT_START,
        input_dir=str(config.input_dir),
        output_path=str(config.output_path),
    )

    # Log pipeline start
    if config.enable_audit_trail:
        audit_trail.append(
            {
                "timestamp": time.time(),
                "event": "pipeline_start",
                "details": {
                    "input_dir": str(config.input_dir),
                    "output_path": str(config.output_path),
                    "profile": (
                        config.industry_profile.name if config.industry_profile else "default"
                    ),
                },
            }
        )

    logger.info(
        "Starting pipeline execution",
        extra={
            "profile": (config.industry_profile.name if config.industry_profile else "default"),
            "input_dir": str(config.input_dir),
        },
    )

    _notify_progress(config, PIPELINE_EVENT_LOAD_STARTED)
    load_start = time.perf_counter()
    combined, source_timings = _load_sources(config)
    load_seconds = time.perf_counter() - load_start

    _notify_progress(
        config,
        PIPELINE_EVENT_LOAD_COMPLETED,
        total_rows=len(combined),
        sources=list(source_timings.keys()),
        load_seconds=load_seconds,
    )

    if config.enable_audit_trail:
        audit_trail.append(
            {
                "timestamp": time.time(),
                "event": "sources_loaded",
                "details": {
                    "total_rows": len(combined),
                    "load_seconds": load_seconds,
                    "sources": list(source_timings.keys()),
                },
            }
        )

    logger.info(
        f"Loaded {len(combined)} rows from {len(source_timings)} sources in {load_seconds:.2f}s"
    )

    metrics: dict[str, Any] = {
        "load_seconds": load_seconds,
        "aggregation_seconds": 0.0,
        "expectations_seconds": 0.0,
        "write_seconds": 0.0,
        "total_seconds": 0.0,
        "rows_per_second": 0.0,
        "load_rows_per_second": 0.0,
        "source_load_seconds": source_timings,
    }
    if load_seconds > 0:
        metrics["load_rows_per_second"] = len(combined) / load_seconds if len(combined) else 0.0

    if combined.empty:
        refined = pd.DataFrame(columns=SSOT_COLUMNS)
        config.output_path.parent.mkdir(parents=True, exist_ok=True)
        _notify_progress(config, PIPELINE_EVENT_AGGREGATE_STARTED, total=0)
        _notify_progress(
            config,
            PIPELINE_EVENT_AGGREGATE_COMPLETED,
            total=0,
            aggregated_records=0,
            conflicts=0,
        )
        _notify_progress(config, PIPELINE_EVENT_WRITE_STARTED, path=str(config.output_path))
        write_start = time.perf_counter()
        refined.to_excel(config.output_path, index=False)
        write_seconds = time.perf_counter() - write_start
        metrics.update(
            aggregation_seconds=0.0,
            expectations_seconds=0.0,
            write_seconds=write_seconds,
            total_seconds=time.perf_counter() - pipeline_start,
            rows_per_second=0.0,
        )
        _notify_progress(
            config,
            PIPELINE_EVENT_WRITE_COMPLETED,
            path=str(config.output_path),
            write_seconds=write_seconds,
        )
        metrics_copy = dict(metrics)
        report = QualityReport(
            total_records=0,
            invalid_records=0,
            schema_validation_errors=[],
            expectations_passed=True,
            expectation_failures=[],
            source_breakdown={},
            data_quality_distribution={"mean": 0.0, "min": 0.0, "max": 0.0},
            performance_metrics=metrics_copy,
            recommendations=["No data loaded. Check input directory and source files."],
            audit_trail=audit_trail,
            conflict_resolutions=[],
        )
        _notify_progress(
            config,
            PIPELINE_EVENT_COMPLETED,
            total_records=0,
            invalid_records=0,
            duration=metrics_copy["total_seconds"],
        )
        return PipelineResult(
            refined=refined,
            quality_report=report,
            performance_metrics=metrics_copy,
            # In the early-return path (no data loaded), the party store is empty by definition.
            party_store=PartyStore(),
        )

    aggregated_rows = []
    all_conflicts: list[dict[str, Any]] = []
    aggregation_start = time.perf_counter()
    group_total = int(combined["organization_slug"].nunique(dropna=False))
    _notify_progress(config, PIPELINE_EVENT_AGGREGATE_STARTED, total=group_total)

    for index, (slug, group) in enumerate(
        combined.groupby("organization_slug", dropna=False),
        start=1,
    ):
        row_dict = _aggregate_group(slug, group)
        # Extract and accumulate conflicts
        conflicts_obj = row_dict.pop("_conflicts", [])
        if isinstance(conflicts_obj, list):
            all_conflicts.extend(conflicts_obj)
        aggregated_rows.append(row_dict)
        if group_total > 0:
            if index == group_total or index % max(group_total // 10, 1) == 0:
                _notify_progress(
                    config,
                    PIPELINE_EVENT_AGGREGATE_PROGRESS,
                    completed=index,
                    total=group_total,
                    slug=str(slug),
                )

    refined_df = pd.DataFrame(aggregated_rows, columns=SSOT_COLUMNS)
    refined_df = refined_df.sort_values("organization_name").reset_index(drop=True)
    metrics["aggregation_seconds"] = time.perf_counter() - aggregation_start
    _notify_progress(
        config,
        PIPELINE_EVENT_AGGREGATE_COMPLETED,
        total=group_total,
        aggregated_records=len(refined_df),
        conflicts=len(all_conflicts),
    )

    if config.enable_audit_trail:
        audit_trail.append(
            {
                "timestamp": time.time(),
                "event": "aggregation_complete",
                "details": {
                    "aggregated_records": len(refined_df),
                    "conflicts_resolved": len(all_conflicts),
                    "aggregation_seconds": metrics["aggregation_seconds"],
                },
            }
        )

    logger.info(
        f"Aggregated {len(refined_df)} records with {len(all_conflicts)} conflict resolutions"
    )

    schema = build_ssot_schema()
    schema_errors: list[str] = []
    validated_df = refined_df
    _notify_progress(
        config,
        PIPELINE_EVENT_SCHEMA_STARTED,
        total_records=len(refined_df),
    )
    try:
        validated_df = schema.validate(refined_df, lazy=True)
        logger.info("Schema validation passed")
    except SchemaErrors as exc:
        schema_errors = [
            f"{row['column']}: {row['failure_case']}" for _, row in exc.failure_cases.iterrows()
        ]
        invalid_indices = exc.failure_cases["index"].unique().tolist()
        valid_indices = [idx for idx in refined_df.index if idx not in invalid_indices]

        # Check if all records failed validation
        if not valid_indices:
            logger.error(
                f"All {len(refined_df)} records failed schema validation. "
                "Writing unvalidated data with quality flags."
            )
            # Use the original refined_df instead of an empty dataframe
            validated_df = refined_df
            schema_errors.append(
                f"CRITICAL: All {len(refined_df)} records failed schema validation. "
                "Output contains unvalidated data."
            )
        else:
            validated_df = schema.validate(refined_df.loc[valid_indices], lazy=False)
            logger.warning(
                f"Schema validation found {len(schema_errors)} errors",
                extra={
                    "error_count": len(schema_errors),
                    "invalid_records": len(invalid_indices),
                },
            )

        if config.enable_audit_trail:
            audit_trail.append(
                {
                    "timestamp": time.time(),
                    "event": "schema_validation_errors",
                    "details": {
                        "error_count": len(schema_errors),
                        "invalid_records": len(invalid_indices),
                        "all_records_invalid": not bool(valid_indices),
                    },
                }
            )

    # Additional safeguard: if validated_df is empty after schema validation,
    # but refined_df had data, write the original refined_df instead
    if len(validated_df) == 0 and len(refined_df) > 0:
        logger.error(
            f"Schema validation resulted in empty output despite {len(refined_df)} input records. "
            "Writing original data to prevent data loss."
        )
        validated_df = refined_df
        if "CRITICAL: Schema validation resulted in complete data loss" not in schema_errors:
            schema_errors.append(
                f"CRITICAL: Schema validation resulted in complete data loss. "
                f"All {len(refined_df)} records would have been filtered out. "
                "Writing original data to prevent empty output file."
            )

    _notify_progress(
        config,
        PIPELINE_EVENT_SCHEMA_COMPLETED,
        errors=len(schema_errors),
    )

    expectation_start = time.perf_counter()
    # Use profile thresholds if available
    profile = config.industry_profile
    email_threshold = profile.email_validation_threshold if profile else 0.85
    phone_threshold = profile.phone_validation_threshold if profile else 0.85
    website_threshold = profile.website_validation_threshold if profile else 0.85

    _notify_progress(
        config,
        PIPELINE_EVENT_EXPECTATIONS_STARTED,
        total_records=len(validated_df),
    )

    expectation_summary: ExpectationSummary = run_expectations(
        validated_df,
        email_mostly=email_threshold,
        phone_mostly=phone_threshold,
        website_mostly=website_threshold,
    )
    metrics["expectations_seconds"] = time.perf_counter() - expectation_start

    logger.info(f"Expectations validation: {'PASSED' if expectation_summary.success else 'FAILED'}")

    _notify_progress(
        config,
        PIPELINE_EVENT_EXPECTATIONS_COMPLETED,
        success=expectation_summary.success,
        failure_count=len(expectation_summary.failures),
    )

    source_breakdown = combined["source_dataset"].value_counts().to_dict()

    polars_validated = pl.from_pandas(validated_df, include_index=False)
    parquet_path = config.output_path.with_suffix(".parquet")
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    polars_validated.write_parquet(parquet_path)
    metrics["parquet_path"] = str(parquet_path)

    if polars_validated.height > 0:
        stats = polars_validated.select(
            pl.col("data_quality_score").mean().alias("mean"),
            pl.col("data_quality_score").min().alias("min"),
            pl.col("data_quality_score").max().alias("max"),
        ).to_dicts()[0]
        quality_distribution = {key: float(value) for key, value in stats.items()}
    else:
        quality_distribution = {"mean": 0.0, "min": 0.0, "max": 0.0}

    with duckdb.connect() as conn:
        ordered_df = conn.execute(
            "SELECT * FROM read_parquet(?) ORDER BY organization_name",
            [str(parquet_path)],
        ).fetch_df()
    validated_df = ordered_df
    pl.from_pandas(validated_df, include_index=False).write_parquet(parquet_path)

    # Generate recommendations if enabled
    recommendations = []
    if config.enable_recommendations:
        recommendations = generate_recommendations(
            validated_df, expectation_summary, quality_distribution
        )
        logger.info(f"Generated {len(recommendations)} recommendations")

    party_store = build_party_store_from_refined(
        validated_df,
        default_country=config.country_code,
        execution_time=datetime.now(tz=UTC),
    )

    config.output_path.parent.mkdir(parents=True, exist_ok=True)
    _notify_progress(config, PIPELINE_EVENT_WRITE_STARTED, path=str(config.output_path))
    write_start = time.perf_counter()

    # Use formatting if enabled
    suffix = config.output_path.suffix.lower()

    if config.enable_formatting and suffix in [".xlsx", ".xls"]:
        logger.info("Writing output with enhanced formatting")
        with pd.ExcelWriter(config.output_path, engine="openpyxl") as writer:
            validated_df.to_excel(writer, sheet_name="Data", index=False)
            apply_excel_formatting(writer, "Data", validated_df, config.output_format)

            # Add summary sheet
            quality_report_dict = {
                "total_records": len(refined_df),
                "invalid_records": len(refined_df) - len(validated_df),
                "expectations_passed": expectation_summary.success,
            }
            summary_df = create_summary_sheet(validated_df, quality_report_dict)
            summary_df.to_excel(writer, sheet_name="Summary", index=False, header=False)
    elif suffix == ".csv":
        validated_df.to_csv(config.output_path, index=False)
        _write_csvw_metadata(config.output_path)
    elif suffix == ".parquet":
        # Snapshot already written via Polars, ensure DuckDB ordering persisted.
        pl.from_pandas(validated_df, include_index=False).write_parquet(config.output_path)
    else:
        validated_df.to_excel(config.output_path, index=False)

    metrics["write_seconds"] = time.perf_counter() - write_start
    metrics["total_seconds"] = time.perf_counter() - pipeline_start
    if metrics["total_seconds"] > 0:
        metrics["rows_per_second"] = len(validated_df) / metrics["total_seconds"]

    _notify_progress(
        config,
        PIPELINE_EVENT_WRITE_COMPLETED,
        path=str(config.output_path),
        write_seconds=metrics["write_seconds"],
    )

    if config.enable_audit_trail:
        audit_trail.append(
            {
                "timestamp": time.time(),
                "event": "pipeline_complete",
                "details": {
                    "total_seconds": metrics["total_seconds"],
                    "output_path": str(config.output_path),
                },
            }
        )

    logger.info(f"Pipeline completed in {metrics['total_seconds']:.2f}s")

    metrics_copy = dict(metrics)
    report = QualityReport(
        total_records=int(len(refined_df)),
        invalid_records=int(len(refined_df) - len(validated_df)),
        schema_validation_errors=schema_errors,
        expectations_passed=expectation_summary.success,
        expectation_failures=expectation_summary.failures,
        source_breakdown=source_breakdown,
        data_quality_distribution=quality_distribution,
        performance_metrics=metrics_copy,
        recommendations=recommendations,
        audit_trail=audit_trail,
        conflict_resolutions=all_conflicts,
    )

    _notify_progress(
        config,
        PIPELINE_EVENT_COMPLETED,
        total_records=report.total_records,
        invalid_records=report.invalid_records,
        duration=metrics_copy["total_seconds"],
    )

    return PipelineResult(
        refined=validated_df,
        quality_report=report,
        performance_metrics=metrics_copy,
        party_store=party_store,
    )


def _notify_progress(config: PipelineConfig, event: str, **payload: Any) -> None:
    listener = config.progress_listener
    if listener is not None:
        listener(event, payload)
