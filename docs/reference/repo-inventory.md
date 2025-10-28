---
title: Reference — repository inventory
summary: Snapshot of Hotpass packages, interfaces, orchestration flows, tests, datasets, and CI automation.
last_updated: 2025-10-30
---

# Reference — repository inventory

This inventory highlights the moving parts that power Hotpass. Use the tables below to
jump to the relevant code, fixtures, or automation when you need to trace behaviour or
extend the platform.

## Packages and modules

| Area | Description | Key entry points |
| --- | --- | --- |
| Pipeline execution | Core orchestration, configuration, and reporting for the refinement pipeline, including ingestion, aggregation, validation, and publishing logic. | <a href="../../src/hotpass/pipeline/">`src/hotpass/pipeline/`</a> · <a href="../../src/hotpass/pipeline_enhanced.py">`pipeline_enhanced.py`</a> · <a href="../../src/hotpass/pipeline_reporting.py">`pipeline_reporting.py`</a> |
| Automation delivery | Circuit breakers, retry-aware HTTP client, and webhook/CRM hooks for downstream automation. | <a href="../../src/hotpass/automation/">`src/hotpass/automation/`</a> |
| Enrichment services | Intent collectors, validators, and provider adapters for enrichment extras. | <a href="../../src/hotpass/enrichment/">`src/hotpass/enrichment/`</a> |
| Entity resolution | Probabilistic linkage runner plus Splink integration. | <a href="../../src/hotpass/linkage/">`src/hotpass/linkage/`</a> · <a href="../../src/hotpass/entity_resolution.py">`entity_resolution.py`</a> |
| Transform & scoring | Feature engineering, scoring, and transformation helpers. | <a href="../../src/hotpass/transform/">`src/hotpass/transform/`</a> · <a href="../../src/hotpass/transform/scoring.py">`transform/scoring.py`</a> |
| Domain models | Typed representations of contacts, organisations, telemetry payloads, and shared enums. | <a href="../../src/hotpass/domain/">`src/hotpass/domain/`</a> |
| Data access | Data source adapters and persistence abstractions (Excel, parquet, Polars datasets). | <a href="../../src/hotpass/data_sources/">`src/hotpass/data_sources/`</a> · <a href="../../src/hotpass/storage/">`src/hotpass/storage/`</a> |
| Configuration & profiles | Canonical config schema, upgrade helpers, and reusable profile presets. | <a href="../../src/hotpass/config_schema.py">`config_schema.py`</a> · <a href="../../src/hotpass/config_doctor.py">`config_doctor.py`</a> · <a href="../../src/hotpass/profiles/">`profiles/`</a> |
| CLI surface | Unified CLI, progress logging, and enhanced compatibility shim. | <a href="../../src/hotpass/cli/">`cli/`</a> · <a href="../../src/hotpass/cli_enhanced.py">`cli_enhanced.py`</a> |
| Compliance & validation | POPIA/ISO evidence logging, PIIs redaction, schema + expectation gates. | <a href="../../src/hotpass/compliance.py">`compliance.py`</a> · <a href="../../src/hotpass/compliance_verification.py">`compliance_verification.py`</a> · <a href="../../src/hotpass/validation.py">`validation.py`</a> |
| Observability & telemetry | Metric exporters, OpenTelemetry wiring, and structured logging helpers. | <a href="../../src/hotpass/telemetry/">`telemetry/`</a> · <a href="../../src/hotpass/observability.py">`observability.py`</a> |

## Console scripts

| Script | Module | Purpose |
| --- | --- | --- |
| `hotpass` | <a href="../../src/hotpass/cli/main.py">`hotpass.cli:main`</a> | Unified CLI for running the pipeline, orchestrations, deployments, dashboards, and tooling. |
| `hotpass-enhanced` | <a href="../../src/hotpass/cli_enhanced.py">`hotpass.cli_enhanced:main`</a> | Backwards-compatible entry point that delegates to the unified CLI with deprecation warnings. |

## Prefect flows

| Flow name | Definition | Highlights |
| --- | --- | --- |
| `hotpass-backfill` | <a href="../../src/hotpass/orchestration.py">`backfill_pipeline_flow`</a> | Rehydrates archived inputs, reruns the pipeline for historical windows, and aggregates metrics with concurrency guards. |
| `hotpass-refinement-pipeline` | <a href="../../src/hotpass/orchestration.py">`refinement_pipeline_flow`</a> | Primary Prefect flow that loads inputs, runs the canonical pipeline, and optionally archives outputs. |

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

| Location | Purpose | Notes |
| --- | --- | --- |
| <a href="../../data/">`data/`</a> | Sample raw/refined workbooks, compliance evidence, logs, and asset inventory used in tutorials and QA. | Includes compliance verification log (`data/compliance/verification-log.json`) and packaged archives produced by CI. |
| <a href="../../contracts/">`contracts/`</a> | Pact-like CLI contract describing required output structure. | <a href="../../contracts/hotpass-cli-contract.yaml">`hotpass-cli-contract.yaml`</a> captures argument and artifact expectations. |
| <a href="../../data_expectations/">`data_expectations/`</a> | Great Expectations suites grouped by dataset (contact, reachout, sacaa). | Feed pipeline validation via <a href="../../src/hotpass/validation.py">`validation.py`</a>. |
| <a href="../../schemas/">`schemas/`</a> | Canonical schema descriptors for SSOT and ingestion layers. | Distributed with the package via `pyproject.toml` data-files. |

## Continuous integration workflows

| Workflow | Trigger | Key stages |
| --- | --- | --- |
| [`docs.yml`](../../.github/workflows/docs.yml) | Docs/README changes on `main` or PRs | Sync docs extras, build HTML docs with warnings as errors, and run linkcheck. |
| [`process-data.yml`](../../.github/workflows/process-data.yml) | Push/PR to `main` | Full QA matrix (lint, tests, type, security, build), Docker validation, accessibility and mutation suites, fitness functions, artefact publication, and supply-chain evidence. |
| [`codeql.yml`](../../.github/workflows/codeql.yml) | Push/PR to `main` | GitHub CodeQL analysis for Python. |
| [`secret-scanning.yml`](../../.github/workflows/secret-scanning.yml) | Push/PR to `main` | Runs Gitleaks and uploads SARIF to code scanning. |
| [`copilot-setup-steps.yml`](../../.github/workflows/copilot-setup-steps.yml) | Manual or workflow file updates | Primes uv environment, installs pre-commit, and configures Prefect for local/offline usage. |
| [`zap-baseline.yml`](../../.github/workflows/zap-baseline.yml) | Manual dispatch | Optional Streamlit launch followed by OWASP ZAP baseline scan and report upload. |

