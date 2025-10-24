"""Entity resolution using Splink for probabilistic matching.

This module provides fuzzy duplicate detection and entity resolution
capabilities to replace the heuristic deduplication approach.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# Try to import splink, but make it optional
try:
    from splink import DuckDBAPI, Linker

    SPLINK_AVAILABLE = True
except ImportError:
    logger.warning("Splink not available - entity resolution will use fallback method")
    SPLINK_AVAILABLE = False


def build_splink_settings() -> dict[str, Any]:
    """Build Splink settings for organization matching.

    Returns:
        Splink settings dictionary
    """
    return {
        "link_type": "dedupe_only",
        "blocking_rules_to_generate_predictions": [
            "l.organization_slug = r.organization_slug",
            "substr(l.organization_name, 1, 3) = substr(r.organization_name, 1, 3)",
        ],
        "comparisons": [
            {
                "output_column_name": "organization_name",
                "comparison_levels": [
                    {
                        "sql_condition": (
                            "organization_name_l IS NULL OR organization_name_r IS NULL"
                        ),
                        "label_for_charts": "Null",
                        "is_null_level": True,
                    },
                    {
                        "sql_condition": "organization_name_l = organization_name_r",
                        "label_for_charts": "Exact match",
                        "m_probability": 0.9,
                    },
                    {
                        "sql_condition": (
                            "levenshtein(organization_name_l, organization_name_r) <= 3"
                        ),
                        "label_for_charts": "Levenshtein <= 3",
                        "m_probability": 0.7,
                    },
                    {
                        "sql_condition": "ELSE",
                        "label_for_charts": "All other comparisons",
                        "m_probability": 0.1,
                    },
                ],
            },
            {
                "output_column_name": "province",
                "comparison_levels": [
                    {
                        "sql_condition": "province_l IS NULL OR province_r IS NULL",
                        "label_for_charts": "Null",
                        "is_null_level": True,
                    },
                    {
                        "sql_condition": "province_l = province_r",
                        "label_for_charts": "Exact match",
                        "m_probability": 0.8,
                    },
                    {
                        "sql_condition": "ELSE",
                        "label_for_charts": "All other comparisons",
                        "m_probability": 0.2,
                    },
                ],
            },
            {
                "output_column_name": "website",
                "comparison_levels": [
                    {
                        "sql_condition": "website_l IS NULL OR website_r IS NULL",
                        "label_for_charts": "Null",
                        "is_null_level": True,
                    },
                    {
                        "sql_condition": "website_l = website_r",
                        "label_for_charts": "Exact match",
                        "m_probability": 0.95,
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
                        "sql_condition": (
                            "contact_primary_email_l IS NULL OR contact_primary_email_r IS NULL"
                        ),
                        "label_for_charts": "Null",
                        "is_null_level": True,
                    },
                    {
                        "sql_condition": "contact_primary_email_l = contact_primary_email_r",
                        "label_for_charts": "Exact match",
                        "m_probability": 0.95,
                    },
                    {
                        "sql_condition": "ELSE",
                        "label_for_charts": "All other comparisons",
                        "m_probability": 0.05,
                    },
                ],
            },
        ],
        "retain_matching_columns": True,
        "retain_intermediate_calculation_columns": True,
    }


def resolve_entities_with_splink(
    df: pd.DataFrame,
    threshold: float = 0.75,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Resolve duplicate entities using Splink probabilistic matching.

    Args:
        df: DataFrame with potential duplicates
        threshold: Match probability threshold (0.0 to 1.0)

    Returns:
        Tuple of (deduplicated DataFrame, match pairs DataFrame)
    """
    if not SPLINK_AVAILABLE:
        logger.warning("Splink not available, using fallback deduplication")
        return resolve_entities_fallback(df, threshold)

    logger.info(f"Resolving entities with Splink (threshold={threshold})")

    # Initialize Splink
    db_api = DuckDBAPI()
    settings = build_splink_settings()

    # Create linker
    linker = Linker(df, settings, db_api)

    # Predict matches
    predictions = linker.predict(threshold_match_probability=threshold)
    predictions_df = predictions.as_pandas_dataframe()

    # Build clusters of matched records
    clusters = linker.cluster_pairwise_predictions_at_threshold(
        predictions, threshold_match_probability=threshold
    )
    clusters_df = clusters.as_pandas_dataframe()

    # Merge cluster information back to original dataframe
    df_with_clusters = df.merge(
        clusters_df[["unique_id", "cluster_id"]],
        left_index=True,
        right_on="unique_id",
        how="left",
    )

    # For records without a cluster, assign individual cluster IDs
    max_cluster_id = df_with_clusters["cluster_id"].max()
    if pd.isna(max_cluster_id):
        max_cluster_id = 0

    null_mask = df_with_clusters["cluster_id"].isna()
    df_with_clusters.loc[null_mask, "cluster_id"] = range(
        int(max_cluster_id) + 1, int(max_cluster_id) + 1 + null_mask.sum()
    )

    # Take the first record from each cluster as the canonical record
    deduplicated = df_with_clusters.groupby("cluster_id").first().reset_index(drop=True)

    logger.info(
        f"Entity resolution complete: {len(df)} → {len(deduplicated)} records "
        f"({len(df) - len(deduplicated)} duplicates removed)"
    )

    return deduplicated, predictions_df


def resolve_entities_fallback(
    df: pd.DataFrame,
    threshold: float = 0.75,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fallback entity resolution using simple rules when Splink is unavailable.

    Args:
        df: DataFrame with potential duplicates
        threshold: Unused in fallback mode

    Returns:
        Tuple of (deduplicated DataFrame, empty match pairs DataFrame)
    """
    logger.info("Using fallback entity resolution (exact matching on slug)")

    # Simple deduplication based on organization slug
    # Keep the first occurrence of each slug
    deduplicated = df.drop_duplicates(subset=["organization_slug"], keep="first")

    duplicates_removed = len(df) - len(deduplicated)
    logger.info(
        f"Fallback resolution complete: {len(df)} → {len(deduplicated)} records "
        f"({duplicates_removed} duplicates removed)"
    )

    # Return empty predictions dataframe
    predictions_df = pd.DataFrame()

    return deduplicated, predictions_df


def build_entity_registry(
    df: pd.DataFrame,
    history_file: str | None = None,
) -> pd.DataFrame:
    """Build canonical entity registry with history tracking.

    Args:
        df: Current deduplicated DataFrame
        history_file: Optional path to load historical entity data

    Returns:
        Entity registry DataFrame with history
    """
    # For now, just add registry metadata
    registry = df.copy()

    # Add registry fields
    registry["entity_id"] = range(1, len(registry) + 1)
    registry["first_seen"] = pd.Timestamp.now()
    registry["last_updated"] = pd.Timestamp.now()
    registry["name_variants"] = registry["organization_name"].apply(
        lambda x: [x] if pd.notna(x) else []
    )
    registry["status_history"] = registry["status"].apply(
        lambda x: ([{"status": x, "date": pd.Timestamp.now().isoformat()}] if pd.notna(x) else [])
    )

    # TODO: Load and merge with historical data if provided
    if history_file:
        logger.info(f"Loading entity history from {history_file}")
        # Implementation for merging with history would go here

    logger.info(f"Built entity registry with {len(registry)} entities")

    return registry


def calculate_completeness_score(row: pd.Series) -> float:
    """Calculate a completeness score for an entity record.

    Args:
        row: DataFrame row representing an entity

    Returns:
        Completeness score (0.0 to 1.0)
    """
    # List of important fields to check
    fields = [
        "organization_name",
        "province",
        "contact_primary_email",
        "contact_primary_phone",
        "website",
        "address_primary",
        "organization_category",
    ]

    # Count non-null, non-empty fields
    filled = sum(
        1 for field in fields if field in row and pd.notna(row[field]) and str(row[field]).strip()
    )

    return filled / len(fields) if fields else 0.0


def add_ml_priority_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Add ML-driven priority and completeness scores.

    Args:
        df: DataFrame to enhance with scores

    Returns:
        DataFrame with added score columns
    """
    # Calculate completeness
    df["completeness_score"] = df.apply(calculate_completeness_score, axis=1)

    # Priority score combines completeness with quality score
    df["priority_score"] = df["completeness_score"] * 0.5 + df["data_quality_score"] * 0.5

    logger.info(f"Added ML priority scores to {len(df)} records")

    return df
