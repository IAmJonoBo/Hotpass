"""Validation helpers using Pandera and Great Expectations."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import pandera as pa
from pandera import Column, DataFrameSchema

try:
    from great_expectations.dataset.pandas_dataset import PandasDataset  # type: ignore
except Exception:  # pragma: no cover - fallback for trimmed GE installations
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


def run_expectations(df: pd.DataFrame) -> ExpectationSummary:
    failures: list[str] = []
    if PandasDataset is not None:
        dataset = PandasDataset(df.copy())
        dataset.set_default_expectation_argument("catch_exceptions", True)

        dataset.expect_column_values_to_not_be_null("organization_name")
        dataset.expect_column_values_to_not_be_null("organization_slug")
        dataset.expect_column_values_to_be_between(
            "data_quality_score", min_value=0.0, max_value=1.0, mostly=1.0
        )
        dataset.expect_column_values_to_match_regex(
            "contact_primary_email", r"^[^@\s]+@[^@\s]+\.[^@\s]+$", mostly=0.85
        )
        dataset.expect_column_values_to_match_regex(
            "contact_primary_phone", r"^\+\d{6,}$", mostly=0.85
        )
        dataset.expect_column_values_to_match_regex("website", r"^https?://", mostly=0.85)
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

    _record_failure(df["organization_name"].notna().all(), "organization_name nulls")
    _record_failure(df["organization_slug"].notna().all(), "organization_slug nulls")
    _record_failure(df["data_quality_score"].between(0.0, 1.0).all(), "data_quality_score bounds")

    email_series = df["contact_primary_email"].dropna()
    _record_failure(
        email_series.str.contains(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", regex=True).all(),
        "contact_primary_email format",
    )

    phone_series = df["contact_primary_phone"].dropna()
    _record_failure(phone_series.str.startswith("+").all(), "contact_primary_phone format")

    website_series = df["website"].dropna()
    _record_failure(website_series.str.startswith("http").all(), "website scheme")

    _record_failure((df["country"] == "South Africa").all(), "country constraint")

    return ExpectationSummary(success=success, failures=failures)
