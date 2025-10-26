from __future__ import annotations

import pytest

pytest.importorskip("frictionless")

from hotpass.pipeline import QualityReport  # noqa: E402


def _sample_report() -> QualityReport:
    return QualityReport(
        total_records=10,
        invalid_records=2,
        schema_validation_errors=["organization_name null"],
        expectations_passed=False,
        expectation_failures=["contact_primary_email format"],
        source_breakdown={"SACAA Cleaned": 6, "Reachout Database": 4},
        data_quality_distribution={"mean": 0.75, "min": 0.5, "max": 0.95},
        performance_metrics={
            "total_seconds": 1.23,
            "load_seconds": 0.4,
            "aggregation_seconds": 0.5,
            "expectations_seconds": 0.2,
            "write_seconds": 0.13,
            "rows_per_second": 120.0,
        },
    )


def test_quality_report_to_dict_roundtrips() -> None:
    report = _sample_report()
    payload = report.to_dict()

    assert payload["total_records"] == report.total_records
    assert payload["expectations_passed"] is report.expectations_passed
    assert payload["source_breakdown"]["SACAA Cleaned"] == 6
    assert payload["performance_metrics"]["rows_per_second"] == 120.0


def test_quality_report_to_markdown_contains_sections() -> None:
    report = _sample_report()
    markdown = report.to_markdown()

    assert "# Hotpass Quality Report" in markdown
    assert "Total records" in markdown
    assert "| Source | Records |" in markdown
    assert "contact_primary_email format" in markdown
    assert "Performance Metrics" in markdown


def test_quality_report_to_html_contains_table() -> None:
    report = _sample_report()
    html = report.to_html()

    assert "<table" in html
    assert "Quality Metrics" in html
    assert "SACAA Cleaned" in html
    assert "Performance Metrics" in html
