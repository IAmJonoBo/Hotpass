from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

import hotpass.quality as quality
from hotpass.pipeline import (
    SSOT_COLUMNS,
    PipelineConfig,
    PipelineResult,
    _aggregate_group,
    run_pipeline,
)


def test_pipeline_generates_refined_dataset(tmp_path: Path, sample_data_dir: Path) -> None:
    output_path = tmp_path / "refined.xlsx"
    config = PipelineConfig(
        input_dir=sample_data_dir,
        output_path=output_path,
        expectation_suite_name="default",
        country_code="ZA",
    )

    result: PipelineResult = run_pipeline(config)

    assert output_path.exists(), "Pipeline should persist refined workbook"
    refined = result.refined

    assert list(refined.columns) == SSOT_COLUMNS
    assert len(refined) == 2

    aero_record = refined.loc[refined["organization_name"] == "Aero School"].iloc[0]
    assert aero_record["contact_primary_email"] == "jane.doe@aero.example"
    assert aero_record["contact_primary_phone"] == "+27821234567"
    assert aero_record["website"] == "https://aero.example"
    assert aero_record["province"] == "Gauteng"
    assert aero_record["data_quality_score"] == pytest.approx(1.0, abs=0.01)
    assert "Reachout Database" in aero_record["source_datasets"]
    assert aero_record["last_interaction_date"] == "2025-03-10"

    selection_raw = aero_record["selection_provenance"]
    assert isinstance(selection_raw, str)
    provenance = json.loads(selection_raw)
    assert provenance["website"]["source_dataset"] == "SACAA Cleaned"
    assert provenance["contact_primary_email"]["source_dataset"] == "SACAA Cleaned"
    assert provenance["province"]["source_dataset"] == "SACAA Cleaned"
    assert provenance["contact_primary_phone"]["source_dataset"] == "SACAA Cleaned"

    report = result.quality_report
    assert report.total_records == 2
    assert report.invalid_records == 0
    assert report.expectations_passed
    assert report.schema_validation_errors == []


def test_pipeline_flags_records_with_missing_contact(sample_data_dir: Path, tmp_path: Path) -> None:
    output_path = tmp_path / "refined.xlsx"
    config = PipelineConfig(
        input_dir=sample_data_dir,
        output_path=output_path,
        expectation_suite_name="default",
        country_code="ZA",
    )
    result = run_pipeline(config)
    heli = result.refined.loc[result.refined["organization_name"] == "Heli Ops"].iloc[0]

    assert heli["contact_primary_email"] == "kelly@heliops.example"
    assert heli["contact_secondary_emails"] == "ops@heliops.example"
    assert heli["data_quality_score"] < 1.0
    assert "missing_website" in heli["data_quality_flags"].split(";")
    assert heli["last_interaction_date"] == "2025-02-18"

    heli_selection_raw = heli["selection_provenance"]
    assert isinstance(heli_selection_raw, str)
    provenance = json.loads(heli_selection_raw)
    assert provenance["contact_primary_email"]["source_dataset"] == "SACAA Cleaned"
    assert provenance["contact_primary_phone"]["source_dataset"] == "SACAA Cleaned"


def test_aggregate_group_prioritises_reliable_and_recent_values() -> None:
    slug = "aero-school"
    group = pd.DataFrame(
        [
            {
                "organization_name": "Aero School",
                "province": None,
                "area": None,
                "address": "Older Hangar",
                "category": "Flight School",
                "organization_type": "Flight School",
                "status": "Active",
                "website": "https://contact.example",
                "planes": None,
                "description": None,
                "notes": None,
                "priority": "Medium",
                "contact_names": ["Older Ops"],
                "contact_roles": ["Operations"],
                "contact_emails": ["ops@contact.example"],
                "contact_phones": ["+27820001111"],
                "source_dataset": "Contact Database",
                "source_record_id": "contact:1",
                "last_interaction_date": "2025-04-01",
            },
            {
                "organization_name": "Aero School",
                "province": "Gauteng",
                "area": "Gauteng",
                "address": "Hangar 1",
                "category": "Flight School",
                "organization_type": "Flight School",
                "status": "Active",
                "website": "https://reachout.example",
                "planes": None,
                "description": None,
                "notes": None,
                "priority": "High",
                "contact_names": ["Jane Doe"],
                "contact_roles": ["Head"],
                "contact_emails": ["jane.doe@reachout.example"],
                "contact_phones": ["+27825550000"],
                "source_dataset": "Reachout Database",
                "source_record_id": "reachout:1",
                "last_interaction_date": "2025-03-10",
            },
            {
                "organization_name": "Aero School",
                "province": "Gauteng",
                "area": "Gauteng",
                "address": "Hangar 1",
                "category": "Flight School",
                "organization_type": "Flight School",
                "status": "Active",
                "website": "https://reachout.example",
                "planes": None,
                "description": None,
                "notes": None,
                "priority": "Medium",
                "contact_names": ["Legacy Reachout"],
                "contact_roles": ["Ops"],
                "contact_emails": ["legacy@reachout.example"],
                "contact_phones": ["+27827777777"],
                "source_dataset": "Reachout Database",
                "source_record_id": "reachout:legacy",
                "last_interaction_date": "2024-01-01",
            },
            {
                "organization_name": "Aero School",
                "province": "Gauteng",
                "area": "Gauteng",
                "address": "Hangar 1",
                "category": "Flight School",
                "organization_type": "Flight School",
                "status": "Active",
                "website": "https://sacaa.example",
                "planes": None,
                "description": None,
                "notes": None,
                "priority": None,
                "contact_names": ["Regulator"],
                "contact_roles": ["Contact"],
                "contact_emails": ["info@sacaa.example"],
                "contact_phones": [],
                "source_dataset": "SACAA Cleaned",
                "source_record_id": "sacaa:1",
                "last_interaction_date": None,
            },
        ]
    )

    aggregated = _aggregate_group(slug, group)

    assert aggregated["website"] == "https://sacaa.example"
    assert aggregated["province"] == "Gauteng"
    assert aggregated["contact_primary_email"] == "info@sacaa.example"
    assert (
        aggregated["contact_secondary_emails"]
        == "jane.doe@reachout.example;legacy@reachout.example;ops@contact.example"
    )
    assert aggregated["contact_primary_phone"] == "+27825550000"
    assert aggregated["contact_secondary_phones"] == "+27827777777;+27820001111"
    aggregated_selection = aggregated["selection_provenance"]
    assert isinstance(aggregated_selection, str)
    provenance = json.loads(aggregated_selection)
    assert provenance["website"]["source_dataset"] == "SACAA Cleaned"
    website_provenance = provenance["website"]
    phone_provenance = provenance["contact_primary_phone"]
    assert website_provenance["source_priority"] >= phone_provenance["source_priority"]
    assert provenance["contact_primary_email"]["source_dataset"] == "SACAA Cleaned"
    assert provenance["contact_primary_phone"]["source_dataset"] == "Reachout Database"
    assert provenance["contact_primary_phone"]["last_interaction_date"] == "2025-03-10"


def test_run_expectations_fallback_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(quality, "PandasDataset", None)

    df = pd.DataFrame(
        {
            "organization_name": ["Valid Org", "Blank Org"],
            "organization_slug": ["valid-org", "blank-org"],
            "data_quality_score": [0.9, 0.8],
            "contact_primary_email": ["valid@example.com", ""],
            "contact_primary_phone": ["+27123456789", ""],
            "website": ["https://valid.example", ""],
            "country": ["South Africa", "South Africa"],
        }
    )

    summary = quality.run_expectations(df)

    assert summary.success
    assert summary.failures == []


def test_run_expectations_fallback_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(quality, "PandasDataset", None)

    df = pd.DataFrame(
        {
            "organization_name": ["Org A", "Org B"],
            "organization_slug": ["org-a", "org-b"],
            "data_quality_score": [0.7, 0.6],
            "contact_primary_email": ["invalid", "also_invalid"],
            "contact_primary_phone": ["+27123456789", "+27123456780"],
            "website": ["https://org-a.example", "https://org-b.example"],
            "country": ["South Africa", "South Africa"],
        }
    )

    summary = quality.run_expectations(df, email_mostly=0.9)

    assert not summary.success
    assert any("contact_primary_email format" in failure for failure in summary.failures)
