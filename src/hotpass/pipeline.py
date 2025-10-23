"""Pipeline orchestration for producing the Hotpass SSOT workbook."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

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
    "last_interaction_date",
    "priority",
    "privacy_basis",
]


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
    provinces = _collect_unique(group["province"].tolist())
    areas = _collect_unique(group["area"].tolist())
    addresses = _collect_unique(group["address"].tolist())
    categories = _collect_unique(group["category"].tolist())
    org_types = _collect_unique(group["organization_type"].tolist())
    statuses = _collect_unique(group.get("status", []).tolist())
    websites = _collect_unique(group["website"].tolist())
    planes = _collect_unique(group["planes"].tolist())
    descriptions = _collect_unique(group["description"].tolist())
    notes = _collect_unique(group["notes"].tolist())
    priorities = _collect_unique(group["priority"].tolist())

    contact_names = _flatten_series_of_lists(group["contact_names"])
    contact_roles = _flatten_series_of_lists(group["contact_roles"])
    contact_emails = _flatten_series_of_lists(group["contact_emails"])
    contact_phones = _flatten_series_of_lists(group["contact_phones"])

    source_datasets = "; ".join(sorted(_collect_unique(group["source_dataset"].tolist())))
    source_record_ids = "; ".join(sorted(_collect_unique(group["source_record_id"].tolist())))

    primary_name = contact_names[0] if contact_names else None
    primary_role = contact_roles[0] if contact_roles else None
    primary_email = contact_emails[0] if contact_emails else None
    primary_phone = contact_phones[0] if contact_phones else None

    secondary_emails = ";".join(contact_emails[1:]) if len(contact_emails) > 1 else ""
    secondary_phones = ";".join(contact_phones[1:]) if len(contact_phones) > 1 else ""

    last_interaction = _latest_iso_date(group["last_interaction_date"].tolist())

    quality = _summarise_quality(
        {
            "contact_primary_email": primary_email,
            "contact_primary_phone": primary_phone,
            "website": websites[0] if websites else None,
            "province": provinces[0] if provinces else None,
            "address_primary": addresses[0] if addresses else None,
        }
    )

    return {
        "organization_name": organization_name,
        "organization_slug": slug,
        "province": provinces[0] if provinces else None,
        "country": "South Africa",
        "area": areas[0] if areas else None,
        "address_primary": addresses[0] if addresses else None,
        "organization_category": categories[0] if categories else None,
        "organization_type": org_types[0] if org_types else None,
        "status": statuses[0] if statuses else None,
        "website": websites[0] if websites else None,
        "planes": "; ".join(planes) if planes else None,
        "description": "; ".join(descriptions) if descriptions else None,
        "notes": "; ".join(notes) if notes else None,
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
        "last_interaction_date": last_interaction,
        "priority": priorities[0] if priorities else None,
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
        except Exception as exc:  # pragma: no cover - defensive logging hook
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
