"""Validation helpers using Pandera and Great Expectations."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import pandera as pa
from pandera import Column, DataFrameSchema

try:
    from great_expectations.dataset.pandas_dataset import PandasDataset  # type: ignore
except ImportError:  # pragma: no cover - fallback for trimmed GE installations
    PandasDataset = None  # type: ignore[assignment]


@dataclass
class ExpectationSummary:
    success: bool
    failures: list[str]


def build_ssot_schema() -> DataFrameSchema:
    def string_col(nullable: bool = True) -> Column:
        return Column(pa.String, nullable=nullable)

    return DataFrameSchema(
        {
            "organization_name": Column(pa.String, nullable=False),
            "organization_slug": Column(pa.String, nullable=False),
            "province": string_col(),
            "country": Column(pa.String, nullable=False),
            "area": string_col(),
            "address_primary": string_col(),
            "organization_category": string_col(),
            "organization_type": string_col(),
            "status": string_col(),
            "website": string_col(),
            "planes": string_col(),
            "description": string_col(),
            "notes": string_col(),
            "source_datasets": Column(pa.String, nullable=False),
            "source_record_ids": Column(pa.String, nullable=False),
            "contact_primary_name": string_col(),
            "contact_primary_role": string_col(),
            "contact_primary_email": string_col(),
            "contact_primary_phone": string_col(),
            "contact_secondary_emails": string_col(),
            "contact_secondary_phones": string_col(),
            "data_quality_score": Column(pa.Float, nullable=False),
            "data_quality_flags": Column(pa.String, nullable=False),
            "last_interaction_date": string_col(),
            "priority": string_col(),
            "privacy_basis": Column(pa.String, nullable=False),
        },
        coerce=True,
        name="hotpass_ssot",
    )


def run_expectations(
    df: pd.DataFrame,
    *,
    email_mostly: float = 0.85,
    phone_mostly: float = 0.85,
    website_mostly: float = 0.85,
) -> ExpectationSummary:
    sanitized = df.copy()
    contact_columns = [
        "contact_primary_email",
        "contact_primary_phone",
        "website",
    ]
    for column in contact_columns:
        sanitized[column] = sanitized[column].replace(r"^\s*$", pd.NA, regex=True)

    failures: list[str] = []
    if PandasDataset is not None:
        dataset = PandasDataset(sanitized)
        dataset.set_default_expectation_argument("catch_exceptions", True)

        dataset.expect_column_values_to_not_be_null("organization_name")
        dataset.expect_column_values_to_not_be_null("organization_slug")
        dataset.expect_column_values_to_be_between(
            "data_quality_score", min_value=0.0, max_value=1.0, mostly=1.0
        )
        dataset.expect_column_values_to_match_regex(
            "contact_primary_email",
            r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
            mostly=email_mostly,
        )
        dataset.expect_column_values_to_match_regex(
            "contact_primary_phone",
            r"^\+\d{6,}$",
            mostly=phone_mostly,
        )
        dataset.expect_column_values_to_match_regex("website", r"^https?://", mostly=website_mostly)
        dataset.expect_column_values_to_be_in_set("country", {"South Africa"})

        validation = dataset.validate()
        for result in validation.results:
            if not result.success:
                expectation = result.expectation_config.expectation_type
                unexpected = result.result.get("unexpected_list")
                if unexpected:
                    sample = unexpected[:3]
                    failures.append(f"{expectation}: unexpected {sample}")
                else:
                    failures.append(expectation)
        return ExpectationSummary(success=validation.success, failures=failures)

    # Manual fallback when lightweight GE dataset API is unavailable.
    success = True

    def _record_failure(condition: bool, message: str) -> None:
        nonlocal success
        if not condition:
            success = False
            failures.append(message)

    _record_failure(sanitized["organization_name"].notna().all(), "organization_name nulls")
    _record_failure(sanitized["organization_slug"].notna().all(), "organization_slug nulls")
    _record_failure(
        sanitized["data_quality_score"].between(0.0, 1.0).all(),
        "data_quality_score bounds",
    )

    def _record_mostly(series: pd.Series, pattern: str, mostly: float, message: str) -> None:
        relevant = series.dropna()
        if relevant.empty:
            return
        matches = relevant.astype(str).str.match(pattern)
        success_ratio = float(matches.mean())
        if success_ratio >= mostly:
            return
        _record_failure(
            False,
            f"{message} success_rate={success_ratio:.0%} threshold={mostly:.0%}",
        )

    _record_mostly(
        sanitized["contact_primary_email"],
        r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        email_mostly,
        "contact_primary_email format",
    )
    _record_mostly(
        sanitized["contact_primary_phone"],
        r"^\+\d{6,}$",
        phone_mostly,
        "contact_primary_phone format",
    )
    _record_mostly(sanitized["website"], r"^https?://", website_mostly, "website scheme")

    _record_failure((sanitized["country"] == "South Africa").all(), "country constraint")

    return ExpectationSummary(success=success, failures=failures)
