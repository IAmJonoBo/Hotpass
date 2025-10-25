---
title: Quickstart — refine a workbook in minutes
summary: Run the core Hotpass pipeline end-to-end using sample data and explore the generated outputs.
last_updated: 2025-10-25
---

# Quickstart — refine a workbook in minutes

This tutorial shows you how to install Hotpass, validate a spreadsheet, and publish a refined workbook with quality insights. It assumes you are comfortable with Python tooling but are new to the Hotpass platform.

## 1. Install the tooling

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if it is not already available.
2. Clone the repository and create a virtual environment.

```bash
uv venv
uv sync --extra dev --extra docs
uv run pre-commit install
```

Hotpass includes optional extras for orchestration, enrichment, geospatial insights, and dashboards. You can add them at any time:

```bash
uv sync --extra dev --extra orchestration --extra enrichment --extra geospatial --extra dashboards
```

## 2. Inspect the sample data

The `data/` directory contains anonymised Excel workbooks that mirror the structure of customer spreadsheets. Open one of the files to review key columns such as `organization_name`, `contact_email`, and `status` so you understand the baseline state before processing.

## 3. Run the pipeline

Run the default command to validate the workbook, normalise field names, and produce a consolidated output file:

```bash
uv run hotpass --input-dir ./data --output-path ./dist/refined.xlsx --archive
```

The command performs these steps:

- Profiles each source workbook and reports data quality metrics.
- Harmonises column names using the active industry profile.
- Consolidates contact rows and resolves conflicts between sources.
- Generates Excel, CSV, and Parquet outputs when `--archive` is enabled.

## 4. Review the results

After the run completes, open the generated Excel file. You should see:

- A **Refined Data** worksheet with cleaned values and consistent formatting.
- A **Quality Summary** worksheet that highlights validation failures and remediation tips.
- Archived raw inputs under `dist/archive/` so you can trace data lineage.

To inspect logs programmatically, run the pipeline with JSON output:

```bash
uv run hotpass --archive --log-format json --log-level INFO
```

## 5. Extend the experience

Once you are comfortable with the basics, explore the advanced tutorial to orchestrate the pipeline and stream telemetry with Prefect and OpenTelemetry.

```{seealso}
The [Enhanced pipeline tutorial](./enhanced-pipeline.md) continues the journey by enabling orchestration, enrichment, and monitoring features.
```
