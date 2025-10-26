"""Tests for intelligent column mapping."""

import pandas as pd
import pytest

pytest.importorskip("frictionless")

from hotpass.column_mapping import ColumnMapper, infer_column_types, profile_dataframe  # noqa: E402


def test_column_mapper_exact_match():
    """Test that exact column name matches work."""
    target_schema = {
        "organization_name": ["company", "business"],
        "contact_email": ["email", "mail"],
    }

    mapper = ColumnMapper(target_schema)
    source_columns = ["organization_name", "contact_email", "other"]

    result = mapper.map_columns(source_columns, confidence_threshold=0.7)

    assert result["mapped"]["organization_name"] == "organization_name"
    assert result["mapped"]["contact_email"] == "contact_email"


def test_column_mapper_synonym_match():
    """Test that synonym matching works."""
    target_schema = {
        "organization_name": ["company", "business"],
        "contact_email": ["email", "mail"],
    }

    mapper = ColumnMapper(target_schema)
    source_columns = ["company", "email"]

    result = mapper.map_columns(source_columns, confidence_threshold=0.7)

    assert result["mapped"]["company"] == "organization_name"
    assert result["mapped"]["email"] == "contact_email"


def test_column_mapper_fuzzy_match():
    """Test that fuzzy matching works for similar names."""
    target_schema = {
        "organization_name": ["company"],
        "contact_email": ["email"],
    }

    mapper = ColumnMapper(target_schema)
    source_columns = ["organization name", "contactemail"]  # Different spacing/format

    result = mapper.map_columns(source_columns, confidence_threshold=0.7)

    # Should map with high confidence due to similarity
    assert "organization name" in result["mapped"]
    assert "contactemail" in result["mapped"]


def test_column_mapper_no_match():
    """Test handling of unmappable columns."""
    target_schema = {
        "organization_name": ["company"],
    }

    mapper = ColumnMapper(target_schema)
    source_columns = ["completely_different", "xyz123"]

    result = mapper.map_columns(source_columns, confidence_threshold=0.7)

    assert len(result["unmapped"]) > 0


def test_column_mapper_apply_mapping():
    """Test applying a mapping to a DataFrame."""
    df = pd.DataFrame(
        {
            "company": ["Acme Inc"],
            "email": ["test@example.com"],
        }
    )

    mapper = ColumnMapper({})
    mapping = {"company": "organization_name", "email": "contact_email"}

    result_df = mapper.apply_mapping(df, mapping)

    assert "organization_name" in result_df.columns
    assert "contact_email" in result_df.columns
    assert result_df["organization_name"].iloc[0] == "Acme Inc"


def test_infer_column_types_email():
    """Test email column type inference."""
    df = pd.DataFrame(
        {
            "email": ["test@example.com", "user@domain.org", "admin@site.net"],
        }
    )

    types = infer_column_types(df)

    assert types["email"] == "email"


def test_infer_column_types_phone():
    """Test phone column type inference."""
    df = pd.DataFrame(
        {
            "phone": ["+1234567890", "123-456-7890", "(123) 456-7890"],
        }
    )

    types = infer_column_types(df)

    assert types["phone"] == "phone"


def test_infer_column_types_url():
    """Test URL column type inference."""
    df = pd.DataFrame(
        {
            "website": ["https://example.com", "www.site.org", "http://domain.net"],
        }
    )

    types = infer_column_types(df)

    assert types["website"] == "url"


def test_profile_dataframe():
    """Test DataFrame profiling."""
    df = pd.DataFrame(
        {
            "name": ["Alice", "Bob", None],
            "email": ["alice@test.com", "bob@test.com", "charlie@test.com"],
            "score": [1, 2, 3],
        }
    )

    profile = profile_dataframe(df)

    assert profile["row_count"] == 3
    assert profile["column_count"] == 3
    assert "name" in profile["columns"]
    assert profile["columns"]["name"]["missing_count"] == 1
    assert profile["duplicate_rows"] == 0
