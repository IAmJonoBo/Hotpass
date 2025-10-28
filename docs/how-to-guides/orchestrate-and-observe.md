---
title: How-to — orchestrate and observe Hotpass runs
summary: Configure Prefect deployments and OpenTelemetry exporters for continuous Hotpass operations.
last_updated: 2025-10-26
---

# How-to — orchestrate and observe Hotpass runs

Use this guide when you need to promote Hotpass from ad-hoc execution to a scheduled, observable service.

## Before you begin

- Install Hotpass with the `orchestration`, `enrichment`, `geospatial`, `compliance`, and `dashboards` extras.
- Provision a Prefect work pool and API key.
- Decide where you want to ship telemetry (stdout, OTLP endpoint, or another backend).

## Create a deployment

```bash
uv run hotpass deploy \
  --name hotpass-prod \
  --profile aviation \
  --schedule "0 2 * * *"
```

The deployment packages the repository, registers it with Prefect, and schedules nightly runs. Use the `--tag` flag to group deployments by environment.

## Manage secrets and configuration

1. Store credentials such as database URLs and API keys as Prefect blocks or environment variables.
2. Reference them from the pipeline config using Jinja templating:

```yaml
datasources:
  crm:
    type: postgres
    dsn: "{{ env_var('CRM_DSN') }}"
```

3. Update the Prefect deployment to pull secrets at runtime:

```bash
uv run prefect deployment run hotpass-prod --params '{"refresh_contacts": true}'
```

## Review probabilistic linkage

Hotpass now persists probabilistic linkage scores and review queues when you
enable entity resolution. Configure thresholds and the review location when
invoking the enhanced orchestrator:

```bash
uv run hotpass orchestrate \
  --profile aviation \
  --enable-entity-resolution \
  --linkage-use-splink \
  --linkage-match-threshold 0.92 \
  --linkage-review-threshold 0.7 \
  --linkage-output-dir dist/linkage \
  --label-studio-url https://labelstudio.example \
  --label-studio-token $LABEL_STUDIO_TOKEN \
  --label-studio-project 12
```

Each run writes the following artefacts under the configured output directory
(default: `dist/linkage/`):

- `linkage_matches.parquet` — scored pairs above the reject threshold.
- `linkage_review_queue.parquet` — pairs routed to clerical review.
- `linkage_metadata.json` — thresholds and record counts for retraining.
- `linkage_reviewer_decisions.jsonl` — reviewer feedback synced from Label Studio.

Label Studio tasks include both the match probability and the configured
thresholds so reviewers understand why a pair requires attention.

## Toggle Prefect runtime decorators

During unit tests Hotpass disables Prefect's runtime decorators to avoid starting ephemeral
servers. Set `HOTPASS_ENABLE_PREFECT_RUNTIME=1` before invoking CLI or Prefect commands when
you need the real Prefect runtime behaviour:

```bash
export HOTPASS_ENABLE_PREFECT_RUNTIME=1
uv run hotpass orchestrate --profile aviation
```

Unset the variable (or leave it blank) to fall back to the no-op decorators that keep local
unit tests offline-friendly.

## Enable telemetry

Set the exporter variables before triggering a run. The CLI now routes telemetry through the
shared registry described in [Observability registry and policy](../observability/index.md):

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="https://otel.example.com"
export OTEL_EXPORTER_OTLP_HEADERS="Authorization=Bearer <token>"
export PREFECT_LOGGING_EXTRA_LOGGERS="hotpass,hotpass.enrichment"
```

Then run the orchestrated pipeline:

```bash
uv run hotpass orchestrate --profile aviation --enable-observability
```

Use the Prefect UI or the OTLP backend (Grafana, Datadog, etc.) to verify metrics such as `hotpass.pipeline.duration`, `hotpass.validation.failures`, and `hotpass.enrichment.coverage`. When
customising exporters, inject a bespoke `TelemetryRegistry` via `hotpass.observability.use_registry`
and include a call to `shutdown_observability()` in CLI scripts to flush readers.

## Replay archived inputs with Prefect backfills

Fill historical gaps by replaying archived spreadsheets through the pipeline. The `backfill` command
rehydrates zipped inputs, honours concurrency guardrails, and emits the same metrics that scheduled
runs produce.

1. Store archives in a predictable directory (for example, `dist/input-archives/`).
2. Name bundles consistently such as `hotpass-inputs-YYYYMMDD-v{version}.zip` or adjust the
   `orchestrator.backfill.archive_pattern` setting to match your layout.
3. Execute the backfill command, overriding dates or versions as required:

```bash
uv run hotpass backfill \
  --config configs/prod.json \
  --start-date 2024-01-01 \
  --end-date 2024-01-03 \
  --version v1 \
  --version v2 \
  --archive-root /data/hotpass/input-archives \
  --restore-root /tmp/hotpass/backfill
```

Each run extracts to `<restore-root>/YYYY-MM-DD--version/`, writes refined workbooks under
`<restore-root>/outputs/`, and reports summary metrics to Prefect. Concurrency is governed by the
canonical configuration (`orchestrator.backfill.concurrency_limit` and `concurrency_key`), aligning
with the operational guardrails described in [Prefect governance](../governance/pr-playbook.md#prefect-deployments).
Setting `concurrency_limit` to `0` or leaving Prefect unavailable forces sequential execution, and the
flow automatically falls back to synchronous runs if Prefect cannot acquire slots—useful for CI or
air-gapped environments.

## Troubleshooting

- **Missing extras**: `ModuleNotFoundError` for Prefect or OpenTelemetry means the extras were not installed. Re-run `uv sync` with the required extras.
- **Telemetry write errors**: When running offline, set `OTEL_EXPORTER_OTLP_PROTOCOL=console` to avoid network timeouts.
- **Flow concurrency**: Prefect limits concurrency per work pool. Adjust `--concurrency-limit` or use work-queue level settings.

```{seealso}
Refer to the [Enhanced pipeline tutorial](../tutorials/enhanced-pipeline.md) for an end-to-end walkthrough that includes enrichment and dashboarding.
```
