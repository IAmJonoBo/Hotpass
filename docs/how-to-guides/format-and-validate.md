---
title: How-to — format outputs and enforce validation rules
summary: Apply professional styling, govern ingest schemas, and surface parquet/CSVW artefacts for downstream tooling.
last_updated: 2025-12-26
---

# How-to — format outputs and enforce validation rules

Follow this guide when stakeholders expect polished deliverables and tailored quality gates.

## Enable premium formatting

```python
from pathlib import Path
from hotpass import PipelineConfig, OutputFormat, run_pipeline

formatting = OutputFormat(
    header_bg_color="366092",
    header_font_color="FFFFFF",
    zebra_striping=True,
    auto_size_columns=True,
    freeze_header_row=True,
    add_filters=True,
)

config = PipelineConfig(
    input_dir=Path("data"),
    output_path=Path("dist/refined.xlsx"),
    enable_formatting=True,
    output_format=formatting,
)
run_pipeline(config)
```

Key options:

- `header_bg_color` and `header_font_color` use hex RGB strings.
- `zebra_striping` alternates row colours for better readability.
- `add_filters` adds Excel auto-filters to every column.

## Govern ingest schemas and expectations

Every workbook consumed by the pipeline now carries a Frictionless Table Schema contract under `schemas/` and a matching Great Expectations suite under `data_expectations/`. Contracts ship with the package and are exercised automatically during `ingest_sources()`.

To introduce a new sheet, add the schema/expectation pair:

```bash
cp schemas/reachout_organisation.schema.json schemas/my_feed.schema.json
cp data_expectations/reachout/organisation.json data_expectations/my_feed/source.json
```

Update the descriptors with your column names, then reference them from a data source loader. If the workbook drifts from the schema, `DataContractError` raises with the missing/extra fields and blocks the run.

To dry-run a contract locally, use the helper APIs:

```python
from pathlib import Path
import pandas as pd

from hotpass.validation import validate_with_frictionless, validate_with_expectations

frame = pd.read_excel(Path("data/Reachout Database.xlsx"), sheet_name="Organisation")
validate_with_frictionless(
    frame,
    schema_descriptor="reachout_organisation.schema.json",
    table_name="Reachout Organisation",
    source_file="Reachout Database.xlsx#Organisation",
)
validate_with_expectations(
    frame,
    suite_descriptor="reachout/organisation.json",
    source_file="Reachout Database.xlsx#Organisation",
)
```

## Customise validation thresholds

Profiles still define the SSOT quality tolerances. Override them for specific deployments:

```yaml
validation:
  email_validity: 0.9
  phone_validity: 0.85
  website_validity: 0.75
  duplicate_threshold: 0.1
```

Lower thresholds make the pipeline more permissive for exploratory analysis. Higher thresholds (≥0.95) are recommended for production datasets.

## Capture governed artefacts (Parquet, DuckDB, CSVW)

Validated outputs are now materialised as Polars-backed Parquet snapshots and queried via DuckDB before the final export. After every run you will find:

- A Parquet file beside your chosen output (`refined.xlsx → refined.parquet`) containing the DuckDB ordered dataset.
- Optional CSV exports accompanied by a CSVW sidecar (`refined.csv-metadata.json`) whose table schema is sourced from `schemas/ssot.schema.json`.

You can inspect the Parquet snapshot directly with DuckDB for ad-hoc SQL:

```python
import duckdb

with duckdb.connect() as conn:
    df = conn.execute(
        "SELECT organization_name, data_quality_score FROM read_parquet('dist/refined.parquet') ORDER BY data_quality_score DESC"
    ).fetch_df()
```

Re-running `run_pipeline` will refresh both the parquet snapshot and any CSVW metadata automatically.

## Monitor validation feedback

After each run, inspect the generated quality report:

```python
from hotpass.quality import load_quality_report

report = load_quality_report(Path("dist/quality-report.json"))
print(report.summary())
```

Combine the structured report with the Markdown export to share remediation tasks with stakeholders.

## Troubleshooting

- **Excel formatting not applied**: Ensure `enable_formatting=True` and install the `dashboards` extra for the required libraries.
- **Frictionless or Great Expectations failures**: Compare the failure payload in the raised `DataContractError` with the schema/expectation JSON files. Align the workbook headers (case-sensitive) or extend the contract as needed.
- **Large Excel files**: Disable conditional formatting for columns with more than 50,000 rows to speed up exports.
- **Missing CSVW sidecar**: Confirm the target filename ends with `.csv`; other extensions bypass CSVW generation.
