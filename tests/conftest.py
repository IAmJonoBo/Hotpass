from __future__ import annotations

import os
import warnings
from pathlib import Path

import pandas as pd
import pytest
from marshmallow.warnings import ChangedInMarshmallow4Warning


def _install_warning_filters() -> None:
    warnings.filterwarnings(
        "ignore",
        category=ChangedInMarshmallow4Warning,
        message=(
            "`Number` field should not be instantiated. "
            "Use `Integer`, `Float`, or `Decimal` instead."
        ),
    )
    warnings.filterwarnings(
        "ignore",
        category=pytest.PytestUnraisableExceptionWarning,
    )
    warnings.filterwarnings(
        "ignore",
        category=ResourceWarning,
        message="Implicitly cleaning up <TemporaryDirectory",
    )


_install_warning_filters()


def pytest_configure(config: pytest.Config) -> None:
    _install_warning_filters()


@pytest.fixture(autouse=True)
def _fail_fast_for_mutmut() -> None:
    if os.environ.get("MUTANT_UNDER_TEST") == "fail":
        pytest.fail("mutmut forced failure sentinel", pytrace=False)


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
                "kelly@heliops.example; ops@heliops.example",
            ],
        }
    )

    with pd.ExcelWriter(
        data_dir / "SACAA Flight Schools - Refined copy__CLEANED.xlsx"
    ) as writer:
        sacaa_cleaned.to_excel(writer, sheet_name="Cleaned", index=False)

    return data_dir
