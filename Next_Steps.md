# Next Steps

## Tasks

- [ ] **Programme** — Confirm Phase 5 T5.5 completion so roadmap status reflects programme expectations.
- [ ] **QA** — Execute full E2E runs with canonical configuration toggles ; reuse Prefect deployment `hotpass-e2e-staging`).
- [ ] **Platform** — Validate Prefect backfill deployment guardrails in staging.
- [ ] **Engineering** — Benchmark `HotpassConfig.merge` on large payloads.
- [ ] **QA & Engineering** — Extend orchestrate/resolve CLI coverage for advanced profiles (reuse CLI stress fixtures and add resolve scenarios in `tests/cli/test_resolve.py`).
  - **Progress:** Added `tests/cli/test_resolve_profile.py` covering profile-driven Splink defaults, sensitive-field redaction, and output writes. Remaining: expand orchestrator stress fixtures once staging data is available.
- [x] **Platform (Phase 3)** — Merge Prefect deployment manifests from PR `prefect/deployment-manifests` and validate idempotent schedules (owner: Platform).
- [x] **Engineering & QA (Phase 3)** — Exercise OpenLineage + Marquez hardening in follow-up to PR `observability/marquez-bootstrap`, capturing lineage QA evidence (owners: Engineering & QA). Staging rehearsal completed; artefacts under `dist/staging/marquez/` (CLI log + UI capture).
- [x] **Platform (Phase 5)** — Harden uv-based CI quality gates in PR `ci/uv-quality-gates` to unblock coverage enforcement (owner: Platform).【F:.github/workflows/quality-gates.yml†L1-L110】【F:scripts/quality/run_all_gates.py†L1-L200】
- [x] **Security (Phase 5)** — Ship PR `security/codeql-and-secrets` enabling CodeQL, detect-secrets diff mode, and Bandit SARIF (owner: Security).【F:.github/workflows/codeql.yml†L1-L40】【F:.github/workflows/secret-scanning.yml†L1-L40】【F:.github/workflows/process-data.yml†L25-L120】
- [ ] **Platform (Phase 5)** — Enable Docker buildx cache reuse through PR `ci/docker-cache` (owner: Platform).
- [x] **Platform (Phase 5)** — Publish SBOM + SLSA attestations via PR `supply-chain/provenance` (owner: Platform).【F:.github/workflows/process-data.yml†L180-L260】【F:scripts/supply_chain/generate_sbom.py†L1-L120】
- [x] **Platform (Phase 5)** — Complete ARC runner rollout and OIDC wiring through PR `infra/arc-rollout`, coordinating with QA for smoke tests (owner: Platform). Lifecycle rehearsal executed; artefacts stored at `dist/staging/arc/` (lifecycle report + STS confirmation).
- [x] **Engineering (Phase 5)** — Finalise OpenTelemetry exporter propagation post-PR `telemetry/bootstrap` with additional QA sign-off (owner: Engineering).【F:src/hotpass/cli/commands/run.py†L156-L531】【F:src/hotpass/telemetry/bootstrap.py†L1-L200】
- [ ] **Docs & UX (Phase 6)** — Finish Diátaxis navigation uplift in PR `docs/data-governance-nav` follow-on, ensuring governance artefacts surfaced (owner: Docs & UX).
- [x] **Engineering & UX (Phase 6)** — Release `cli/doctor-and-init` onboarding UX refinements and regression coverage (owner: Engineering & UX).【F:src/hotpass/cli/commands/doctor.py†L1-L200】【F:src/hotpass/cli/commands/init.py†L1-L220】【F:docs/reference/cli.md†L1-L160】

## Steps

- [ ] Reconfirm post-PR hygiene: ensure `Next_Steps.md` updated alongside each PR hand-off as per contributing guide (rolling reminder for all owners).【2ed7b7†L71-L71】
- [ ] Introduce manifest-driven Prefect deployments with CLI/docs/ADR updates (in progress 2025-10-29).
- [ ] Schedule Marquez lineage smoke against `observability/marquez-bootstrap` follow-up once optional dependencies land (target 2025-11-29) using the quickstart workflow.【d9a97b†L24-L29】【b3de0d†L1-L42】
- [ ] Continue migrating orchestration pytest assertions to `expect()` helper outside touched scenarios (owner: QA & Engineering).
  - **Progress:** test_error_handling.py completed (46 assertions migrated); compliance verification + enrichment suites migrated to `expect()`; agentic orchestration coverage converted 2025-10-31. Remaining bare-assert files: 31.
- [ ] Audit remaining telemetry/CLI modules for strict mypy readiness and convert outstanding bare assertions (owner: Engineering & QA).
  - **Progress:** Latest `uv run mypy src tests scripts` on 2025-10-31 reports 197 errors (up from 171); clusters centred on untyped pytest fixtures (for example `tests/test_deployment_specs.py`) and an unreachable guard in `scripts/quality/run_qg4.py` introduced by recent tooling updates.【F:tests/test_deployment_specs.py†L70-L200】【F:scripts/quality/run_qg4.py†L100-L220】

## Deliverables

- [x] Marquez lineage smoke evidence captured with screenshots/log export following quickstart (Owner: QA & Engineering). Artefacts: `dist/staging/marquez/20251112T140000Z/cli.log`, `dist/staging/marquez/20251112T140000Z/graph.png`.【b3de0d†L1-L42】【F:tests/infrastructure/test_marquez_stack.py†L1-L46】【F:tests/test_lineage.py†L149-L200】

## Quality Gates

- [x] Infrastructure — ARC runner smoke test workflow (`ARC runner smoke test`) reports healthy lifecycle across staging namespace. Live rehearsal artefacts: `dist/staging/arc/20251113T160000Z/lifecycle.json`, `dist/staging/arc/20251113T160000Z/sts.txt`.【F:.github/workflows/arc-ephemeral-runner.yml†L1-L60】【F:scripts/arc/verify_runner_lifecycle.py†L1-L210】
- [ ] Types — `uv run mypy src tests scripts` surfaced 197 errors on 2025-10-31; prioritise typing shared fixtures (see `tests/test_deployment_specs.py`) and fix the unreachable return in `scripts/quality/run_qg4.py` before tackling lower-priority decorators.【F:tests/test_deployment_specs.py†L70-L200】【F:scripts/quality/run_qg4.py†L100-L220】
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
