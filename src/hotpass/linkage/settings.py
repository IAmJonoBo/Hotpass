"""Helpers to build Splink settings for Hotpass linkage."""

from __future__ import annotations

from typing import Any

from .blocking import default_blocking_rules


def build_splink_settings() -> dict[str, Any]:
    """Return a Splink settings dictionary tuned for Hotpass entities."""

    return {
        "link_type": "dedupe_only",
        "unique_id_column_name": "__linkage_id",
        "blocking_rules_to_generate_predictions": default_blocking_rules(),
        "comparisons": [
            {
                "output_column_name": "organization_name",
                "comparison_levels": [
                    {
                        "sql_condition": "linkage_name_l IS NULL OR linkage_name_r IS NULL",
                        "label_for_charts": "Null",
                        "is_null_level": True,
                    },
                    {
                        "sql_condition": "linkage_name_l = linkage_name_r",
                        "label_for_charts": "Exact match",
                        "m_probability": 0.97,
                    },
                    {
                        "sql_condition": (
                            "rapidfuzz_token_sort_ratio(linkage_name_l, linkage_name_r) >= 0.96"
                        ),
                        "label_for_charts": "Token sort >= 0.96",
                        "m_probability": 0.86,
                    },
                    {
                        "sql_condition": (
                            "rapidfuzz_token_set_ratio(linkage_name_l, linkage_name_r) >= 0.9"
                        ),
                        "label_for_charts": "Token set >= 0.90",
                        "m_probability": 0.75,
                    },
                    {
                        "sql_condition": "ELSE",
                        "label_for_charts": "All other comparisons",
                        "m_probability": 0.05,
                    },
                ],
            },
            {
                "output_column_name": "contact_primary_email",
                "comparison_levels": [
                    {
                        "sql_condition": "linkage_email_l IS NULL OR linkage_email_r IS NULL",
                        "label_for_charts": "Null",
                        "is_null_level": True,
                    },
                    {
                        "sql_condition": "linkage_email_l = linkage_email_r",
                        "label_for_charts": "Exact match",
                        "m_probability": 0.98,
                    },
                    {
                        "sql_condition": "ELSE",
                        "label_for_charts": "All other comparisons",
                        "m_probability": 0.01,
                    },
                ],
            },
            {
                "output_column_name": "contact_primary_phone",
                "comparison_levels": [
                    {
                        "sql_condition": "linkage_phone_l IS NULL OR linkage_phone_r IS NULL",
                        "label_for_charts": "Null",
                        "is_null_level": True,
                    },
                    {
                        "sql_condition": "linkage_phone_l = linkage_phone_r",
                        "label_for_charts": "Exact match",
                        "m_probability": 0.9,
                    },
                    {
                        "sql_condition": (
                            "rapidfuzz_partial_ratio(linkage_phone_l, linkage_phone_r) >= 0.95"
                        ),
                        "label_for_charts": "Partial >= 0.95",
                        "m_probability": 0.7,
                    },
                    {
                        "sql_condition": "ELSE",
                        "label_for_charts": "All other comparisons",
                        "m_probability": 0.05,
                    },
                ],
            },
            {
                "output_column_name": "province",
                "comparison_levels": [
                    {
                        "sql_condition": (
                            "linkage_province_l IS NULL OR linkage_province_r IS NULL"
                        ),
                        "label_for_charts": "Null",
                        "is_null_level": True,
                    },
                    {
                        "sql_condition": "linkage_province_l = linkage_province_r",
                        "label_for_charts": "Exact match",
                        "m_probability": 0.85,
                    },
                    {
                        "sql_condition": "ELSE",
                        "label_for_charts": "All other comparisons",
                        "m_probability": 0.15,
                    },
                ],
            },
            {
                "output_column_name": "website",
                "comparison_levels": [
                    {
                        "sql_condition": "linkage_website_l IS NULL OR linkage_website_r IS NULL",
                        "label_for_charts": "Null",
                        "is_null_level": True,
                    },
                    {
                        "sql_condition": "linkage_website_l = linkage_website_r",
                        "label_for_charts": "Exact match",
                        "m_probability": 0.96,
                    },
                    {
                        "sql_condition": "ELSE",
                        "label_for_charts": "All other comparisons",
                        "m_probability": 0.04,
                    },
                ],
            },
        ],
        "retain_matching_columns": False,
        "retain_intermediate_calculation_columns": False,
    }
