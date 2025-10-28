---
title: Reference — repository inventory
summary: Snapshot of Hotpass packages, interfaces, orchestration flows, tests, datasets, and CI automation.
last_updated: 2025-10-30
---

This inventory highlights the moving parts that power Hotpass. Use the tables below to
jump to the relevant code, fixtures, or automation when you need to trace behaviour or
extend the platform.

## Packages and modules

| Area                      | Description                                                                                                                                       | Key entry points                                                                                                                                                                                                                |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Pipeline execution        | Core orchestration, configuration, and reporting for the refinement pipeline, including ingestion, aggregation, validation, and publishing logic. | [`src/hotpass/pipeline/`](../../src/hotpass/pipeline/) · [`pipeline_enhanced.py`](../../src/hotpass/pipeline_enhanced.py) · [`pipeline_reporting.py`](../../src/hotpass/pipeline_reporting.py) |
| Automation delivery       | Circuit breakers, retry-aware HTTP client, and webhook/CRM hooks for downstream automation.                                                       | [`src/hotpass/automation/`](../../src/hotpass/automation/)                                                                                                                                                           |
| Enrichment services       | Intent collectors, validators, and provider adapters for enrichment extras.                                                                       | [`src/hotpass/enrichment/`](../../src/hotpass/enrichment/)                                                                                                                                                           |
| Entity resolution         | Probabilistic linkage runner plus Splink integration.                                                                                             | [`src/hotpass/linkage/`](../../src/hotpass/linkage/) · [`entity_resolution.py`](../../src/hotpass/entity_resolution.py)                                                                                   |
| Transform & scoring       | Feature engineering, scoring, and transformation helpers.                                                                                         | [`src/hotpass/transform/`](../../src/hotpass/transform/) · [`transform/scoring.py`](../../src/hotpass/transform/scoring.py)                                                                               |
| Domain models             | Typed representations of contacts, organisations, telemetry payloads, and shared enums.                                                           | [`src/hotpass/domain/`](../../src/hotpass/domain/)                                                                                                                                                                   |
| Data access               | Data source adapters and persistence abstractions (Excel, parquet, Polars datasets).                                                              | [`src/hotpass/data_sources/`](../../src/hotpass/data_sources/) · [`src/hotpass/storage/`](../../src/hotpass/storage/)                                                                                     |
| Configuration & profiles  | Canonical config schema, upgrade helpers, and reusable profile presets.                                                                           | [`config_schema.py`](../../src/hotpass/config_schema.py) · [`config_doctor.py`](../../src/hotpass/config_doctor.py) · [`profiles/`](../../src/hotpass/profiles/)                               |
| CLI surface               | Unified CLI, progress logging, and enhanced compatibility shim.                                                                                   | [`cli/`](../../src/hotpass/cli/) · [`cli_enhanced.py`](../../src/hotpass/cli_enhanced.py)                                                                                                                 |
| Compliance & validation   | POPIA/ISO evidence logging, PIIs redaction, schema + expectation gates.                                                                           | [`compliance.py`](../../src/hotpass/compliance.py) · [`compliance_verification.py`](../../src/hotpass/compliance_verification.py) · [`validation.py`](../../src/hotpass/validation.py)         |
| Observability & telemetry | Metric exporters, OpenTelemetry wiring, and structured logging helpers.                                                                           | [`telemetry/`](../../src/hotpass/telemetry/) · [`observability.py`](../../src/hotpass/observability.py)                                                                                                   |

## Console scripts

| Script             | Module                                                                      | Purpose                                                                                       |
| ------------------ | --------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `hotpass`          | [`hotpass.cli:main`](../../src/hotpass/cli/main.py)              | Unified CLI for running the pipeline, orchestrations, deployments, dashboards, and tooling.   |
| `hotpass-enhanced` | [`hotpass.cli_enhanced:main`](../../src/hotpass/cli_enhanced.py) | Backwards-compatible entry point that delegates to the unified CLI with deprecation warnings. |

## Prefect flows

| Flow name                     | Definition                                                                  | Highlights                                                                                                              |
| ----------------------------- | --------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `hotpass-backfill`            | [`backfill_pipeline_flow`](../../src/hotpass/orchestration.py)   | Rehydrates archived inputs, reruns the pipeline for historical windows, and aggregates metrics with concurrency guards. |
| `hotpass-refinement-pipeline` | [`refinement_pipeline_flow`](../../src/hotpass/orchestration.py) | Primary Prefect flow that loads inputs, runs the canonical pipeline, and optionally archives outputs.                   |

## Test suites

- [ ] `tests/pipeline/` — Feature toggles, ingestion validation, and orchestrator behaviour tests.
- [ ] `tests/automation/` — HTTP client policies and webhook/CRM delivery fixtures.
- [ ] `tests/enrichment/` — Intent collectors, validators, and enrichment adapters.
- [ ] `tests/linkage/` — Entity resolution and probabilistic matching coverage.
- [ ] `tests/cli/` — Command parsing, progress reporting, and option integration tests.
- [ ] `tests/data_sources/` — Reader/writer adapters and dataset helpers.
- [ ] `tests/accessibility/` — Accessibility smoke tests for dashboards and reports.
- [ ] `tests/contracts/` — Golden contracts for CLI outputs and pipeline reports.
- [ ] `tests/domain/` — Domain model invariants and schema serialisation checks.
- [ ] `tests/fixtures/` — Shared fixtures for telemetry, orchestration, and pipeline flows.

_Tick a box when reviewing or updating a suite during a docs or QA sweep._

## Data, contracts, and expectations

| Location                                                    | Purpose                                                                                                | Notes                                                                                                                            |
| ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------- |
| [`data/`](../../data/)                           | Sample raw/refined workbooks, compliance evidence, logs, and asset inventory used in tutorials and QA. | Includes compliance verification log (`data/compliance/verification-log.json`) and packaged archives produced by CI.             |
| [`contracts/`](../../contracts/)                 | Pact-like CLI contract describing required output structure.                                           | [`hotpass-cli-contract.yaml`](../../contracts/hotpass-cli-contract.yaml) captures argument and artifact expectations. |
| [`data_expectations/`](../../data_expectations/) | Great Expectations suites grouped by dataset (contact, reachout, sacaa).                               | Feed pipeline validation via [`validation.py`](../../src/hotpass/validation.py).                                      |
| [`schemas/`](../../schemas/)                     | Canonical schema descriptors for SSOT and ingestion layers.                                            | Distributed with the package via `pyproject.toml` data-files.                                                                    |

## Continuous integration workflows

| Workflow                                                                     | Trigger                              | Key stages                                                                                                                                                                     |
| ---------------------------------------------------------------------------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [`docs.yml`](../../.github/workflows/docs.yml)                               | Docs/README changes on `main` or PRs | Sync docs extras, build HTML docs with warnings as errors, and run linkcheck.                                                                                                  |
| [`process-data.yml`](../../.github/workflows/process-data.yml)               | Push/PR to `main`                    | Full QA matrix (lint, tests, type, security, build), Docker validation, accessibility and mutation suites, fitness functions, artefact publication, and supply-chain evidence. |
| [`codeql.yml`](../../.github/workflows/codeql.yml)                           | Push/PR to `main`                    | GitHub CodeQL analysis for Python.                                                                                                                                             |
| [`secret-scanning.yml`](../../.github/workflows/secret-scanning.yml)         | Push/PR to `main`                    | Runs Gitleaks and uploads SARIF to code scanning.                                                                                                                              |
| [`copilot-setup-steps.yml`](../../.github/workflows/copilot-setup-steps.yml) | Manual or workflow file updates      | Primes uv environment, installs pre-commit, and configures Prefect for local/offline usage.                                                                                    |
| [`zap-baseline.yml`](../../.github/workflows/zap-baseline.yml)               | Manual dispatch                      | Optional Streamlit launch followed by OWASP ZAP baseline scan and report upload.                                                                                               |
