---
title: Observability registry and policy
summary: Configure the Hotpass telemetry bootstrap, exporter policies, and QA expectations.
last_updated: 2025-12-02
---

Hotpass now routes all tracing and metrics through a dedicated telemetry bootstrap layer.
The bootstrap centralises OpenTelemetry provider initialisation, exporter wiring, and
shutdown behaviour so the CLI, Prefect orchestrator, and unit tests share the same
lifecycle hooks. Both CLI entry points and Prefect flows call the shared
`telemetry_session` context manager to ensure exporter shutdown always runs, even when
exceptions bubble up.

## Registry overview

- `hotpass.telemetry.registry.TelemetryRegistry` owns tracer/meter providers and exporter
  instances. Dependency injection allows tests to swap in lightweight stubs without
  touching global state.
- `hotpass.telemetry.bootstrap.telemetry_session` is the canonical way to initialise and
  shut down telemetry. The CLI and Prefect flows wrap pipeline execution inside this
  context to guarantee exporters flush on exit.
- `hotpass.observability.initialize_observability` remains a thin wrapper around the
  registry and is used by lower-level helpers that need direct tracer/meter references.
- `PipelineMetrics` moved to `hotpass.telemetry.metrics` and is created via the registry,
  ensuring histogram and counter instruments share the same meter instance.

The registry enforces a `TelemetryConfig` schema that requires a service name, environment,
and at least one exporter. By default Hotpass instantiates the safe console exporters that
were previously hand-rolled in `observability.py`.

## Lineage exploration

Hotpass ships a Docker Compose stack for [Marquez](marquez.md) so you can visualise the
OpenLineage events emitted by CLI runs and Prefect deployments. Launch the stack during
local development to confirm datasets, jobs, and runs are captured end-to-end.

## Configuration examples

### CLI (hotpass run / hotpass orchestrate)

```bash
uv run hotpass run \
  --input-dir ./data \
  --output-path ./dist/refined.xlsx \
  --enable-observability \
  --telemetry-exporter otlp \
  --telemetry-otlp-endpoint grpc://collector:4317 \
  --telemetry-otlp-header Authorization="Bearer 123" \
  --telemetry-resource-attr deployment=staging
```

The CLI sets telemetry attributes for the selected profile and annotates each run with
`hotpass.command` (`hotpass run` or `hotpass orchestrate`). Exporters default to the
console wrapper, but the new `--telemetry-exporter` flag enables OTLP alongside console or
noop exporters. Endpoint, headers, and timeout flags map directly to the registry's OTLP
settings and are safe to leave unset when publishing solely to the console.

### Prefect deployments

Prefect flows call `run_enhanced_pipeline` with `enable_observability=True`. Pass
additional attributes via `EnhancedPipelineConfig.telemetry_attributes`, e.g.:

```python
EnhancedPipelineConfig(
    enable_observability=True,
    telemetry_attributes={
        "deployment.environment": "prod",
        "hotpass.profile": "aviation",
        "prefect.work_pool": work_pool_name,
    },
)
```

### Custom exporters

Console exporters remain the default, but OTLP exporters are now included out of the box.
To integrate with additional back-ends, instantiate `TelemetryRegistry` with bespoke
exporter factories and inject the registry via `hotpass.observability.use_registry()`.
Any CLI-specified exporter name must be allow-listed by the registry policy before it can
be used.

## Policy enforcement

`TelemetryPolicy` validates configuration before providers start:

- `service_name` must be non-empty.
- `environment` must resolve to a non-empty string (falls back to `HOTPASS_ENVIRONMENT`
  then `development`).
- Each requested exporter must be allow-listed. The default allow list includes
  `console`, `noop`, and `otlp`.

Invalid configurations raise `ValueError` early so CI fails fast rather than attempting to
emit telemetry with missing metadata.

## QA expectations

Run the following checks before shipping telemetry changes:

```bash
uv run pytest tests/test_telemetry_registry.py tests/test_observability.py
uv run pytest --cov=src --cov=tests --cov-report=term-missing
uv run ruff check apps/data-platform/hotpass/observability.py apps/data-platform/hotpass/telemetry/
uv run mypy apps/data-platform/hotpass/telemetry apps/data-platform/hotpass/observability.py
```

Add new exporters through dedicated tests that cover lifecycle hooks (`shutdown`), policy
validation, and integration with `pipeline_stage` spans.

## Troubleshooting

- **Missing exporters** — confirm the exporter name is in the registry's allowed set and
  the corresponding OpenTelemetry dependency is installed.
- **Telemetry disabled in tests** — use `hotpass.observability.use_registry` to inject the
  shared stub registry defined in `tests/_telemetry_stubs.py`.
- **Hanging shutdown** — ensure `shutdown_observability()` runs in `finally` blocks when
  instrumented CLIs exit to flush readers.
