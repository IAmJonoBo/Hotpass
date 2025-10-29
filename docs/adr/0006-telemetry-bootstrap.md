# ADR-0006: Centralised telemetry bootstrap and exporter wiring

**Status:** Accepted

**Date:** 2025-12-02

## Context

OpenTelemetry support lived in several modules (`observability.py`, CLI commands, Prefect flows) and each location handled
provider initialisation, exporter selection, and shutdown independently. As a result:

1. CLI runs and Prefect deployments occasionally double-initialised providers, leaking metric readers and span processors.
2. Exporter support was limited to the console writer; operators needed OTLP exporters with configurable endpoints and headers.
3. Shutdown hooks were easy to miss, so telemetry buffers could remain unflushed when commands terminated via exceptions.
4. Tests had to monkeypatch internal globals, making it difficult to validate exporter lifecycle behaviour.

## Decision

We introduced a telemetry bootstrap layer that the CLI, Prefect flows, and tests share:

1. **Bootstrap options** — `TelemetryBootstrapOptions` models service metadata, exporter selections, and OTLP-specific settings.
   The helper normalises resource attributes and derives exporter configuration.
2. **Context manager** — `telemetry_session` wraps bootstrap initialisation in a context manager that always calls
   `shutdown_observability()` on exit. CLI commands (`hotpass run` / `hotpass orchestrate`) and Prefect flows now execute
   pipeline work within this context so exporter shutdown is guaranteed.
3. **Configuration schema** — `TelemetrySettings` gained OTLP endpoint, header, and timeout fields. CLI flags mirror these
   options via `--telemetry-*` switches and merge into the runtime configuration.
4. **Policy + registry updates** — The telemetry registry now allow-lists `otlp`, wires default OTLP factories, and exposes a
   safe exporter proxy to guard against `ValueError` from downstream libraries.
5. **Documentation & tests** — Observability docs describe the new CLI flags and bootstrap workflow. Unit tests cover
   `telemetry_session` shutdown semantics, telemetry option merging, and enhanced pipeline wiring.

## Consequences

### Positive

- Instrumentation is initialised exactly once per run and always shuts down cleanly.
- Operators can enable OTLP exporters from the CLI or Prefect parameters without bespoke scripts.
- Tests exercise exporter lifecycle behaviour through a shared context manager rather than fragile globals.

### Neutral

- CLI help now includes additional telemetry flags that operators must learn.
- Telemetry bootstrap introduces another dataclass that developers must populate when extending orchestration helpers.

### Negative

- OTLP exporter support requires the optional `opentelemetry-exporter-otlp-proto-grpc` dependency.
- Misconfigured exporter settings now surface earlier via policy validation, which may fail existing configurations until they
  supply service metadata.

## Alternatives considered

1. **Keep ad-hoc initialisation** — Rejected because it continued to duplicate shutdown logic and offered no path to OTLP.
2. **Rely solely on Prefect instrumentation** — Rejected since CLI runs would remain unauthenticated and exporter wiring would be
   inconsistent across entry points.
3. **Environment-variable configuration only** — Rejected to preserve explicit configuration in `HotpassConfig` and allow
   profile overrides.

## References

- `src/hotpass/telemetry/bootstrap.py`
- `src/hotpass/telemetry/registry.py`
- `src/hotpass/cli/commands/run.py`
- `src/hotpass/orchestration.py`
- `docs/observability/index.md`
