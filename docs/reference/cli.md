---
title: Reference — command-line interface
summary: Detailed options for the `hotpass` and `hotpass-enhanced` CLI entry points.
last_updated: 2025-10-26
---

# Reference — command-line interface

Hotpass exposes two console scripts. Use `hotpass` for the base pipeline and `hotpass-enhanced` when you need orchestration or enrichment extras.

## `hotpass`

```bash
uv run hotpass [OPTIONS]
```

| Option | Description |
| --- | --- |
| `--input-dir PATH` | Directory containing raw spreadsheets (default: `./data`). |
| `--output-path PATH` | Destination path for the refined workbook (default: `<input-dir>/refined_data.xlsx`). |
| `--config FILE` | TOML or JSON configuration file applied before CLI flags. Repeat the flag to merge multiple files. |
| `--country-code TEXT` | ISO country code used when normalising phone numbers (default: `ZA`). |
| `--expectation-suite TEXT` | Great Expectations suite to execute (default: `default`). |
| `--archive` / `--no-archive` | Enable or disable creation of a timestamped `.zip` archive that bundles the refined workbook. |
| `--dist-dir PATH` | Directory used for archive output when `--archive` is enabled (default: `./dist`). |
| `--log-format [rich &#124; json]` | Structured log format for pipeline output (default: `rich`). |
| `--interactive` / `--no-interactive` | Control whether the CLI prompts to review recommendations when using rich output (default: auto-detect). |
| `--sensitive-field FIELD` | Field name to redact from structured logs. Repeat to mask multiple fields. Default redactions cover `email`, `phone`, `contact`, `cell`, `mobile`, and `whatsapp`. |
| `--report-path PATH` | Optional path to write the quality report (Markdown or HTML). |
| `--report-format [markdown &#124; html]` | Explicit report format override. When omitted the format is inferred from `--report-path`. |
| `--party-store-path PATH` | Path to write the canonical Party/Role/Alias/Contact store as JSON. |
| `--excel-chunk-size INTEGER` | Chunk size for streaming Excel sheets; must be greater than zero when provided. |
| `--excel-engine TEXT` | Explicit pandas Excel engine (for example `openpyxl`). |
| `--excel-stage-dir PATH` | Directory for staging chunked Excel reads to parquet for reuse. |


Structured JSON logs replace masked fields with `***redacted***` using the default sensitive field list above. Add additional masks by repeating `--sensitive-field` or set the list in a configuration file (`sensitive_fields = ["passport", "id_number"]`). When the list is empty the CLI emits full payloads for downstream debugging.

When running with rich output the CLI streams stage-aware progress updates covering load, aggregation, validation, and write phases. Interactive sessions prompt operators to review the top recommendations inline once the run completes.

When `--party-store-path` is provided the CLI serialises the canonical Party/Role/Alias/Contact store as JSON. Pair this artefact with the generated data dictionary (see below) to hand off structured metadata to downstream teams.

## `hotpass-enhanced`

```bash
uv run hotpass-enhanced COMMAND [OPTIONS]
```

### `orchestrate`

Runs the enriched pipeline with optional extras.

Key flags:

- `--enable-entity-resolution`
- `--enable-geospatial`
- `--enable-enrichment`
- `--enable-compliance`
- `--enable-observability`
- `--enable-all`

Combine them to activate integrations incrementally.

### `resolve`

Deduplicate records using Splink or fallback slug matching.

```bash
uv run hotpass-enhanced resolve \
  --input-file data/raw.xlsx \
  --output-file data/deduplicated.xlsx \
  --threshold 0.8 \
  --use-splink
```

### `deploy`

Registers a Prefect deployment.

```bash
uv run hotpass-enhanced deploy \
  --name hotpass-prod \
  --profile aviation \
  --schedule "0 2 * * *"
```

### `dashboard`

Launches the Streamlit monitoring dashboard.

```bash
uv run hotpass-enhanced dashboard --port 8501
```

Configure runtime controls with environment variables:

- `HOTPASS_DASHBOARD_PASSWORD` — shared secret required before operators can execute the pipeline through the dashboard. Omit the variable to run in unsecured local-only mode.
- `HOTPASS_DASHBOARD_ALLOWED_ROOTS` — list of allowed directories (separated by the platform path separator, e.g. `:` on Linux/macOS, `;` on Windows). Input and output selections must resolve within these roots. Defaults to `./data`, `./dist`, and `./logs` when unset.

### Exit codes

- `0`: success.
- `1`: unrecoverable failure.
- `2`: validation failure (check the quality report).

Refer to the [pipeline configuration guide](../how-to-guides/configure-pipeline.md) for environment-specific setup.

## Canonical data dictionary

Generate the Hotpass data dictionary with the helper script:

```bash
uv run python scripts/catalog/generate_dictionary.py \
  --output dist/catalog/hotpass_data_dictionary.md
```

Link the resulting Markdown file alongside the party-store export produced by `--party-store-path` so consumers can cross-reference entity attributes and provenance metadata.
