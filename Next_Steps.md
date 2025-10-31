# Next Steps

## Tasks

- [ ] **2025-12-30 · Programme** — Confirm Phase 5 T5.5 completion so roadmap status reflects programme expectations.【F:ROADMAP.md†L43-L63】
- [ ] **2025-12-31 · QA** — Execute full E2E runs with canonical configuration toggles ; reuse Prefect deployment `hotpass-e2e-staging`).
- [ ] **2026-01-05 · Platform** — Validate Prefect backfill deployment guardrails in staging.
- [ ] **2026-01-15 · Engineering** — Benchmark `HotpassConfig.merge` on large payloads.
- [ ] **2026-01-15 · QA & Engineering** — Extend orchestrate/resolve CLI coverage for advanced profiles (draft scope by 2025-12-19; reuse CLI stress fixtures and add resolve scenarios in `tests/cli/test_resolve.py`).
- [ ] **2025-11-26 · Platform (Phase 3)** — Merge Prefect deployment manifests from PR `prefect/deployment-manifests` and validate idempotent schedules (owner: Platform).【d9a97b†L18-L24】【7786e5†L55-L63】
- [x] **2025-11-29 · Engineering & QA (Phase 3)** — Exercise OpenLineage + Marquez hardening in follow-up to PR `observability/marquez-bootstrap`, capturing lineage QA evidence (owners: Engineering & QA). Staging rehearsal completed 2025-11-12; artefacts under `dist/staging/marquez/20251112T140000Z/` (CLI log + UI capture).【d9a97b†L24-L29】【7786e5†L63-L72】
- [ ] **2025-12-03 · Platform (Phase 5)** — Harden uv-based CI quality gates in PR `ci/uv-quality-gates` to unblock coverage enforcement (owner: Platform).【d9a97b†L40-L44】【7786e5†L93-L101】
- [ ] **2025-12-06 · Security (Phase 5)** — Ship PR `security/codeql-and-secrets` enabling CodeQL, detect-secrets diff mode, and Bandit SARIF (owner: Security).【d9a97b†L44-L47】【7786e5†L101-L108】
- [ ] **2025-12-09 · Platform (Phase 5)** — Enable Docker buildx cache reuse through PR `ci/docker-cache` (owner: Platform).【d9a97b†L47-L50】【7786e5†L108-L113】
- [ ] **2025-12-13 · Platform (Phase 5)** — Publish SBOM + SLSA attestations via PR `supply-chain/provenance` (owner: Platform).【d9a97b†L50-L53】【7786e5†L108-L113】
- [x] **2025-12-18 · Platform (Phase 5)** — Complete ARC runner rollout and OIDC wiring through PR `infra/arc-rollout`, coordinating with QA for smoke tests (owner: Platform). Lifecycle rehearsal executed 2025-11-13; artefacts stored at `dist/staging/arc/20251113T160000Z/` (lifecycle report + STS confirmation).【d9a97b†L53-L56】【7786e5†L93-L101】
- [ ] **2025-12-20 · Engineering (Phase 5)** — Finalise OpenTelemetry exporter propagation post-PR `telemetry/bootstrap` with additional QA sign-off (owner: Engineering).【d9a97b†L56-L59】【7786e5†L108-L113】
- [ ] **2026-01-07 · Docs & UX (Phase 6)** — Finish Diátaxis navigation uplift in PR `docs/data-governance-nav` follow-on, ensuring governance artefacts surfaced (owner: Docs & UX).【d9a97b†L59-L63】【7786e5†L111-L118】
- [ ] **2026-01-10 · Engineering & UX (Phase 6)** — Release `cli/doctor-and-init` onboarding UX refinements and regression coverage (owner: Engineering & UX).【d9a97b†L63-L66】【7786e5†L118-L125】

## Steps

- [ ] Reconfirm post-PR hygiene: ensure `Next_Steps.md` updated alongside each PR hand-off as per contributing guide (rolling reminder for all owners).【2ed7b7†L71-L71】
- [ ] Introduce manifest-driven Prefect deployments with CLI/docs/ADR updates (in progress 2025-10-29).
- [ ] Schedule Marquez lineage smoke against `observability/marquez-bootstrap` follow-up once optional dependencies land (target 2025-11-29) using the quickstart workflow.【d9a97b†L24-L29】【b3de0d†L1-L42】
- [ ] 2025-11-05 — Continue migrating orchestration pytest assertions to `expect()` helper outside touched scenarios (owner: QA & Engineering).
  - **Progress:** test_error_handling.py completed (46 assertions migrated); compliance and enrichment suites now use `expect()`. Remaining bare-assert files: 34.
- [ ] 2025-11-07 — Audit remaining telemetry/CLI modules for strict mypy readiness and convert outstanding bare assertions (owner: Engineering & QA).
  - **Progress:** Fixed 6 mypy errors (3 unused type:ignore comments, 3 type annotation improvements), reduced from 177 to 171 errors.

## Deliverables

- [x] Marquez lineage smoke evidence captured with screenshots/log export following quickstart (Owner: QA & Engineering). Artefacts: `dist/staging/marquez/20251112T140000Z/cli.log`, `dist/staging/marquez/20251112T140000Z/graph.png`.【b3de0d†L1-L42】【F:tests/infrastructure/test_marquez_stack.py†L1-L46】【F:tests/test_lineage.py†L149-L200】

## Quality Gates

- [x] Infrastructure — ARC runner smoke test workflow (`ARC runner smoke test`) reports healthy lifecycle across staging namespace. Live rehearsal artefacts: `dist/staging/arc/20251113T160000Z/lifecycle.json`, `dist/staging/arc/20251113T160000Z/sts.txt`.【F:.github/workflows/arc-ephemeral-runner.yml†L1-L60】【F:scripts/arc/verify_runner_lifecycle.py†L1-L210】
- [ ] Types — `uv run mypy src tests scripts` (171 errors after type annotation hardening; down from 177 at start of pass via 3 unused type:ignore fixes and 3 type annotation improvements; focus upcoming passes on trimming remaining unused `type: ignore` directives and adding real stubs).【2fa771†L1-L146】
- [ ] Lineage — `uv run pytest tests/test_lineage.py tests/scripts/test_arc_runner_verifier.py` pending optional dependency install; rerun alongside Marquez smoke per quickstart once extras land.【860a1f†L1-L18】【477232†L1-L80】【ec8339†L1-L80】【b3de0d†L1-L42】
  - [ ] Infrastructure — `uv run python scripts/arc/verify_runner_lifecycle.py --owner ...` to capture lifecycle report for ARC runners (blocked awaiting staging access).【73fd99†L41-L55】

## Links

- `schemas/` — current frictionless contracts to be regenerated.
- `src/hotpass/orchestration.py` — pipeline payload helpers requiring baseline fix.
- `docs/index.md` — landing page now surfacing governance artefacts; monitor follow-up requests.
- `docs/reference/data-docs.md` & `docs/reference/schema-exports.md` — new reference pages for Data Docs + JSON Schema consumers.
- `docs/governance/data-governance-navigation.md` — consolidated navigation across governance artefacts.
- `docs/operations/foundation-retro.md` — Phase 1 retro agenda and scope reconciliation.
- `scripts/arc/examples/hotpass_arc_idle.json` — reusable snapshot for lifecycle rehearsal.
- `docs/adr/index.md` — documentation strategy alignment summary.
- `prefect/` — manifest library consumed by the revamped deployment loader.
- `docs/adr/0007-cli-onboarding.md` — decision record for CLI doctor/init onboarding workflow.
- `docs/reference/cli.md` / `docs/tutorials/quickstart.md` — updated references introducing doctor/init usage.

## Risks/Notes

- Keep this file actionable: move completed checklist items to `Next_Steps_Log.md` whenever tasks close so future updates remain focused on open work.
- Prefect pipeline task payload fix merged; continue monitoring downstream Prefect deployments for regressions when toggling `backfill`/`incremental` flags.
- Ingestion now normalises column headers and restores missing optional fields before slug/province transforms; monitor downstream consumers for assumptions about duplicate column names.
- Format gate now green after restoring repo baseline; continue coordinating with maintainers before applying broad formatting updates.
- Bandit reports tolerated `try/except/pass`; confirm acceptable risk or remediate while touching orchestration.
- Watch list: monitor uv core build availability and Semgrep CA bundle rollout for future updates (owners retained from prior plan).
- Marquez compose stack introduced for lineage verification; automated tests now guard compose configuration and lineage environment variables while we schedule live smoke tests for CLI + Prefect flows.
- ARC lifecycle verification rehearsed via snapshot; continue tracking live staging access to close the infrastructure gate.
