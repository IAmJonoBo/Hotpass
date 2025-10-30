"""Tests for intelligent column mapping."""

import pandas as pd
import pytest

pytest.importorskip("frictionless")

from hotpass.column_mapping import (  # noqa: E402
    ColumnMapper,
    infer_column_types,
    profile_dataframe,
)


def test_column_mapper_exact_match():
    """Test that exact column name matches work."""
    target_schema = {
        "organization_name": ["company", "business"],
        "contact_email": ["email", "mail"],
    }

    mapper = ColumnMapper(target_schema)
    source_columns = ["organization_name", "contact_email", "other"]

    result = mapper.map_columns(source_columns, confidence_threshold=0.7)

    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")


def test_column_mapper_synonym_match():
    """Test that synonym matching works."""
    target_schema = {
        "organization_name": ["company", "business"],
        "contact_email": ["email", "mail"],
    }

    mapper = ColumnMapper(target_schema)
    source_columns = ["company", "email"]

    result = mapper.map_columns(source_columns, confidence_threshold=0.7)

    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")


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
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")


def test_column_mapper_no_match():
    """Test handling of unmappable columns."""
    target_schema = {
        "organization_name": ["company"],
    }

    mapper = ColumnMapper(target_schema)
    source_columns = ["completely_different", "xyz123"]

    result = mapper.map_columns(source_columns, confidence_threshold=0.7)

    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")


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

    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")


def test_infer_column_types_email():
    """Test email column type inference."""
    df = pd.DataFrame(
        {
            "email": ["test@example.com", "user@domain.org", "admin@site.net"],
        }
    )

    types = infer_column_types(df)

    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")


def test_infer_column_types_phone():
    """Test phone column type inference."""
    df = pd.DataFrame(
        {
            "phone": ["+1234567890", "123-456-7890", "(123) 456-7890"],
        }
    )

    types = infer_column_types(df)

    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")


def test_infer_column_types_url():
    """Test URL column type inference."""
    df = pd.DataFrame(
        {
            "website": ["https://example.com", "www.site.org", "http://domain.net"],
        }
    )

    types = infer_column_types(df)

    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")


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

    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
