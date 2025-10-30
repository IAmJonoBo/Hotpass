# Hotpass Gap Analysis — 30 Oct 2025

## 1. Context
- **Scope**: Alignment review across `UPGRADE.md`, `IMPLEMENTATION_PLAN.md`, `Next_Steps.md`, and the current Hotpass codebase/documentation.
- **Goal**: Capture open gaps blocking frontier-standard readiness and the five quality gates (QG‑1 → QG‑5), and commit to concrete remediation work.
- **Baseline artifacts**: `UPGRADE.md`, `IMPLEMENTATION_PLAN.md`, `Next_Steps.md`, `.github/copilot-instructions.md`, `AGENTS.md`, `scripts/quality`, `src/hotpass/mcp`, `tests/*`.

## 2. Executive Summary
- Core CLI/MCP parity is landed, and the quality-gate workflows exist, but key verification steps (especially data quality) are still stubs.
- Documentation trails implementation: the CLI reference and missing MCP/quality-gate references dilute the agent experience promised in `UPGRADE.md`.
- Research guidance in docs over-promises APIs that are not exposed by the package, creating confusion for downstream agents.
- Testing hygiene and outstanding Next Steps (mypy debt, lineage smoke, infra rehearsals) remain active risks to TA closure.

## 3. Detailed Gaps & Resolution Plans

### Gap 1 — QG-2 (Data Quality) is only a schema check
- **Observation**: `scripts/quality/run_all_gates.py` line 92 merely verifies that `aviation.yaml` lists expectations instead of running Great Expectations suites and producing Data Docs.
- **Impact**: QG-2 does not validate actual data, so regressions in expectations or GE configuration can ship unnoticed; TA items 2/3 remain unproven.
- **Plan**:
  1. Implement `run_qg2.py` to load sample data, execute GE suites, and emit HTML docs for failures.
  2. Update `run_all_gates.py` and `hotpass qa data-quality` to delegate to the new runner.
  3. Capture output paths as artifacts in `.github/workflows/quality-gates.yml`.
- **Owner**: Data Quality pod.
- **Target**: 2025‑11‑08.

### Gap 2 — Sprint 5 automation stubs
- **Observation**: The plan calls for per-gate scripts, an MCP TA helper, and full TA orchestration, yet only `run_all_gates.py` exists and `hotpass qa ta` just checks for `IMPLEMENTATION_PLAN.md`.
- **Impact**: TA-6 ("Quality gates wired") and TA-1 ("single tool rule") are nominal; agents cannot invoke gates individually or programmatically via MCP.
- **Plan**:
  1. Add `scripts/quality/run_qg1.py` … `run_qg5.py` and expose them via `hotpass qa` subcommands.
  2. Refactor `hotpass qa ta` to execute the gate suite and return structured results; reuse in `hotpass.mcp.server` instead of shelling out.
  3. Write `tests/mcp/test_quality_gates.py` to exercise tool discovery/invocation under MCP.
  4. Update `IMPLEMENTATION_PLAN.md` checklist when CI consumes the new scripts.
- **Owner**: Platform QA pod.
- **Target**: 2025‑11‑15.

### Gap 3 — Documentation misalignment with upgraded CLI surface
- **Observation**: `docs/reference/cli.md` still leads with `uv run hotpass run`, and the reference documents promised in Sprint 4 (`docs/reference/mcp-tools.md`, `docs/reference/quality-gates.md`, `docs/reference/profiles.md`) are absent.
- **Impact**: Agents receive conflicting guidance versus `UPGRADE.md`/repo instructions, undermining QG-5 ("Docs/instruction gate").
- **Plan**:
  1. Rewrite the CLI reference to highlight `overview`, `refine`, `enrich`, `qa`, and `contracts`.
  2. Author the missing reference docs and cross-link from `.github/copilot-instructions.md` and `AGENTS.md`.
  3. Extend QG-5 to assert the presence of these references.
- **Owner**: Docs & UX pod.
- **Target**: 2025‑11‑06.

### Gap 4 — Research APIs promised but not exposed
- **Observation**: `UPGRADE.md` §9 cites `hotpass.research.search` and `.crawl`, but the package only includes internal fetchers calling an external service; no public module or CLI/MCP verb exists.
- **Impact**: Agents may attempt to call non-existent APIs, leading to runtime failures; violates the "single tool rule" clarity.
- **Plan**:
  1. Decide on exposure path: (a) implement a thin `hotpass.research` client (CLI + MCP), or (b) amend documentation to describe current fetcher-only behaviour.
  2. If pursuing (a), add deterministic-first safeguards and tests; otherwise, update all guidance to remove or reframe the claim.
  3. Track decision in `IMPLEMENTATION_PLAN.md` and `Next_Steps.md`.
- **Owner**: Research & Enrichment pod.
- **Target decision**: 2025‑11‑05.

### Gap 5 — Assert-free pytest migration incomplete
- **Observation**: Despite `docs/how-to-guides/assert-free-pytest.md` and `Next_Steps.md` actions, suites like `tests/test_config_doctor.py` still use bare `assert`.
- **Impact**: Bandit rule B101 remains at risk; violates the testing guardrail, and impacts security reviews.
- **Plan**:
  1. Identify remaining files via lint (Bandit) and `rg`.
  2. Migrate assertions to the shared `expect` helper, adding contextual messages.
  3. Update QG-5 docs checklist to confirm the migration is complete.
  4. Close the 2025‑11‑05 Next Step once the suite is clean.
- **Owner**: QA & Engineering pod.
- **Target**: 2025‑11‑12.

### Gap 6 — Next Steps backlog intersects frontier readiness
- **Observation**: `Next_Steps.md` lists open items that directly affect QG/TA closure (quality-gates hardening, mypy error reduction, lineage smoke evidence, ARC runner rehearsal).
- **Impact**: Without these, we cannot credibly claim TA completion or production readiness for platform automation.
- **Plan**:
  1. Align each open Next Step with gate/TA criteria and add owners + proof artifacts.
  2. Prioritise the three critical blockers:
     - Harden uv-based quality gates (`ci/uv-quality-gates`).
     - Reduce mypy errors from 171 → ≤ 50 ahead of type enforcement rollout.
     - Capture Marquez lineage smoke evidence with logs/screenshots.
  3. Move completed work to `Next_Steps_Log.md` per contributing guide.
- **Owner**: Respective domain leads (Platform, Engineering, QA).
- **Checkpoint**: Weekly review every Friday starting 2025‑11‑07.

## 4. Tracking & Reporting
- **Status board**: Add each gap to the project tracking board under the “Frontier Readiness” swimlane with the targets above.
- **Quality Gate linkage**: Update `IMPLEMENTATION_PLAN.md` and the CI workflow once each remediation is merged, ensuring QG summaries cite the new scripts/logs.
- **Artefact archive**: Store generated GE Data Docs, TA summaries, and MCP audit logs under `dist/quality-gates/YYYY-MM-DD/` for reproducibility.
- **Progress reviews**: Use the weekly Ops/Engineering sync to validate closure evidence and adjust dates/owners when dependencies move.

## 5. Next Actions (Codex)
1. Draft `scripts/quality/run_qg1.py` → `run_qg5.py` scaffolds and refactor `hotpass qa ta` to consume them.
2. Pair with Docs & UX to refresh CLI/MCP references and inject new pages before running QG-5 updates.
3. Coordinate with Data Quality pod on the GE runner implementation and ensure the workflow archives Data Docs outputs.

