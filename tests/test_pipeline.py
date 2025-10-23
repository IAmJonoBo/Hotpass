from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from hotpass.pipeline import SSOT_COLUMNS, PipelineConfig, PipelineResult, run_pipeline


@pytest.fixture()
def sample_data_dir(tmp_path: Path) -> Path:
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    reachout_org = pd.DataFrame(
        {
            "Organisation Name": ["Aero School", "Heli Ops"],
            "ID": [1, 2],
            "Reachout Date": ["March 10, 2025", "2025-01-20"],
            "Recent_Touch_Ind": ["Y", "N"],
            "Area": ["Gauteng", "Western Cape"],
            "Distance": [0, 1200],
            "Type": ["Flight School", "Helicopter"],
            "Website": ["www.aero.example", ""],
            "Address": ["Hangar 1", "Cape Town Intl"],
            "Planes": ["Sling 2", "Robinson R44"],
            "Description Type": ["Fixed-wing", "Rotary"],
            "Notes": ["Follow up", ""],
            "Open Questions": ["Need pricing", ""],
        }
    )
    reachout_contacts = pd.DataFrame(
        {
            "ID": [1, 1, 2],
            "Organisation Name": ["Aero School", "Aero School", "Heli Ops"],
            "Reachout Date": ["2025-01-15", "2025-01-15", "2025-01-20"],
            "Firstname": ["Jane", "Ops", "Kelly"],
            "Surname": ["Doe", "Team", "Nguyen"],
            "Position": ["Head of Training", "Operations", "Chief Pilot"],
            "Phone": ["082 123 4567", "0829991111", "021 555 0000"],
            "WhatsApp": ["0821234567", "", "0215550000"],
            "Email": [
                "JANE.DOE@AERO.EXAMPLE",
                "ops@aero.example",
                "kelly@heliops.example",
            ],
            "Invalid": ["", "", ""],
            "Unnamed: 10": ["Validated", "Validated", "Validated"],
        }
    )

    with pd.ExcelWriter(data_dir / "Reachout Database.xlsx") as writer:
        reachout_org.to_excel(writer, sheet_name="Organisation", index=False)
        reachout_contacts.to_excel(writer, sheet_name="Contact Info", index=False)

    company_cat = pd.DataFrame(
        {
            "C_ID": [10, 11],
            "Company": ["Aero School", "Heli Ops"],
            "QuickNooks_Name": ["Aero School QB", "Heli Ops QB"],
            "Last_Order_Date": ["2024-11-01", ""],
            "Category": ["Flight School", "Helicopter"],
            "Strat": ["Core", "Expansion"],
            "Priority": ["High", "Medium"],
            "Status": ["Active", "Prospect"],
            "LoadDate": ["05/02/2025", "2025/02/18"],
            "Checked": ["2024-11-05", "2024-11-05"],
            "Website": ["https://aero.example", ""],
        }
    )
    company_contacts = pd.DataFrame(
        {
            "C_ID": [10, 11],
            "Company": ["Aero School", "Heli Ops"],
            "Status": ["Active", "Prospect"],
            "FirstName": ["John", "Kelly"],
            "Surname": ["Smith", "Nguyen"],
            "Position": ["Operations", "Chief Pilot"],
            "Cellnumber": ["+27 82 999 1111", "0215550000"],
            "Email": ["ops@aero.example", "kelly@heliops.example"],
            "Landline": ["0111110000", "0215550001"],
        }
    )
    company_addresses = pd.DataFrame(
        {
            "C_ID": [10, 11],
            "Company": ["Aero School", "Heli Ops"],
            "Type": ["Head", "Head"],
            "Airport": ["FALA", "FACT"],
            "Unnamed: 4": ["Hangar Complex", "Cape Town Intl"],
        }
    )
    capture_sheet = pd.DataFrame(
        {
            "Unnamed: 0": [""],
            "School": ["Heli Ops"],
            "Contact person (role)": ["Kelly Nguyen (Chief Pilot)"],
            "Phone": ["021 555 0000"],
            "Email": ["kelly@heliops.example"],
            "Addresses": ["Cape Town"],
            "Planes": ["Robinson R44"],
            "Website": [""],
            "Description": ["Helicopter operations"],
            "Type": ["Helicopter"],
        }
    )

    with pd.ExcelWriter(data_dir / "Contact Database.xlsx") as writer:
        company_cat.to_excel(writer, sheet_name="Company_Cat", index=False)
        company_contacts.to_excel(writer, sheet_name="Company_Contacts", index=False)
        company_addresses.to_excel(writer, sheet_name="Company_Addresses", index=False)
        capture_sheet.to_excel(writer, sheet_name="10-10-25 Capture", index=False)

    sacaa_cleaned = pd.DataFrame(
        {
            "Name of Organisation": ["Aero School", "Heli Ops"],
            "Province": ["Gauteng", "Western Cape"],
            "Status": ["Active", "Active"],
            "Website URL": ["https://aero.example", ""],
            "Contact Person": ["Jane Doe", "Kelly Nguyen"],
            "Contact Number": ["0821234567", "0215550000"],
            "Contact Email Address": [
                "jane.doe@aero.example",
                "kelly@heliops.example",
            ],
        }
    )

    with pd.ExcelWriter(data_dir / "SACAA Flight Schools - Refined copy__CLEANED.xlsx") as writer:
        sacaa_cleaned.to_excel(writer, sheet_name="Cleaned", index=False)

    return data_dir


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
    assert pytest.approx(aero_record["data_quality_score"], 0.01) == 1.0
    assert "Reachout Database" in aero_record["source_datasets"]
    assert aero_record["last_interaction_date"] == "2025-03-10"

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
    assert heli["data_quality_score"] < 1.0
    assert "missing_website" in heli["data_quality_flags"].split(";")
    assert heli["last_interaction_date"] == "2025-02-18"
