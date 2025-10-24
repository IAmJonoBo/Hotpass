# Hotpass Upgrade Roadmap

## Vision & Outcomes

- Deliver an intelligent, compliant SSOT platform with automated enrichment, entity resolution, and high trust scores.
- Maintain strict POPIA alignment with field-level provenance, consent tracking, and auditable guardrails.
- Provide a first-class developer experience using modern tooling, documentation, and observability.

---

## Phase Breakdown

### Phase 0 – Foundations *(Complete – October 2025)*

- [x] Adopted `uv` for dependency management (pyproject, lock file, CI integration, Docker image).
- [x] Introduced pre-commit hooks (`ruff`, `mypy`, `black`, `detect-secrets`) with Python 3.13 default.
- [x] Containerized pipeline with micromamba + `uv` bootstrap; runtime now aligned across local, CI, Docker.
- [x] Initialized and automated Sphinx documentation (`docs/`, `uv run sphinx-build`).

### Phase 1 – Orchestration & Observability

- [ ] Stand up Prefect or Dagster orchestration for pipeline runs, scheduling, retries.
- [ ] Expose pipeline configuration as tasks/flows with metadata logging.
- [ ] Implement OpenTelemetry logging + metrics (Grafana/Loki or Datadog sink).
- [ ] Publish validation status dashboards (Streamlit or Prefect UI).

### Phase 2 – Entity Resolution & Data Intelligence

- [ ] Replace heuristic dedupe with probabilistic matching (e.g., Splink) + confidence scoring.
- [ ] Build canonical entity registry with history (name variants, status timeline).
- [ ] Add ML-driven completeness/prioritization scores (LightGBM or XGBoost).
- [ ] Deploy human-in-the-loop review UI for ambiguous merges.

### Phase 3 – External Validation & Enrichment

- [ ] Integrate CIPC/SACAA/aviation registries (Playwright scraping or official APIs).
- [ ] Add search enrichment (Bing SERP API) + website extraction (Trafilatura).
- [ ] Implement structured LLM extraction with Pydantic guardrails + human review queue.
- [ ] Introduce caching layer (Redis/SQLite) with TTL+provenance.

### Phase 4 – Geospatial & Quality Expansion

- [ ] Plug in Google Maps or OSM geocoding for address validation and provincial inference.
- [ ] Store geospatial data (GeoParquet/PostGIS) and derive spatial insights.
- [ ] Enhance Great Expectations suites, add drift/anomaly detection, publish Data Docs.
- [ ] Persist run metadata, delta tracking, and change-data-capture snapshots.

### Phase 5 – Compliance & Operational Excellence

- [ ] Formalize POPIA policy: data classification, lawful basis, retention, DSAR process.
- [ ] Implement automated PII detection (Presidio) and redaction pipelines.
- [ ] Add consent & provenance columns per field (source, method, timestamp, legal basis).
- [ ] Build alerting for compliance deviations and enrichment guardrail violations.

---

## Quality Gates

1. **Static Analysis**: `ruff`, `mypy`, `detect-secrets`, and `bandit` clean (Python 3.13 runtime).
2. **Unit & Integration Tests**: `pytest` with snapshot tests for pipeline outputs; coverage ≥ 80% on core modules (current: ~79%).
3. **Data Validation**: Great Expectations checkpoints must pass; failure blocks deploy.
4. **Security Scan**: Bandit + dependency vulnerability checks (Safety/OSV).
5. **Documentation**: Sphinx build passes; changelog and migration notes updated.
6. **Compliance Audit**: POPIA checklist verified per release (consent fields, logging, removal requests).
7. **Performance Benchmark**: Pipeline runtime within defined SLA; regressions flagged.

---

## Test Approach (TA)

### Strategy

- Layered testing: unit → integration → system → user acceptance.
- Dedicated synthetic datasets for edge cases (duplicates, missing fields, conflicting data).
- Golden dataset comparisons using Parquet snapshots for regression detection.

### Test Types

- **Unit Tests**: Functions in normalization, entity resolution, enrichment handlers.
- **Integration Tests**: Pipeline runs against staged Excel inputs, external API mocks.
- **Contract Tests**: Validate orchestrator tasks, API schemas, CLI arguments.
- **End-to-End**: Orchestrated run from raw ingestion to enriched SSOT with validation reports.
- **Compliance Tests**: Automated assertions on provenance completeness, consent fields, redaction.
- **Performance Tests**: Load tests for enrichment workers and orchestrated flows.

### Tooling & Automation

- `pytest` (fixtures, parametrization, snapshot testing).
- `pytest-recording` for HTTP fixtures; `responses`/`respx` for API mocks.
- Prefect/Dagster test harness to simulate flow runs.
- CI matrix (macOS, Linux) with `uv run pytest` + quality gates.
- Nightly scheduled E2E validation via orchestration platform.

---

## POPIA Compliance Guardrails

- **Data Inventory**: Maintain catalog of collected fields, classification, lawful basis.
- **Consent Tracking**: Record consent state per contact; enforce removal requests.
- **Source Provenance**: Store {source_url, acquisition method, timestamp, confidence} per field.
- **Redaction**: Automatic PII scrubbing on scraped/free text fields before storage.
- **Access Control**: Role-based access, audit logging, encryption at rest/in transit.
- **Review Workflow**: Manual approval for high-risk enrichment; dual control for sensitive updates.
- **Incident Response**: Documented process with SLA, escalation contacts, communication templates.

---

## Sequencing & Milestones

1. **Week 1-2**: Phase 0 completion; CI/CD updated; docs baseline deployed.
2. **Week 3-4**: Orchestrator live, logging/metrics integrated; docs, dashboards refreshed.
3. **Month 2**: Entity resolution upgrade, review UI prototype, ML scoring beta.
4. **Month 3**: External enrichment connectors in production with guardrails; caching implemented.
5. **Month 4**: Geospatial pipeline, quality dashboards, drift detection.
6. **Month 5**: Compliance automations, POPIA audit readiness, release of new SSOT format.

Progress will be tracked via GitHub Projects kanban, with retrospectives each sprint to adjust scope and ensure alignment with compliance and business objectives.
