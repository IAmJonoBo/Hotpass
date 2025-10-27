---
title: Observability registry and policy
summary: Configure the Hotpass telemetry registry, exporter policies, and QA expectations.
last_updated: 2025-10-27
---

# Observability registry and policy

Hotpass now routes all tracing and metrics through a dedicated telemetry registry. The
registry centralises OpenTelemetry provider initialisation, exporter wiring, and shutdown
behaviour so the CLI, Prefect orchestrator, and unit tests share the same lifecycle hooks.

## Registry overview

- `hotpass.telemetry.registry.TelemetryRegistry` owns tracer/meter providers and exporter
  instances. Dependency injection allows tests to swap in lightweight stubs without
  touching global state.
- `hotpass.observability.initialize_observability` is a thin wrapper around the registry
  that the CLI and orchestrator call when `enable_observability` is set.
- `PipelineMetrics` moved to `hotpass.telemetry.metrics` and is created via the registry,
  ensuring histogram and counter instruments share the same meter instance.

The registry enforces a `TelemetryConfig` schema that requires a service name, environment,
and at least one exporter. By default Hotpass instantiates the safe console exporters that
were previously hand-rolled in `observability.py`.

## Configuration examples

### CLI (hotpass-enhanced orchestrate)

```bash
uv run hotpass-enhanced orchestrate \
  --profile aviation \
  --enable-observability
```

The CLI sets telemetry attributes for the selected profile and annotates each run with the
`hotpass.command=hotpass-enhanced orchestrate` tag. Exporters default to the console
wrapper and the registry uses `HOTPASS_ENVIRONMENT` (or `development`) for the environment
tag.

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

Only the safe console exporter ships out of the box. To add OTLP exporters in a custom
deployment, instantiate `TelemetryRegistry` with bespoke exporter factories and inject the
registry via `hotpass.observability.use_registry()`.

## Policy enforcement

`TelemetryPolicy` validates configuration before providers start:

- `service_name` must be non-empty.
- `environment` must resolve to a non-empty string (falls back to `HOTPASS_ENVIRONMENT`
  then `development`).
- Each requested exporter must be allow-listed. The default allow list includes
  `console` and `noop`.

Invalid configurations raise `ValueError` early so CI fails fast rather than attempting to
emit telemetry with missing metadata.

## QA expectations

Run the following checks before shipping telemetry changes:

```bash
uv run pytest tests/test_telemetry_registry.py tests/test_observability.py
uv run pytest --cov=src --cov=tests --cov-report=term-missing
uv run ruff check src/hotpass/observability.py src/hotpass/telemetry/
uv run mypy src/hotpass/telemetry src/hotpass/observability.py
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

