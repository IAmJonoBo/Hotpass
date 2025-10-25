---
title: Reference — command-line interface
summary: Detailed options for the `hotpass` and `hotpass-enhanced` CLI entry points.
last_updated: 2025-10-25
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
| `--output-path PATH` | Target Excel file (default: `./dist/refined.xlsx`). |
| `--config FILE` | YAML configuration file that overrides CLI flags. |
| `--archive / --no-archive` | Retain raw inputs and emit CSV/Parquet alongside Excel. |
| `--log-format [rich|json]` | Structured log output. |
| `--log-level LEVEL` | Logging level (default: `INFO`). |
| `--profile NAME` | Industry profile to load (default: `aviation`). |

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

### Exit codes

- `0`: success.
- `1`: unrecoverable failure.
- `2`: validation failure (check the quality report).

Refer to the [pipeline configuration guide](../how-to-guides/configure-pipeline.md) for environment-specific setup.
