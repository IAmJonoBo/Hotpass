# Hotpass delivery roadmap

This file complements [`docs/roadmap.md`](docs/roadmap.md) with a quick view of
open checklist items and the pull requests planned to address them. Use it as the
entry point during triage so upcoming work stays aligned with the programme
phases and governance gates.

## Phase 1 — Foundation alignment

- [x] **T1.1 Programme guardrails** — Roadmap, governance charter, and evidence
  ledger refreshed; retro plan captured in
  [`docs/operations/foundation-retro.md`](docs/operations/foundation-retro.md) to
  guide the upcoming Programme review.
- [x] **T1.2 Operational readiness** — Prefect bootstrap, telemetry wiring, and
  ARC lifecycle verifier (with snapshot mode) prepared Platform for the staged
  runner rollout documented in the ARC how-to guide.

## Phase 2 — Contracts, validation, and data hygiene

- [ ] **T2.1 Canonical dataset contracts** — Finalise Pandera table models and
  publish JSON Schema artefacts for any new datasets.
  - Upcoming PR: `contracts/new-dataset-schemas` (assign to Engineering once
    new workbook samples land).
- [x] **T2.2 Great Expectations gates** — Keep checkpoints and Data Docs in
  sync, ensuring the docs landing page points to the validation artefacts.
  - Delivered via `docs/data-governance-nav`: the new
    [`docs/governance/data-governance-navigation.md`](docs/governance/data-governance-navigation.md)
    page surfaces Data Docs, schema exports, lineage, and evidence packs from the
    docs landing page.
- [ ] **T2.3 Property-based tests** — Expand Hypothesis coverage for ingestion
  and export idempotency scenarios.
  - Upcoming PR: `qa/property-tests-round-two` scheduled for the next QA sweep.

## Phase 3 — Pipelines (ingest, backfill, refine, publish)

- [ ] **T3.1 Prefect 3 deployments** — Commit deployment manifests and ensure
  `prefect deploy` produces idempotent schedules.
  - Upcoming PR: `prefect/deployment-manifests` (platform-eng, pending review).
- [ ] **T3.2 OpenLineage + Marquez** — Harden lineage emission and document the
  local Marquez stack.
  - Completed PR: `observability/marquez-bootstrap` (2025-10-28) introduced the
    compose stack and quickstart guide; ongoing maintenance tasks live in
    `docs/roadmap.md`.
- [x] **T3.3 Persist refined outputs + data versioning** — Parquet outputs and
  DVC snapshots are live with CLI support.

## Phase 4 — ML lifecycle (conditional)

- [x] **T4.1 MLflow tracking + registry** — Tracking, registry, and promotion
  workflows are merged with comprehensive coverage.

## Phase 5 — CI/CD & ephemeral runners

- [ ] **T5.1 Quality gates** — Migrate the GitHub Actions QA workflow to uv and
  enforce coverage thresholds.
  - Upcoming PR: `ci/uv-quality-gates` aligned with the platform team schedule.
- [ ] **T5.2 Security scanning** — Codify CodeQL, detect-secrets diff mode, and
  Bandit SARIF uploads.
  - Upcoming PR: `security/codeql-and-secrets` blocked on runner availability.
- [ ] **T5.3 Docker buildx cache** — Enable cache reuse across PR builds.
  - Upcoming PR: `ci/docker-cache` queued after quality gate hardening.
- [ ] **T5.4 Provenance** — Generate SBOMs and SLSA attestations.
  - Upcoming PR: `supply-chain/provenance` depends on SBOM generator refactor.
- [ ] **T5.5 Ephemeral runners** — Roll out ARC manifests and AWS OIDC wiring.
  - Upcoming PR: `infra/arc-rollout` tracked in platform backlog.
- [ ] **T5.6 Telemetry instrumentation** — Propagate OpenTelemetry exporters
  through CLI and Prefect.
  - Completed PR: `telemetry/bootstrap` (2025-12-02) delivered shared bootstrap
    logic; follow-up docs tracked separately.

## Phase 6 — Documentation & UX

- [ ] **T6.1 Diátaxis docs structure** — Maintain the Tutorials/How-to/Reference/
  Explanations balance and surface governance artefacts from the landing page.
  - In flight: `docs/data-governance-nav` (this PR) and follow-on PRs for the
    `hotpass doctor` quickstart once the CLI work lands.
- [ ] **T6.2 CLI UX (`hotpass doctor` / `hotpass init`)** — Introduce guided
  onboarding and diagnostics commands.
  - Upcoming PR: `cli/doctor-and-init` (design pending from product UX).

## Quick links

- Full programme context: [`docs/roadmap.md`](docs/roadmap.md)
- Governance assets: [`docs/reference/data-docs.md`](docs/reference/data-docs.md),
  [`docs/reference/schema-exports.md`](docs/reference/schema-exports.md),
  [`docs/observability/marquez.md`](docs/observability/marquez.md)
- Contribution workflow: [`README.md`](README.md),
  [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md)
