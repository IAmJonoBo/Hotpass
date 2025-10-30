"""Tests for enhanced pipeline features."""

from pathlib import Path

import pandas as pd
import pytest

pytest.importorskip("frictionless")

from hotpass.config import get_default_profile  # noqa: E402
from hotpass.formatting import OutputFormat
from hotpass.pipeline import PipelineConfig, run_pipeline
from hotpass.pipeline_reporting import generate_recommendations
from hotpass.quality import ExpectationSummary


def test_generate_recommendations_good_quality():
    """Test recommendation generation for good quality data."""
    df = pd.DataFrame(
        {
            "contact_primary_email": ["test@example.com", "user@test.com"],
            "contact_primary_phone": ["+27123456789", "+27987654321"],
            "data_quality_score": [0.8, 0.9],
            "data_quality_flags": ["none", "none"],
        }
    )

    expectation_summary = ExpectationSummary(success=True, failures=[])
    quality_dist = {"mean": 0.85, "min": 0.8, "max": 0.9}

    recommendations = generate_recommendations(df, expectation_summary, quality_dist)

    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")


def test_generate_recommendations_poor_quality():
    """Test recommendation generation for poor quality data."""
    df = pd.DataFrame(
        {
            "contact_primary_email": [None, None, "test@example.com"],
            "contact_primary_phone": [None, None, "+27123456789"],
            "data_quality_score": [0.2, 0.3, 0.4],
            "data_quality_flags": ["missing_email", "missing_phone", "none"],
        }
    )

    expectation_summary = ExpectationSummary(success=False, failures=["Some failure"])
    quality_dist = {"mean": 0.3, "min": 0.2, "max": 0.4}

    recommendations = generate_recommendations(df, expectation_summary, quality_dist)

    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
    # Should have critical or warning recommendations
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
        "critical" in rec.lower() or "warning" in rec.lower() for rec in recommendations
    )


def test_pipeline_with_formatting(sample_data_dir: Path, tmp_path: Path):
    """Test pipeline with formatting enabled."""
    output_path = tmp_path / "output" / "refined.xlsx"
    output_path.parent.mkdir()

    config = PipelineConfig(
        input_dir=sample_data_dir,
        output_path=output_path,
        enable_formatting=True,
        output_format=OutputFormat(),
        industry_profile=get_default_profile("generic"),
    )

    result = run_pipeline(config)

    # Check that output was created
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")

    # Check that quality report includes new fields
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
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")


def test_pipeline_with_audit_trail(sample_data_dir: Path, tmp_path: Path):
    """Test pipeline audit trail generation."""
    output_path = tmp_path / "output" / "refined.xlsx"
    output_path.parent.mkdir()

    config = PipelineConfig(
        input_dir=sample_data_dir,
        output_path=output_path,
        enable_audit_trail=True,
    )

    result = run_pipeline(config)

    # Check audit trail
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")

    # Should have start and complete events
    events = [entry["event"] for entry in result.quality_report.audit_trail]
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")


def test_pipeline_uses_profile_thresholds(sample_data_dir: Path, tmp_path: Path):
    """Test that pipeline uses industry profile validation thresholds."""
    from hotpass.config import IndustryProfile

    output_path = tmp_path / "output" / "refined.xlsx"
    output_path.parent.mkdir()

    # Create profile with custom thresholds
    profile = IndustryProfile(
        name="custom",
        display_name="Custom",
        email_validation_threshold=0.95,
        phone_validation_threshold=0.95,
        website_validation_threshold=0.90,
    )

    config = PipelineConfig(
        input_dir=sample_data_dir,
        output_path=output_path,
        industry_profile=profile,
    )

    result = run_pipeline(config)

    # Pipeline should complete successfully
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")


def test_quality_report_to_dict_includes_new_fields():
    """Test that quality report to_dict includes new fields."""
    from hotpass.pipeline import QualityReport

    report = QualityReport(
        total_records=10,
        invalid_records=0,
        schema_validation_errors=[],
        expectations_passed=True,
        expectation_failures=[],
        source_breakdown={"Test": 10},
        data_quality_distribution={"mean": 0.8, "min": 0.5, "max": 1.0},
        recommendations=["Test recommendation"],
        audit_trail=[{"event": "test"}],
        conflict_resolutions=[{"field": "test", "value": "value"}],
    )

    report_dict = report.to_dict()

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


def test_quality_report_markdown_includes_recommendations():
    """Test that quality report markdown includes recommendations section."""
    from hotpass.pipeline import QualityReport

    report = QualityReport(
        total_records=10,
        invalid_records=0,
        schema_validation_errors=[],
        expectations_passed=True,
        expectation_failures=[],
        source_breakdown={"Test": 10},
        data_quality_distribution={"mean": 0.8, "min": 0.5, "max": 1.0},
        recommendations=["Improve email coverage", "Add more phone numbers"],
        conflict_resolutions=[
            {
                "field": "website",
                "chosen_source": "Source A",
                "value": "http://example.com",
                "alternatives": [{"source": "Source B", "value": "http://test.com"}],
            }
        ],
    )

    markdown = report.to_markdown()

    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
