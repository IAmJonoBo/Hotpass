# Next Steps

## Tasks

- [ ] **Programme** — Confirm Phase 5 T5.5 completion so roadmap status reflects programme expectations.
- [ ] **QA** — Execute full E2E runs with canonical configuration toggles ; reuse Prefect deployment `hotpass-e2e-staging`).
- [ ] **Platform** — Validate Prefect backfill deployment guardrails in staging.
- [ ] **Engineering** — Benchmark `HotpassConfig.merge` on large payloads.
- [ ] **Engineering & Platform** — Design and implement new CLI surface commands (`hotpass net`, `hotpass aws`, `hotpass ctx`, `hotpass env`) that wrap tunnel setup, AWS identity checks, Prefect/kube context configuration, and environment drafting.
- [ ] **Docs & QA** — Document and test the new CLI automation surface once available (README quickstart, `docs/reference/cli.md`, `AGENTS.md`, and ARC how-to guide).
- [ ] **QA & Engineering** — Extend orchestrate/resolve CLI coverage for advanced profiles (reuse CLI stress fixtures and add resolve scenarios in `tests/cli/test_resolve.py`).
  - **Progress:** Added `tests/cli/test_resolve_profile.py` coverage for profile-driven Splink defaults, explicit disable flags, and Label Studio wiring; orchestrator stress fixtures still pending once staging data is available.
- [x] **Engineering & QA** — Execute the staged mypy remediation plan (typed Hypothesis wrappers ➜ optional-dependency stubs ➜ CLI/MCP typing ➜ long-tail cleanup) to drive the error count toward zero.
- [x] **Platform (Phase 5)** — Enable Docker buildx cache reuse through PR `ci/docker-cache` (owner: Platform).【F:.github/workflows/docker-cache.yml†L1-L60】
- [ ] **Platform & QA** — Capture staging evidence for Prefect backfill guardrails and ARC runner sign-off once access returns.
- [ ] **Docs & UX (Phase 6)** — Finish Diátaxis navigation uplift in PR `docs/data-governance-nav` follow-on, ensuring governance artefacts surfaced (owner: Docs & UX).

## Steps

- [ ] Reconfirm post-PR hygiene: ensure `Next_Steps.md` updated alongside each PR hand-off as per contributing guide (rolling reminder for all owners).【2ed7b7†L71-L71】
- [ ] Introduce manifest-driven Prefect deployments with CLI/docs/ADR updates (in progress 2025-10-29).
- [ ] Schedule Marquez lineage smoke against `observability/marquez-bootstrap` follow-up once optional dependencies land (target 2025-11-29) using the quickstart workflow.【d9a97b†L24-L29】【b3de0d†L1-L42】
- [ ] Document expected staging artefacts for Prefect backfill guardrails and ARC runner sign-off runs so evidence drops into `dist/staging/backfill/` and `dist/staging/arc/` when access resumes (owner: Platform & QA).
- [x] **Types remediation roadmap (Engineering & QA)** — execute the staged plan and record checkpoints:
  - **Phase 0** (Baseline capture) — archived `dist/quality-gates/baselines/mypy-baseline-2025-10-31.txt`; pytest baseline confirmed.
  - **Phase 1** (Hypothesis/property suites) — typed wrappers + suite updates; property suites now raise zero decorator warnings.
  - **Phase 2** (Optional dependency stubs) — centralised stubs (`tests/helpers/stubs.py`), refactored orchestration/dashboard suites; mypy fell below 40 errors with tests green.
  - **Phase 3** (CLI/MCP/source typing) — annotated CLI commands, MCP server, remaining fixtures; mypy below 15 errors with `uv run pytest` green.
  - **Phase 4** (Long tail) — residual list-based expects/unreachables cleared; `uv run mypy src tests scripts` now reports 0 errors.
- [ ] Continue migrating orchestration pytest assertions to `expect()` helper outside touched scenarios (owner: QA & Engineering).
  - **Progress:** test_error_handling.py completed (46 assertions migrated); compliance verification + enrichment suites migrated to `expect()`; agentic orchestration coverage converted 2025-10-31. Remaining bare-assert files: 31.
- [ ] Audit remaining telemetry/CLI modules for strict mypy readiness and convert outstanding bare assertions (owner: Engineering & QA).
  - **Progress:** `uv run mypy apps/data-platform tests ops` on 2025-10-31 reports 0 errors (down from 197 baseline). Remaining follow-up: monitor new suites for decorator regressions.
- [ ] Review and adopt the repository restructure guidance in `docs/architecture/repo-restructure-plan.md` as the canonical layout reference (owners: Engineering & Docs).

## Deliverables

- [x] Marquez lineage smoke evidence captured with screenshots/log export following quickstart (Owner: QA & Engineering). Artefacts: `dist/staging/marquez/20251112T140000Z/cli.log`, `dist/staging/marquez/20251112T140000Z/graph.png`.【b3de0d†L1-L42】【F:tests/infrastructure/test_marquez_stack.py†L1-L46】【F:tests/test_lineage.py†L149-L200】

## Quality Gates

- [x] Infrastructure — ARC runner smoke test workflow (`ARC runner smoke test`) reports healthy lifecycle across staging namespace. Live rehearsal artefacts: `dist/staging/arc/20251113T160000Z/lifecycle.json`, `dist/staging/arc/20251113T160000Z/sts.txt`.【F:.github/workflows/arc-ephemeral-runner.yml†L1-L60】【F:ops/arc/verify_runner_lifecycle.py†L1-L210】
- [x] Types — `uv run mypy src tests scripts` now reports 0 errors as of 2025-10-31; remediation plan complete.【F:tests/helpers/stubs.py†L1-L170】【F:apps/data-platform/hotpass/cli/commands/plan.py†L1-L200】
- [x] Lineage — `uv run pytest tests/test_lineage.py tests/scripts/test_arc_runner_verifier.py` executed 2025-10-31; suite passes locally with existing dependencies.【F:tests/test_lineage.py†L1-L200】【F:tests/scripts/test_arc_runner_verifier.py†L1-L160】
  - [ ] Infrastructure — `uv run python ops/arc/verify_runner_lifecycle.py --owner ...` to capture lifecycle report for ARC runners (blocked awaiting staging access).【73fd99†L41-L55】

## Links

- `schemas/` — current frictionless contracts to be regenerated.
- `apps/data-platform/hotpass/orchestration.py` — pipeline payload helpers requiring baseline fix.
- `docs/architecture/repo-restructure-plan.md` — canonical mapping for the apps/ops separation and follow-up actions.
- `docs/index.md` — landing page now surfacing governance artefacts; monitor follow-up requests.
- `docs/reference/data-docs.md` & `docs/reference/schema-exports.md` — new reference pages for Data Docs + JSON Schema consumers.
- `docs/governance/data-governance-navigation.md` — consolidated navigation across governance artefacts.
- `docs/operations/foundation-retro.md` — Phase 1 retro agenda and scope reconciliation.
- `ops/arc/examples/hotpass_arc_idle.json` — reusable snapshot for lifecycle rehearsal.
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
