"""Tests for quality validation functionality."""

import pandas as pd
import pytest

from hotpass.quality import ExpectationSummary, build_ssot_schema, run_expectations


def test_build_ssot_schema():
    """Test that SSOT schema is created correctly."""
    schema = build_ssot_schema()

    assert schema is not None
    assert "organization_name" in schema.columns
    assert "organization_slug" in schema.columns
    assert "data_quality_score" in schema.columns

    # Organization name should not be nullable
    assert not schema.columns["organization_name"].nullable
    assert not schema.columns["organization_slug"].nullable


def test_ssot_schema_validates_valid_data():
    """Test that SSOT schema validates correct data."""
    schema = build_ssot_schema()

    valid_df = pd.DataFrame(
        {
            "organization_name": ["Test Org"],
            "organization_slug": ["test-org"],
            "province": ["Western Cape"],
            "country": ["South Africa"],
            "area": ["Cape Town"],
            "address_primary": ["123 Main St"],
            "organization_category": ["Flight School"],
            "organization_type": ["Active"],
            "status": ["Active"],
            "website": ["https://test.com"],
            "planes": ["Cessna 172"],
            "description": ["Test description"],
            "notes": ["Test notes"],
            "source_datasets": ["SACAA"],
            "source_record_ids": ["123"],
            "contact_primary_name": ["John Doe"],
            "contact_primary_role": ["Manager"],
            "contact_primary_email": ["john@test.com"],
            "contact_primary_phone": ["+27123456789"],
            "contact_secondary_emails": ["jane@test.com"],
            "contact_secondary_phones": ["+27987654321"],
            "data_quality_score": [0.85],
            "data_quality_flags": [""],
            "selection_provenance": ["SACAA"],
            "last_interaction_date": ["2024-01-01"],
            "priority": ["High"],
            "privacy_basis": ["Legitimate Interest"],
        }
    )

    # Should not raise an error
    validated = schema.validate(valid_df)
    assert len(validated) == 1


def test_run_expectations_with_valid_data():
    """Test run_expectations with valid data."""
    df = pd.DataFrame(
        {
            "organization_name": ["Test Org 1", "Test Org 2"],
            "organization_slug": ["test-org-1", "test-org-2"],
            "country": ["South Africa", "South Africa"],
            "data_quality_score": [0.8, 0.9],
            "contact_primary_email": ["test1@example.com", "test2@example.com"],
            "contact_primary_phone": ["+27123456789", "+27987654321"],
            "website": ["https://test1.com", "https://test2.com"],
        }
    )

    result = run_expectations(df)

    assert isinstance(result, ExpectationSummary)
    assert result.success is True
    assert len(result.failures) == 0


def test_run_expectations_with_missing_org_name():
    """Test run_expectations detects missing organization names."""
    df = pd.DataFrame(
        {
            "organization_name": [None, "Test Org"],
            "organization_slug": ["test-1", "test-2"],
            "country": ["South Africa", "South Africa"],
            "data_quality_score": [0.8, 0.9],
            "contact_primary_email": ["test1@example.com", "test2@example.com"],
            "contact_primary_phone": ["+27123456789", "+27987654321"],
            "website": ["https://test1.com", "https://test2.com"],
        }
    )

    result = run_expectations(df)

    assert result.success is False
    assert any("organization_name" in str(f) for f in result.failures)


def test_run_expectations_with_invalid_quality_score():
    """Test run_expectations detects invalid quality scores."""
    df = pd.DataFrame(
        {
            "organization_name": ["Test Org"],
            "organization_slug": ["test-org"],
            "country": ["South Africa"],
            "data_quality_score": [1.5],  # Invalid: > 1.0
            "contact_primary_email": ["test@example.com"],
            "contact_primary_phone": ["+27123456789"],
            "website": ["https://test.com"],
        }
    )

    result = run_expectations(df)

    assert result.success is False
    assert any("quality_score" in str(f).lower() for f in result.failures)


def test_run_expectations_with_invalid_email_format():
    """Test run_expectations detects invalid email formats."""
    df = pd.DataFrame(
        {
            "organization_name": ["Test Org 1", "Test Org 2", "Test Org 3"],
            "organization_slug": ["test-1", "test-2", "test-3"],
            "country": ["South Africa", "South Africa", "South Africa"],
            "data_quality_score": [0.8, 0.9, 0.7],
            "contact_primary_email": [
                "invalid-email",  # Invalid
                "test@example.com",  # Valid
                "another@test.com",  # Valid
            ],
            "contact_primary_phone": ["+271234", "+272345", "+273456"],
            "website": ["https://test1.com", "https://test2.com", "https://test3.com"],
        }
    )

    # With default threshold of 0.85, 2/3 valid (66%) should fail
    result = run_expectations(df, email_mostly=0.85)

    assert result.success is False
    assert any("email" in str(f).lower() for f in result.failures)


def test_run_expectations_with_custom_thresholds():
    """Test run_expectations with custom validation thresholds."""
    df = pd.DataFrame(
        {
            "organization_name": ["Test Org 1", "Test Org 2"],
            "organization_slug": ["test-1", "test-2"],
            "country": ["South Africa", "South Africa"],
            "data_quality_score": [0.8, 0.9],
            "contact_primary_email": [
                "test1@example.com",  # Valid
                "invalid",  # Invalid
            ],
            "contact_primary_phone": ["+27123456789", "+27987654321"],
            "website": ["https://test1.com", "https://test2.com"],
        }
    )

    # With 50% threshold, 1/2 valid should pass
    result = run_expectations(df, email_mostly=0.5)

    assert result.success is True


def test_run_expectations_with_blank_emails():
    """Test that blank emails are sanitized before validation."""
    df = pd.DataFrame(
        {
            "organization_name": ["Test Org 1", "Test Org 2", "Test Org 3"],
            "organization_slug": ["test-1", "test-2", "test-3"],
            "country": ["South Africa", "South Africa", "South Africa"],
            "data_quality_score": [0.8, 0.9, 0.7],
            "contact_primary_email": [
                "test@example.com",  # Valid
                "",  # Blank - should be treated as NA
                "another@test.com",  # Valid
            ],
            "contact_primary_phone": ["+271234", "+272345", "+273456"],
            "website": ["https://test1.com", "https://test2.com", "https://test3.com"],
        }
    )

    # Blank should be ignored, so 2/2 non-blank should be valid (100%)
    result = run_expectations(df, email_mostly=0.85)

    # Should pass since blanks are excluded
    assert result.success is True


def test_run_expectations_with_invalid_phone_format():
    """Test run_expectations detects invalid phone formats."""
    df = pd.DataFrame(
        {
            "organization_name": ["Test Org 1", "Test Org 2"],
            "organization_slug": ["test-1", "test-2"],
            "country": ["South Africa", "South Africa"],
            "data_quality_score": [0.8, 0.9],
            "contact_primary_email": ["test1@example.com", "test2@example.com"],
            "contact_primary_phone": [
                "123456",  # Invalid: no +
                "+27123456789",  # Valid
            ],
            "website": ["https://test1.com", "https://test2.com"],
        }
    )

    # With default threshold of 0.85, 1/2 valid (50%) should fail
    result = run_expectations(df, phone_mostly=0.85)

    assert result.success is False
    assert any("phone" in str(f).lower() for f in result.failures)


def test_run_expectations_with_invalid_website_format():
    """Test run_expectations detects invalid website formats."""
    df = pd.DataFrame(
        {
            "organization_name": ["Test Org 1", "Test Org 2"],
            "organization_slug": ["test-1", "test-2"],
            "country": ["South Africa", "South Africa"],
            "data_quality_score": [0.8, 0.9],
            "contact_primary_email": ["test1@example.com", "test2@example.com"],
            "contact_primary_phone": ["+27123456789", "+27987654321"],
            "website": [
                "www.test.com",  # Invalid: no https://
                "https://test2.com",  # Valid
            ],
        }
    )

    # With default threshold of 0.85, 1/2 valid (50%) should fail
    result = run_expectations(df, website_mostly=0.85)

    assert result.success is False
    assert any("website" in str(f).lower() for f in result.failures)


def test_run_expectations_with_wrong_country():
    """Test run_expectations detects wrong country values."""
    df = pd.DataFrame(
        {
            "organization_name": ["Test Org"],
            "organization_slug": ["test-org"],
            "country": ["United States"],  # Wrong country
            "data_quality_score": [0.8],
            "contact_primary_email": ["test@example.com"],
            "contact_primary_phone": ["+27123456789"],
            "website": ["https://test.com"],
        }
    )

    result = run_expectations(df)

    assert result.success is False
    assert any("country" in str(f).lower() for f in result.failures)


def test_run_expectations_with_empty_dataframe():
    """Test run_expectations handles empty DataFrame."""
    df = pd.DataFrame(
        {
            "organization_name": [],
            "organization_slug": [],
            "country": [],
            "data_quality_score": [],
            "contact_primary_email": [],
            "contact_primary_phone": [],
            "website": [],
        }
    )

    result = run_expectations(df)

    assert isinstance(result, ExpectationSummary)
    # Empty df should pass contact format checks (no data to validate)
    # But may fail other checks
    assert isinstance(result.success, bool)


def test_run_expectations_with_all_na_emails():
    """Test run_expectations when all emails are NA."""
    df = pd.DataFrame(
        {
            "organization_name": ["Test Org 1", "Test Org 2"],
            "organization_slug": ["test-1", "test-2"],
            "country": ["South Africa", "South Africa"],
            "data_quality_score": [0.8, 0.9],
            "contact_primary_email": [None, None],  # All NA
            "contact_primary_phone": ["+27123456789", "+27987654321"],
            "website": ["https://test1.com", "https://test2.com"],
        }
    )

    result = run_expectations(df)

    # Should pass email check since all are NA (no non-null values to validate)
    assert isinstance(result, ExpectationSummary)


def test_expectation_summary_structure():
    """Test ExpectationSummary dataclass structure."""
    summary = ExpectationSummary(success=True, failures=[])

    assert summary.success is True
    assert summary.failures == []

    summary2 = ExpectationSummary(success=False, failures=["error1", "error2"])

    assert summary2.success is False
    assert len(summary2.failures) == 2
