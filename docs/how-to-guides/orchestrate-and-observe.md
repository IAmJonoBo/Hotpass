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
uv run hotpass-enhanced deploy \
  --name hotpass-prod \
  --profile aviation \
  --schedule "0 2 * * *" \
  --concurrency-limit 1
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

## Toggle Prefect runtime decorators

During unit tests Hotpass disables Prefect's runtime decorators to avoid starting ephemeral
servers. Set `HOTPASS_ENABLE_PREFECT_RUNTIME=1` before invoking CLI or Prefect commands when
you need the real Prefect runtime behaviour:

```bash
export HOTPASS_ENABLE_PREFECT_RUNTIME=1
uv run hotpass-enhanced orchestrate --profile aviation
```

Unset the variable (or leave it blank) to fall back to the no-op decorators that keep local
unit tests offline-friendly.

## Enable telemetry

Set the exporter variables before triggering a run:

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="https://otel.example.com"
export OTEL_EXPORTER_OTLP_HEADERS="Authorization=Bearer <token>"
export PREFECT_LOGGING_EXTRA_LOGGERS="hotpass,hotpass.enrichment"
```

Then run the orchestrated pipeline:

```bash
uv run hotpass-enhanced orchestrate --profile aviation --enable-observability
```

Use the Prefect UI or the OTLP backend (Grafana, Datadog, etc.) to verify metrics such as `hotpass.pipeline.duration`, `hotpass.validation.failures`, and `hotpass.enrichment.coverage`.

## Troubleshooting

- **Missing extras**: `ModuleNotFoundError` for Prefect or OpenTelemetry means the extras were not installed. Re-run `uv sync` with the required extras.
- **Telemetry write errors**: When running offline, set `OTEL_EXPORTER_OTLP_PROTOCOL=console` to avoid network timeouts.
- **Flow concurrency**: Prefect limits concurrency per work pool. Adjust `--concurrency-limit` or use work-queue level settings.

```{seealso}
Refer to the [Enhanced pipeline tutorial](../tutorials/enhanced-pipeline.md) for an end-to-end walkthrough that includes enrichment and dashboarding.
```
