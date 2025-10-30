---
title: Explanation — architecture overview
summary: High-level view of Hotpass components and how data flows between them.
last_updated: 2025-10-30
---

Hotpass ingests spreadsheet workbooks and orchestrated research crawlers, applies cleaning, backfilling, relationship mapping, validation, and enrichment logic, and emits governed, analysis-ready outputs. The platform is composed of the following layers.

## Architecture views

Download the Structurizr DSL workspace in [docs/architecture/hotpass-architecture.dsl](../architecture/hotpass-architecture.dsl). The workspace defines:

- A **context view** that captures Hotpass, its operators, Prefect, observability sinks, and enrichment systems.
- A **container view** that highlights the execution boundary (CLI, Prefect workers, and file-system stores) alongside the Streamlit dashboard and external dependencies.
- A **component view** that drills into the pipeline engine and shows how ingestion, mapping, validation, enrichment, and formatting modules collaborate.

Render the diagrams locally with [Structurizr Lite](https://docs.structurizr.com/lite):

```bash
docker run --rm -p 8080:8080 -v "$(pwd)/docs/architecture:/workspace" structurizr/lite
```

Then open `http://localhost:8080` and load `hotpass-architecture.dsl`.

## 1. Ingestion

- **CLI and orchestration**: Users trigger runs via the CLI or Prefect deployments.
- **Profiles**: YAML-defined industry profiles provide configuration for synonyms, validation thresholds, and contact preferences.
- **Data loaders**: Parsers convert Excel, CSV, and Parquet into Pandas dataframes while preserving lineage metadata.

## 2. Processing

- **Column mapping**: Fuzzy matching and synonym dictionaries align source headers with canonical fields.
- **Entity resolution**: Splink-based duplicate detection merges overlapping organisations with deterministic fallbacks.
- **Validation**: Great Expectations suites ensure data quality and compliance with POPIA.
- **Enrichment**: Optional connectors add registry data, scraped insights, and geospatial coordinates.

The pipeline runtime has been modularised so each stage now lives in a focused module:

- `pipeline.ingestion` handles source loading, acquisition plans, slug generation, and initial PII redaction.
- `pipeline.aggregation` encapsulates canonicalisation, conflict tracking, and per-record scoring logic.
- `pipeline.validation` runs schema checks and expectation suites, returning concise validation results.
- `pipeline.export` owns persistence concerns (Excel/CSV/Parquet, DuckDB ordering, daily lists, intent digests).
- `pipeline.config` defines the shared dataclasses (`PipelineConfig`, `PipelineResult`, `QualityReport`, `SSOT_COLUMNS`).

`pipeline.base` now orchestrates these modules, keeping telemetry, audit, and metrics coordination without housing the implementation details. The component view in Structurizr reflects this split so downstream services can reason about extension points per stage.

## 3. Output

- **Formatter**: Produces Excel workbooks with consistent styling, plus CSV and Parquet exports. The storage layer now relies on `hotpass.storage.PolarsDataset` backed by DuckDB adapters so parquet snapshots remain Arrow-native while serving DuckDB SQL queries for deterministic ordering.
- **Quality report**: Generates JSON and Markdown reports summarising validation outcomes.
- **Observability**: Emits Prefect task logs and OpenTelemetry metrics for pipeline health monitoring. Each run wraps the ingest, canonicalise, validate, link, and publish stages in OpenTelemetry spans so Prefect and Streamlit dashboards surface end-to-end timings without bespoke instrumentation.

## 4. Supporting services

- **Dashboard**: Streamlit app visualises run history, validation failures, and enrichment coverage in real time.
- **Configuration doctor**: Diagnoses missing dependencies, misconfigured profiles, and schema drift.
- **Benchmarks**: Performance benchmarks guard against regressions in core operations.

The architecture emphasises modularity—each layer can be extended independently without disrupting the pipeline contract. See the [platform scope explanation](./platform-scope.md) for upcoming investments.

## Trust boundaries

### Runner and worker boundary

- Covers the CLI (`hotpass.cli`), Prefect flows (`hotpass.orchestration`), and pipeline engine modules that run wherever operators execute `uv run hotpass` or Prefect schedules a deployment.
- Protects file-system backed stores under `data/`, `dist/`, and `logs/`. These hold raw uploads, refined exports, and audit artefacts respectively and are tagged as critical assets in the diagrams.
- Docker images (see [`Dockerfile`](../../Dockerfile)) default to running the CLI as a non-root `appuser`. Harden the container runtime by mounting read-only secrets and using volume mounts for input/output stores.

### Dashboard boundary

- Encapsulates the Streamlit UI (`hotpass.dashboard`) that imports pipeline code directly. Runs on an operator workstation or inside a separate container with access to the same file-system stores.
- Needs strict CORS and authentication if exposed beyond an internal network. At present the app trusts local filesystem access and in-memory session state.

### External service boundary

- Prefect Orion or Cloud invokes the flow via work pools. Prefect credentials and service accounts must be scoped to read/write only the required deployment.
- OpenTelemetry exporters (`hotpass.observability`) push spans and metrics to a collector endpoint. Configure endpoint URLs and authentication via environment variables, and ensure TLS enforcement in shared environments.
- Enrichment connectors (`hotpass.enrichment`) call public registries or web endpoints through `requests` and `trafilatura`. When productionising registry integrations, provide API keys or OAuth tokens via secrets managers rather than embedding them in profiles.

## Critical assets and attack surfaces

- **Raw spreadsheets and archives** (`data/`, `dist/`): Store personally identifiable information (PII) such as contact details. Restrict filesystem permissions and consider at-rest encryption for shared volumes.
- **Quality reports and audit trails** (`logs/`, Markdown/JSON exports): Contain compliance evidence and failure diagnostics. Tampering undermines POPIA reporting obligations.
- **Prefect deployment credentials**: Compromise lets attackers exfiltrate data or run malicious code through the pipeline workers. Rotate tokens and confine network egress on worker hosts.
- **Telemetry streams**: OpenTelemetry exporters can leak data if collectors are multi-tenant. Limit attribute payloads to avoid exporting PII, and monitor collector ACLs.
- **Enrichment HTTP calls**: Attackers controlling upstream registries or intercepting traffic can inject malicious content. Enable HTTPS, validate schemas, and sanitise text scraped by `trafilatura` before persistence.

## Single points of failure

- **Local filesystem stores**: The pipeline currently writes to local directories. Use resilient shared storage or object stores when scaling beyond a single host.
- **Prefect work pool**: A single Prefect worker triggers runs. Add redundant workers or fall back to cron/CLI automation if Prefect is unavailable.
- **External registries**: Enrichment is optional, but when enabled it depends on upstream availability. Implement caching (`redis` extra) and graceful degradation for long outages.
- **OpenTelemetry console exporters**: Even with safe emitters, unresponsive collectors can stall shutdown. Configure batching timeouts and consider disabling exporters in air-gapped sites.

## Unknowns and follow-up questions

- **Authentication for the dashboard**: Shared-secret password gate now protects local deployments; determine if SSO-backed auth and centralised session logging are required before exposing beyond trusted operators.
- **Secrets management**: Clarify the target mechanism (Prefect blocks, environment variables, vault) for registry API credentials and telemetry endpoints.
- **CI artefact handling**: The GitHub Actions workflow publishes refined datasets to a `data-artifacts` branch. Validate retention requirements and access controls with stakeholders.
- **Docker image distribution**: The current Dockerfile builds the CLI but CI does not yet push images. Confirm if container registries or air-gapped deployments are in scope.
