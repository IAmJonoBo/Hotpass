---
title: Hotpass roadmap
summary: Status of the Hotpass modernisation programme, quality gates, and follow-up work.
last_updated: 2025-10-28
---

# Hotpass roadmap

This roadmap is the single source of truth for the Hotpass programme. It captures the active plan, guardrails, acceptance criteria, and the mapping of work to the repository layout so that changes are incremental, reversible, and observable.

## Executive summary

Focus areas for the upcoming iterations:

- **Contracts & validation**: canonical dataset models (Pydantic/Pandera), JSON Schemas in `schemas/`, and Great Expectations (GX) gates that block publishes on failure.
- **Pipelines**: Prefect 3 deployments with idempotent/resumable runs and explicit `backfill` / `incremental` parameters; OpenLineage emission with a local Marquez viewer; refined outputs written as Parquet with data versioning.
- **CI/CD & runners**: uv-based quality gates (ruff, mypy, pytest+coverage, SARIF), CodeQL/detect-secrets/bandit, Docker buildx with cache, SBOM + SLSA attestations, and ephemeral self-hosted runners via Actions Runner Controller (ARC) with OIDC→AWS.
- **Docs & UX**: Diátaxis structure enforced; add `hotpass doctor` and `hotpass init` to streamline onboarding and troubleshooting.

## Iteration plan (date-free)

**Iteration A – safety rails first**

1. Phase 2 tasks (contracts, GX, property tests).
2. Phase 5 tasks T5.1–T5.4 (quality CI, security, build, provenance).
3. Phase 6 task T6.1 (docs skeleton and links).

**Iteration B – orchestration, observability, and data versioning** 4. Phase 3 tasks (Prefect deployments, OpenLineage/Marquez, Parquet + DVC). 5. Phase 5 tasks T5.5–T5.6 (ephemeral runners + OpenTelemetry instrumentation). 6. Phase 6 task T6.2 (CLI UX: `doctor` and `init`). 7. Phase 4 task (MLflow) **only if** training is in scope; otherwise record an ADR and defer.

---

## Phase 2 — Contracts, validation, and data hygiene

- [ ] **T2.1 Canonical dataset contracts**

  - [ ] Add row-level models with **Pydantic** under `contracts/<dataset>.py`. Optionally add table-level **Pandera** `DataFrameModel`s for whole-table checks.
  - [ ] Export **JSON Schema** files to `schemas/<dataset>.schema.json` for every canonical dataset.
  - [ ] Autogenerate `docs/reference/schemas.md` with a field table per dataset.
  - **Acceptance:** sample records validate; schemas exist under `schemas/`; the reference page builds and links correctly.

- [ ] **T2.2 Great Expectations gates**

  - [ ] Create **Expectation Suites** per dataset and store under `data_expectations/`.
  - [ ] Add **Checkpoints** that run before publish steps; failing validation must block publish.
  - [ ] Render **Data Docs** to `dist/data-docs/` and link from `docs/index`.
  - **Acceptance:** CI job runs checkpoints; failures fail the job; `dist/data-docs/` artefacts are published.

- [ ] **T2.3 Property-based tests (Hypothesis)**
  - [ ] Create `tests/property/` for edge cases: encodings, date formats, missing/extra columns, duplicate headers.
  - [ ] Add idempotency tests (same inputs → same outputs) for core transforms.
  - **Acceptance:** CI passes property-based tests; any discovered regressions include minimal repro data in `tests/data/`.

## Phase 3 — Pipelines (ingest, backfill, refine, publish)

- [ ] **T3.1 Prefect 3 deployments**

  - [ ] Add `prefect.yaml` defining per-flow deployments, schedules, and tags.
  - [ ] Define parameters `backfill: bool`, `incremental: bool`, `since: datetime|None` and ensure flows are idempotent and resumable.
  - **Acceptance:** `prefect deploy` produces deployments; the UI shows schedules; re-running is idempotent.

- [ ] **T3.2 OpenLineage + Marquez**

  - [ ] Add `infra/marquez/docker-compose.yml` to run Marquez locally; document `make marquez-up`.
  - [ ] Emit **OpenLineage** events from flows; record datasets/jobs/runs; link the UI from docs.
  - **Acceptance:** lineage appears in Marquez for a demo flow; screenshot in PR.

- [ ] **T3.3 Persist refined outputs + data versioning**
  - [ ] Persist refined outputs as **Parquet** under `dist/refined/` with explicit schema and compression.
  - [ ] Adopt **DVC** (or lakeFS) to version refined data and backfill snapshots.
  - **Acceptance:** `dvc status` is clean after a run; `dvc repro` restores a snapshot; Parquet schema checks pass.

## Phase 4 — ML lifecycle (conditional)

- [ ] **T4.1 MLflow tracking + registry**
  - [ ] If model training exists or is planned, run MLflow Tracking with a DB backend; log code, params, metrics, and artefacts.
  - [ ] Create a Model Registry with stage gates ("Staging" → "Production"); document promotion policy.
  - **Acceptance:** example run visible; a dummy model promoted to "Staging"; ADR committed describing the policy.

## Phase 5 — CI/CD & ephemeral runners

- [ ] **T5.1 `ci.yml` – quality gates**

  - [ ] Use **uv** with caching; run **ruff**, **mypy**, **pytest** with coverage gates; upload SARIF where applicable.
  - **Acceptance:** CI green; coverage ≥ baseline.

- [ ] **T5.2 `security.yml` – CodeQL, secrets, Bandit**

  - [ ] Enable **CodeQL**; run **detect-secrets** in diff mode; run **bandit**.
  - **Acceptance:** CodeQL results in Security tab; secrets baseline present; Bandit SARIF uploaded.

- [ ] **T5.3 `build.yml` – Docker buildx + cache**

  - [ ] Use `docker/build-push-action` with `cache-from/to: gha`; publish image artefacts.
  - **Acceptance:** builds hit cache across PRs; image digest attached.

- [ ] **T5.4 `provenance.yml` – SBOM + SLSA**

  - [ ] Generate **SBOM** via Syft; add **build-provenance** attestations.
  - **Acceptance:** SBOM artefact attached; provenance attestation verifiable.

- [ ] **T5.5 Ephemeral runners – ARC + OIDC→AWS**

  - [ ] Commit `infra/arc/` manifests for **Actions Runner Controller** runner scale sets; default to ephemeral pods.
  - [ ] Configure **OIDC** → AWS roles for temporary credentials (no long-lived secrets).
  - **Acceptance:** workflows execute on ephemeral runners; AWS access uses OIDC.

- [ ] **T5.6 Telemetry – OpenTelemetry**
  - [ ] Initialise OTel in the CLI and flows with OTLP exporters; set `OTEL_EXPORTER_OTLP_ENDPOINT` in CI/dev.
  - **Acceptance:** traces/metrics visible for a demo run.

## Phase 6 — Documentation & UX

- [ ] **T6.1 Diátaxis docs structure**

  - [ ] Ensure `docs/` uses Tutorials, How‑tos, Reference, and Explanations; link Data Docs and the lineage UI from the docs home.
  - **Acceptance:** landing page shows the four doc types; "How‑to: run a backfill" and "How‑to: read Data Docs" exist.

- [ ] **T6.2 CLI UX – `hotpass doctor` and `hotpass init`**
  - [ ] `doctor`: environment check (Python, uv, Prefect profile, OTel vars) and dataset sample validation.
  - [ ] `init`: generate config, sample data, and one‑shot bootstrap.
  - **Acceptance:** both commands succeed from a fresh checkout and provide actionable remediation hints on failure.

---

## Per‑PR acceptance criteria (applies to all changes)

- CI and security green; coverage not lower than baseline; docs build passes.
- **Data changes:** updated GX suites; validation passing; Data Docs refreshed.
- **Pipelines:** OpenLineage events visible in Marquez; flows have deployments and schedules.
- **CI:** SBOM artefacts and provenance attestations present; CodeQL uploaded.
- **Runners:** ARC manifests used; jobs execute on ephemeral runners with OIDC; Docker builds hit cache.

## Outputs

- ADRs under `docs/adr/NNN-*.md` (MADR‑style).
- Docs site navigation updated with links to Data Docs and the lineage UI.
- `ROADMAP.md` checklist tying issues/PRs to phases with labels `phase:2`…`phase:6`.

## Guardrails

- **Avoid scope creep (YAGNI):** if an integration isn’t required within the next two iterations, stub the interface and stop.
- **Prefer small, fast iterations;** never land a PR that reduces observability or reversibility.
