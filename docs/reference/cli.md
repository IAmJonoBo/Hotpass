---
title: Reference — command-line interface
summary: Detailed options for the unified `hotpass` CLI entry point and its subcommands.
last_updated: 2025-10-28
---

Hotpass now ships a single console script: `hotpass`. Subcommands map to the core
pipeline as well as orchestrator, entity resolution, dashboard, and deployment workflows.
Legacy `hotpass-enhanced` invocations continue to work but simply delegate to the unified
CLI after printing a deprecation warning.

## Quick start

```bash
uv run hotpass run --input-dir ./data --output-path ./dist/refined.xlsx --archive
```

Shared flags such as `--profile`, `--config`, `--log-format`, and `--sensitive-field`
may be supplied before the subcommand or repeated per subcommand thanks to the parser's
parent structure. Profiles defined in TOML or YAML load via `--profile` and can merge
additional configuration files and feature toggles.

## Canonical configuration schema

The CLI now materialises every run from the canonical `HotpassConfig` schema defined in
[`src/hotpass/config_schema.py`](../../src/hotpass/config_schema.py). Profiles, config files,
and CLI flags are normalised into that schema before any pipeline code executes, ensuring
consistent behaviour across CLI, Prefect flows, and agent-triggered runs.

```toml
# config/pipeline.canonical.toml
[profile]
name = "aviation"
display_name = "Aviation & Flight Training"

[pipeline]
input_dir = "./data"
output_path = "./dist/refined.xlsx"
archive = true
dist_dir = "./dist"
log_format = "json"

[features]
compliance = true
geospatial = true

[governance]
intent = ["Process POPIA regulated dataset"]
data_owner = "Data Governance"
classification = "sensitive_pii"

[compliance]
detect_pii = true

[data_contract]
dataset = "aviation_ssot"
expectation_suite = "aviation"
schema_descriptor = "ssot.schema.json"
```

Merge the file with `--config config/pipeline.canonical.toml` or place it under a CLI profile.
Legacy configuration payloads can be upgraded via the `ConfigDoctor` helper:

```python
from hotpass.config_doctor import ConfigDoctor

doctor = ConfigDoctor()
config, notices = doctor.upgrade_payload(legacy_payload)
doctor.diagnose()
doctor.autofix()
```

The doctor flags missing governance intent or data owners and injects safe defaults such as
`Data Governance` when autofixable.

## Shared options

| Option                                     | Description                                                                                                |
| ------------------------------------------ | ---------------------------------------------------------------------------------------------------------- |
| `--profile NAME`                           | Named profile (TOML/YAML) to apply before CLI flags.                                                       |
| `--profile-search-path PATH`               | Additional directory to search when resolving named profiles. Repeat the flag to merge multiple locations. |
| `--config FILE`                            | TOML or JSON configuration file merged before CLI flags. Repeat to layer multiple files.                   |
| `--log-format [rich \| json]`              | Structured logging format. Rich enables interactive output and progress bars.                              |
| `--sensitive-field FIELD`                  | Field name to mask in structured logs. Repeat for multiple masks.                                          |
| `--interactive` / `--no-interactive`       | Control inline prompts when rich logging is enabled.                                                       |
| `--qa-mode [default \| strict \| relaxed]` | Apply guardrail presets (strict enables additional validation; relaxed disables audit prompts).            |
| `--observability` / `--no-observability`   | Toggle OpenTelemetry exporters regardless of profile defaults.                                             |

## Subcommands

### `run`

Validate, normalise, and publish the refined workbook.

```bash
uv run hotpass run [OPTIONS]
```

| Option                                                                       | Description                                                                           |
| ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `--input-dir PATH`                                                           | Directory containing raw spreadsheets (default: `./data`).                            |
| `--output-path PATH`                                                         | Destination path for the refined workbook (default: `<input-dir>/refined_data.xlsx`). |
| `--expectation-suite NAME`                                                   | Great Expectations suite to execute (default: `default`).                             |
| `--country-code CODE`                                                        | ISO country code applied when normalising phone numbers (default: `ZA`).              |
| `--archive` / `--no-archive`                                                 | Enable or disable creation of a timestamped `.zip` archive.                           |
| `--dist-dir PATH`                                                            | Directory used for archive output when `--archive` is enabled (default: `./dist`).    |
| `--report-path PATH`                                                         | Optional path for the quality report (Markdown or HTML).                              |
| `--report-format [markdown \| html]`                                         | Explicit report format override. When omitted the format is inferred from the path.   |
| `--party-store-path PATH`                                                    | Path to serialise the canonical Party/Role/Alias/Contact store.                       |
| `--excel-chunk-size INTEGER`                                                 | Chunk size for streaming Excel reads; must be greater than zero when supplied.        |
| `--excel-engine TEXT`                                                        | Explicit pandas Excel engine (for example `openpyxl`).                                |
| `--excel-stage-dir PATH`                                                     | Directory for staging chunked Excel reads to parquet for reuse.                       |
| `--automation-http-timeout FLOAT`                                            | Timeout in seconds for webhook and CRM deliveries.                                    |
| `--automation-http-retries INTEGER`                                          | Maximum retry attempts for automation deliveries.                                     |
| `--automation-http-backoff FLOAT`                                            | Exponential backoff factor applied between automation retries.                        |
| `--automation-http-backoff-max FLOAT`                                        | Upper bound for the backoff interval (seconds).                                       |
| `--automation-http-circuit-threshold INTEGER`                                | Consecutive failures that open the automation circuit breaker.                        |
| `--automation-http-circuit-reset FLOAT`                                      | Seconds to wait before half-opening the automation circuit.                           |
| `--automation-http-idempotency-header TEXT`                                  | Override the `Idempotency-Key` header when generating idempotency keys.               |
| `--automation-http-dead-letter PATH`                                         | Append failed automation payloads to the given NDJSON file.                           |
| `--automation-http-dead-letter-enabled` / `--no-automation-http-dead-letter` | Toggle dead-letter persistence for automation failures.                               |

### `orchestrate`

Execute the pipeline under Prefect with optional enhanced features.

```bash
uv run hotpass orchestrate [OPTIONS]
```

| Option                                                       | Description                                                                   |
| ------------------------------------------------------------ | ----------------------------------------------------------------------------- |
| `--industry-profile NAME`                                    | Prefect profile used when loading orchestrator presets (default: `aviation`). |
| `--enable-all`                                               | Enable all enhanced features in one flag.                                     |
| `--enable-entity-resolution` / `--disable-entity-resolution` | Control probabilistic entity resolution.                                      |
| `--enable-geospatial` / `--disable-geospatial`               | Control geospatial enrichment (geocoding).                                    |
| `--enable-enrichment` / `--disable-enrichment`               | Control web enrichment workflows.                                             |
| `--enable-compliance` / `--disable-compliance`               | Control compliance tracking and PII detection.                                |
| `--enable-observability` / `--disable-observability`         | Control observability exporters during orchestrated runs.                     |
| `--linkage-match-threshold FLOAT`                            | Probability considered an automatic match (default: `0.9`).                   |
| `--linkage-review-threshold FLOAT`                           | Probability routed to human review (default: `0.7`).                          |
| `--linkage-output-dir PATH`                                  | Directory to persist linkage artefacts.                                       |
| `--linkage-use-splink`                                       | Force Splink for probabilistic linkage even when profiles disable it.         |
| `--label-studio-url URL`                                     | Label Studio base URL for review queues.                                      |
| `--label-studio-token TOKEN`                                 | Label Studio API token.                                                       |
| `--label-studio-project INTEGER`                             | Label Studio project identifier.                                              |

Profiles enabling enrichment or compliance must declare intent statements (`intent = [...]`) to
enforce guardrails such as consent capture and audit logging.

### `resolve`

Deduplicate existing datasets using rule-based or probabilistic linkage.

```bash
uv run hotpass resolve --input-file data/raw.xlsx --output-file data/deduplicated.xlsx
```

| Option                             | Description                                                                                      |
| ---------------------------------- | ------------------------------------------------------------------------------------------------ |
| `--input-file PATH`                | Source CSV or Excel file with potential duplicates.                                              |
| `--output-file PATH`               | Destination path for deduplicated results.                                                       |
| `--threshold FLOAT`                | Baseline match probability threshold (default: `0.75`).                                          |
| `--use-splink` / `--no-use-splink` | Toggle Splink for probabilistic matching. Profiles enabling entity resolution default to `True`. |
| `--match-threshold FLOAT`          | Threshold treated as an automatic match (default: `0.9`).                                        |
| `--review-threshold FLOAT`         | Threshold that routes pairs to human review (default: `0.7`).                                    |
| `--label-studio-url URL`           | Label Studio base URL for review queues.                                                         |
| `--label-studio-token TOKEN`       | Label Studio API token.                                                                          |
| `--label-studio-project INTEGER`   | Label Studio project identifier.                                                                 |

### `deploy`

Create or update Prefect deployments for the refinement pipeline.

```bash
uv run hotpass deploy --name hotpass-refinement --schedule "0 2 * * *"
```

| Option             | Description                                                |
| ------------------ | ---------------------------------------------------------- |
| `--name TEXT`      | Prefect deployment name (default: `hotpass-refinement`).   |
| `--schedule CRON`  | Optional cron schedule (`"0 2 * * *"` for daily at 02:00). |
| `--work-pool TEXT` | Prefect work pool name.                                    |

### `dashboard`

Launch the Streamlit monitoring dashboard. Install the `dashboards` extra before using this
subcommand.

```bash
uv run hotpass dashboard --host localhost --port 8501
```

| Option           | Description                                                   |
| ---------------- | ------------------------------------------------------------- |
| `--host HOST`    | Bind address for the dashboard server (default: `localhost`). |
| `--port INTEGER` | Port for the Streamlit dashboard (default: `8501`).           |

### Automation delivery environment variables

The CLI and Prefect flows read the following environment variables when CLI flags are not
provided. All values are optional.

| Variable                                      | Purpose                                                     |
| --------------------------------------------- | ----------------------------------------------------------- |
| `HOTPASS_AUTOMATION_HTTP_TIMEOUT`             | Override the automation timeout (seconds).                  |
| `HOTPASS_AUTOMATION_HTTP_RETRIES`             | Override the retry count.                                   |
| `HOTPASS_AUTOMATION_HTTP_BACKOFF`             | Override the backoff factor.                                |
| `HOTPASS_AUTOMATION_HTTP_BACKOFF_MAX`         | Override the maximum backoff interval (seconds).            |
| `HOTPASS_AUTOMATION_HTTP_CIRCUIT_THRESHOLD`   | Override the failure threshold before the circuit opens.    |
| `HOTPASS_AUTOMATION_HTTP_CIRCUIT_RESET`       | Override the circuit recovery window (seconds).             |
| `HOTPASS_AUTOMATION_HTTP_IDEMPOTENCY_HEADER`  | Override the idempotency header name.                       |
| `HOTPASS_AUTOMATION_HTTP_DEAD_LETTER`         | Write failed deliveries to the specified NDJSON file.       |
| `HOTPASS_AUTOMATION_HTTP_DEAD_LETTER_ENABLED` | Enable or disable dead-letter persistence (`true`/`false`). |

## Exit codes

| Code | Meaning                                                                         |
| ---- | ------------------------------------------------------------------------------- |
| `0`  | Success.                                                                        |
| `1`  | Unrecoverable failure (for example missing input files, orchestration failure). |
| `2`  | Validation failure when loading profiles or configuration.                      |

## See also

- [How-to guide — orchestrate and observe](../how-to-guides/orchestrate-and-observe.md)
- [How-to guide — configure pipeline](../how-to-guides/configure-pipeline.md)
- [Tutorial — enhanced pipeline](../tutorials/enhanced-pipeline.md)
