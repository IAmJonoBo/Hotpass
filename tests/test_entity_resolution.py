"""Tests for entity resolution module."""

import json

import pandas as pd
import pytest

pytest.importorskip("frictionless")

import hotpass.entity_resolution as entity_resolution  # noqa: E402
from hotpass.entity_resolution import (
    add_ml_priority_scores,
    build_entity_registry,
    calculate_completeness_score,
    resolve_entities_fallback,
)


@pytest.fixture
def sample_df_with_duplicates():
    """Create a sample DataFrame with duplicates."""
    return pd.DataFrame(
        {
            "organization_name": [
                "ABC Flight School",
                "ABC Flight School",  # Exact duplicate
                "XYZ Aviation",
                "xyz aviation",  # Case different
            ],
            "organization_slug": [
                "abc-flight-school",
                "abc-flight-school",
                "xyz-aviation",
                "xyz-aviation-2",
            ],
            "province": ["Western Cape", "Western Cape", "Gauteng", "Gauteng"],
            "website": [
                "https://abc.com",
                "https://abc.com",
                "https://xyz.com",
                "https://xyz.com",
            ],
            "contact_primary_email": [
                "contact@abc.com",
                "contact@abc.com",
                "info@xyz.com",
                "info@xyz.com",
            ],
            "contact_primary_phone": ["+27123456789", "+27123456789", None, None],
            "address_primary": ["123 Main St", "123 Main St", None, "456 Oak Ave"],
            "organization_category": [
                "Flight School",
                "Flight School",
                "Aviation",
                "Aviation",
            ],
            "status": ["Active", "Active", "Active", "Active"],
            "data_quality_score": [0.8, 0.8, 0.6, 0.7],
        }
    )


def test_resolve_entities_fallback(sample_df_with_duplicates):
    """Test fallback entity resolution."""
    deduplicated, predictions = resolve_entities_fallback(sample_df_with_duplicates)

    # Should remove exact slug duplicates
    assert len(deduplicated) == 3  # 4 original - 1 duplicate = 3

    # Predictions should be empty for fallback
    assert len(predictions) == 0


def test_resolve_entities_fallback_without_slug_column():
    """Fallback deduplication synthesises slugs from organization names."""

    df = pd.DataFrame(
        {
            "organization_name": ["Alpha Org", "Alpha Org", "Beta Org"],
            "province": ["WC", "WC", "GP"],
        }
    )

    deduplicated, predictions = resolve_entities_fallback(df)

    assert len(deduplicated) == 2
    assert len(predictions) == 0


def test_resolve_entities_fallback_with_sparse_slug_values():
    """Blank slug fields reuse slugified names to avoid crashes."""

    df = pd.DataFrame(
        {
            "organization_name": ["Gamma Org", "Gamma Org", "Delta Org"],
            "organization_slug": [None, "", "delta-org"],
            "province": ["WC", "WC", "GP"],
        }
    )

    deduplicated, _ = resolve_entities_fallback(df)

    assert len(deduplicated) == 2
    assert "organization_slug" in deduplicated.columns


def test_resolve_entities_fallback_all_data_missing():
    """Rows without identifying information are preserved without crashing."""

    df = pd.DataFrame(
        {
            "organization_name": [None, None],
            "organization_slug": [None, None],
            "province": [None, None],
        }
    )

    deduplicated, predictions = resolve_entities_fallback(df)

    assert len(deduplicated) == 2
    assert len(predictions) == 0


def test_calculate_completeness_score_full():
    """Test completeness score calculation with full data."""
    row = pd.Series(
        {
            "organization_name": "Test Org",
            "province": "Gauteng",
            "contact_primary_email": "test@example.com",
            "contact_primary_phone": "+27123456789",
            "website": "https://test.com",
            "address_primary": "123 Test St",
            "organization_category": "Aviation",
        }
    )

    score = calculate_completeness_score(row)
    assert score == 1.0


def test_calculate_completeness_score_partial():
    """Test completeness score with partial data."""
    row = pd.Series(
        {
            "organization_name": "Test Org",
            "province": "Gauteng",
            "contact_primary_email": None,
            "contact_primary_phone": None,
            "website": "https://test.com",
            "address_primary": None,
            "organization_category": "Aviation",
        }
    )

    score = calculate_completeness_score(row)
    assert 0.4 < score < 0.6  # 4 out of 7 fields filled


def test_calculate_completeness_score_empty():
    """Test completeness score with empty data."""
    row = pd.Series(
        {
            "organization_name": "",
            "province": None,
            "contact_primary_email": None,
            "contact_primary_phone": None,
            "website": None,
            "address_primary": None,
            "organization_category": None,
        }
    )

    score = calculate_completeness_score(row)
    assert score == 0.0


def test_add_ml_priority_scores(sample_df_with_duplicates):
    """Test adding ML priority scores."""
    df_with_scores = add_ml_priority_scores(sample_df_with_duplicates)

    # Check that new columns were added
    assert "completeness_score" in df_with_scores.columns
    assert "priority_score" in df_with_scores.columns

    # Check score ranges
    assert df_with_scores["completeness_score"].between(0, 1).all()
    assert df_with_scores["priority_score"].between(0, 1).all()

    # Priority score should be between quality and completeness
    for _idx, row in df_with_scores.iterrows():
        assert (
            min(row["data_quality_score"], row["completeness_score"])
            <= row["priority_score"]
            <= max(row["data_quality_score"], row["completeness_score"])
        )


def test_build_entity_registry(sample_df_with_duplicates):
    """Test building entity registry."""
    registry = build_entity_registry(sample_df_with_duplicates)

    # Check registry fields were added
    assert "entity_id" in registry.columns
    assert "first_seen" in registry.columns
    assert "last_updated" in registry.columns
    assert "name_variants" in registry.columns
    assert "status_history" in registry.columns

    # Check entity IDs are unique
    assert registry["entity_id"].nunique() == len(registry)

    # Check name variants is a list
    assert isinstance(registry["name_variants"].iloc[0], list)


def test_build_entity_registry_with_history_file():
    """Test building entity registry with history file."""
    df = pd.DataFrame(
        {
            "organization_name": ["Test Org"],
            "organization_slug": ["test-org"],
            "status": ["Active"],
        }
    )

    # Should not raise error even with non-existent history file
    registry = build_entity_registry(df, history_file="/nonexistent/file.json")

    assert len(registry) == 1


def test_build_entity_registry_merges_history(tmp_path):
    """Historical entity data is merged and preserved when provided."""

    history_df = pd.DataFrame(
        {
            "entity_id": [7, 8],
            "organization_name": ["Legacy Org", "Dormant Org"],
            "organization_slug": ["legacy-org", "dormant-org"],
            "first_seen": [pd.Timestamp("2024-01-01"), pd.Timestamp("2023-05-01")],
            "last_updated": [pd.Timestamp("2024-06-01"), pd.Timestamp("2024-06-01")],
            "name_variants": [["Legacy Org Pty"], ["Legacy Org Pty"]],
            "status_history": [
                [{"status": "Active", "date": "2024-06-01T00:00:00"}],
                [{"status": "Inactive", "date": "2024-06-01T00:00:00"}],
            ],
            "status": ["Active", "Inactive"],
        }
    )
    history_path = tmp_path / "entity_history.json"
    history_df.to_json(history_path, orient="records", date_format="iso")

    current_df = pd.DataFrame(
        {
            "organization_name": ["Legacy Org", "New Org"],
            "organization_slug": ["legacy-org", "new-org"],
            "status": ["Dormant", "Active"],
            "province": ["Gauteng", "Western Cape"],
        }
    )

    registry = build_entity_registry(current_df, history_file=str(history_path))

    # History row retained, new row appended, unmatched history preserved
    assert len(registry) == 3

    legacy = registry.loc[registry["organization_slug"] == "legacy-org"].iloc[0]
    assert legacy["entity_id"] == 7
    assert pd.to_datetime(legacy["first_seen"]) == pd.Timestamp("2024-01-01T00:00:00")
    assert legacy["status_history"][-1]["status"] == "Dormant"
    assert any(entry["status"] == "Active" for entry in legacy["status_history"])
    assert "Legacy Org" in legacy["name_variants"]

    new_org = registry.loc[registry["organization_slug"] == "new-org"].iloc[0]
    assert new_org["entity_id"] > 7
    assert isinstance(new_org["name_variants"], list)
    assert new_org["status_history"][-1]["status"] == "Active"

    dormant = registry.loc[registry["organization_slug"] == "dormant-org"].iloc[0]
    assert dormant["status_history"][0]["status"] == "Inactive"


def test_load_entity_history_parses_json_lists(tmp_path):
    """History loader parses JSON payloads without using literal evaluation."""

    history_path = tmp_path / "history.json"
    history_path.write_text(
        json.dumps(
            [
                {
                    "entity_id": 1,
                    "name_variants": ["Alpha", "Aviation"],
                    "status_history": [{"status": "active"}],
                }
            ]
        ),
        encoding="utf-8",
    )

    history = entity_resolution._load_entity_history(str(history_path))

    first_row = history.iloc[0]
    assert first_row["name_variants"] == ["Alpha", "Aviation"]
    assert first_row["status_history"] == [{"status": "active", "date": None}]


def test_load_entity_history_ignores_unexpected_strings(tmp_path):
    """Unexpected values are preserved safely instead of being executed."""

    history_path = tmp_path / "history.csv"
    history_path.write_text(
        """entity_id,name_variants\n1,__import__('os').system('whoami')\n""",
        encoding="utf-8",
    )

    history = entity_resolution._load_entity_history(str(history_path))

    first_row = history.iloc[0]
    assert first_row["name_variants"] == ["__import__('os').system('whoami')"]


def test_resolve_entities_with_splink_not_available():
    """Test Splink resolution when Splink is not available."""
    from unittest.mock import patch

    df = pd.DataFrame(
        {
            "organization_name": ["ABC Corp", "ABC Corp"],
            "organization_slug": ["abc-corp", "abc-corp"],
        }
    )

    with patch("hotpass.entity_resolution.SPLINK_AVAILABLE", False):
        from hotpass.entity_resolution import resolve_entities_with_splink

        deduplicated, matches = resolve_entities_with_splink(df)

        # Should fall back to simple deduplication
        assert len(deduplicated) <= len(df)


def test_build_splink_settings():
    """Test building Splink settings."""
    from hotpass.entity_resolution import build_splink_settings

    settings = build_splink_settings()

    # Check that settings dictionary is returned
    assert isinstance(settings, dict)
    assert "link_type" in settings
    assert "comparisons" in settings


def test_calculate_completeness_score_with_missing_columns():
    """Test completeness score with missing expected columns."""
    row = pd.Series({"organization_name": "Test", "some_other_field": "value"})

    # Should handle missing columns gracefully
    score = calculate_completeness_score(row)
    assert 0 <= score <= 1


def test_add_ml_priority_scores_without_quality_score():
    """Test adding priority scores when quality score column is missing."""
    df = pd.DataFrame(
        {
            "organization_name": ["Test Org"],
            "province": ["Test Province"],
        }
    )

    result = add_ml_priority_scores(df)

    # Should add scores even without quality_score column
    assert "completeness_score" in result.columns
    assert "priority_score" in result.columns
