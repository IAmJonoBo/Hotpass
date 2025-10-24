"""Pipeline orchestration for producing the Hotpass SSOT workbook."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from pandera.errors import SchemaErrors

from .data_sources import (
    load_contact_database,
    load_reachout_database,
    load_sacaa_cleaned,
)
from .normalization import clean_string, coalesce, normalize_province, slugify
from .quality import ExpectationSummary, build_ssot_schema, run_expectations

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


@dataclass
class QualityReport:
    total_records: int
    invalid_records: int
    schema_validation_errors: list[str]
    expectations_passed: bool
    expectation_failures: list[str]
    source_breakdown: dict[str, int]
    data_quality_distribution: dict[str, float]


@dataclass
class PipelineResult:
    refined: pd.DataFrame
    quality_report: QualityReport


YEAR_FIRST_PATTERN = re.compile(r"^\s*\d{4}")


def _collect_unique(values: Iterable[str | None]) -> list[str]:
    unique: list[str] = []
    for value in values:
        cleaned = clean_string(value)
        if cleaned and cleaned not in unique:
            unique.append(cleaned)
    return unique


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
    return _collect_unique(items)


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
        if not selections or value is None:
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

    source_datasets = "; ".join(sorted(_collect_unique(group["source_dataset"].tolist())))
    source_record_ids = "; ".join(sorted(_collect_unique(group["source_record_id"].tolist())))

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
        "contact_primary_email", email_values, email_values[0].value if email_values else None
    )
    primary_email = primary_email_selection.value if primary_email_selection else None
    secondary_email_values = email_values[1:]
    secondary_emails = ";".join(selection.value for selection in secondary_email_values)
    if secondary_emails:
        _record_provenance("contact_secondary_emails", secondary_email_values, secondary_emails)

    primary_phone_selection = _record_provenance(
        "contact_primary_phone", phone_values, phone_values[0].value if phone_values else None
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

    return {
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
    }


def _load_sources(config: PipelineConfig) -> pd.DataFrame:
    loaders = [load_reachout_database, load_contact_database, load_sacaa_cleaned]
    frames: list[pd.DataFrame] = []
    for loader in loaders:
        try:
            frame = loader(config.input_dir, config.country_code)
        except FileNotFoundError:
            continue
        except (OSError, ValueError) as exc:  # pragma: no cover - defensive logging hook
            raise RuntimeError(f"Failed to load source via {loader.__name__}: {exc}") from exc
        if not frame.empty:
            frames.append(frame)
    if not frames:
        return pd.DataFrame(
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
    combined = pd.concat(frames, ignore_index=True, sort=False)
    combined["organization_slug"] = combined["organization_name"].apply(slugify)
    combined["province"] = combined["province"].apply(normalize_province)
    return combined


def run_pipeline(config: PipelineConfig) -> PipelineResult:
    combined = _load_sources(config)
    if combined.empty:
        refined = pd.DataFrame(columns=SSOT_COLUMNS)
        report = QualityReport(
            total_records=0,
            invalid_records=0,
            schema_validation_errors=[],
            expectations_passed=True,
            expectation_failures=[],
            source_breakdown={},
            data_quality_distribution={"mean": 0.0, "min": 0.0, "max": 0.0},
        )
        config.output_path.parent.mkdir(parents=True, exist_ok=True)
        refined.to_excel(config.output_path, index=False)
        return PipelineResult(refined=refined, quality_report=report)

    aggregated_rows = []
    for slug, group in combined.groupby("organization_slug", dropna=False):
        aggregated_rows.append(_aggregate_group(slug, group))
    refined_df = pd.DataFrame(aggregated_rows, columns=SSOT_COLUMNS)
    refined_df = refined_df.sort_values("organization_name").reset_index(drop=True)

    schema = build_ssot_schema()
    schema_errors: list[str] = []
    validated_df = refined_df
    try:
        validated_df = schema.validate(refined_df, lazy=True)
    except SchemaErrors as exc:
        schema_errors = [
            f"{row['column']}: {row['failure_case']}" for _, row in exc.failure_cases.iterrows()
        ]
        invalid_indices = exc.failure_cases["index"].unique().tolist()
        valid_indices = [idx for idx in refined_df.index if idx not in invalid_indices]
        validated_df = schema.validate(refined_df.loc[valid_indices], lazy=False)

    expectation_summary: ExpectationSummary = run_expectations(validated_df)

    source_breakdown = combined["source_dataset"].value_counts().to_dict()
    quality_distribution = {
        "mean": float(validated_df["data_quality_score"].mean()),
        "min": float(validated_df["data_quality_score"].min()),
        "max": float(validated_df["data_quality_score"].max()),
    }

    report = QualityReport(
        total_records=int(len(refined_df)),
        invalid_records=int(len(refined_df) - len(validated_df)),
        schema_validation_errors=schema_errors,
        expectations_passed=expectation_summary.success,
        expectation_failures=expectation_summary.failures,
        source_breakdown=source_breakdown,
        data_quality_distribution=quality_distribution,
    )

    config.output_path.parent.mkdir(parents=True, exist_ok=True)
    validated_df.to_excel(config.output_path, index=False)

    return PipelineResult(refined=validated_df, quality_report=report)
