#!/usr/bin/env python3
"""Refresh Data Docs by running validation against bundled sample workbooks.

This script runs checkpoint validation against the sample workbooks in data/
and generates Data Docs under dist/data-docs/. It's used in CI to verify
that expectation suites and checkpoints are properly configured.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

# Add src to path for direct execution
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from hotpass.error_handling import DataContractError
from hotpass.validation import run_checkpoint


def main() -> int:
    """Run validation checkpoints and generate Data Docs."""
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data"
    docs_dir = project_root / "dist" / "data-docs"

    # Ensure docs directory exists
    docs_dir.mkdir(parents=True, exist_ok=True)

    # Define checkpoints to run with their data sources
    checkpoints = [
        ("reachout_organisation", "Reachout Database.xlsx", "Organisation"),
        ("reachout_contact_info", "Reachout Database.xlsx", "Contact Info"),
        ("sacaa_cleaned", "SACAA Flight Schools - Refined copy__CLEANED.xlsx", "Cleaned"),
        ("contact_company_cat", "Contact Database.xlsx", "Company_Cat"),
        ("contact_company_contacts", "Contact Database.xlsx", "Company_Contacts"),
        ("contact_company_addresses", "Contact Database.xlsx", "Company_Addresses"),
        ("contact_capture", "Contact Database.xlsx", "10-10-25 Capture"),
    ]

    success_count = 0
    failure_count = 0

    print("Refreshing Data Docs from sample workbooks...")
    print(f"Data directory: {data_dir}")
    print(f"Docs directory: {docs_dir}")
    print()

    for checkpoint_name, workbook_name, sheet_name in checkpoints:
        workbook_path = data_dir / workbook_name
        source_file = f"{workbook_name}#{sheet_name}"

        if not workbook_path.exists():
            print(f"⚠ Skipping {checkpoint_name}: {workbook_name} not found")
            continue

        try:
            df = pd.read_excel(workbook_path, sheet_name=sheet_name)
            result = run_checkpoint(
                df,
                checkpoint_name=checkpoint_name,
                source_file=source_file,
                data_docs_dir=docs_dir,
            )
            print(f"✓ {checkpoint_name}: {result.success} ({len(df)} rows validated)")
            success_count += 1
        except DataContractError as exc:
            print(f"✗ {checkpoint_name}: Validation failed")
            print(f"  {exc.context.message}")
            failure_count += 1
        except Exception as exc:
            print(f"✗ {checkpoint_name}: Unexpected error - {exc}")
            failure_count += 1

    print()
    print(f"Validation complete: {success_count} passed, {failure_count} failed")

    if docs_dir.exists():
        doc_files = list(docs_dir.rglob("*.html"))
        print(f"Data Docs generated: {len(doc_files)} HTML files in {docs_dir}")

    return 0 if failure_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
