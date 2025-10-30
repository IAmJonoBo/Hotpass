# Hotpass Agent Runbook (E2E)

**Version:** 1.1  
**Date:** 2025-10-30  
**Audience:** GitHub Copilot CLI / Copilot Agent HQ / Codex (with MCP)  
**Goal:** upgrade Hotpass so agents can, from natural language, refine a spreadsheet, enrich or double-check a row, and enforce data-quality gates — all through one CLI and one MCP surface.  
**Supersedes:** `UPGRADE_B.md` and `GAP_ANALYSIS_30_10_25.md`; this runbook is now the canonical plan.

---

## 0. Executive Summary (Updated 2025-10-30)

- **Completed**  
  - CLI & MCP parity is live: the new command set ships under `src/hotpass/cli/commands/` and the stdio server in `src/hotpass/mcp/server.py` exposes `hotpass.refine`, `hotpass.enrich`, `hotpass.qa`, `hotpass.explain_provenance`, `hotpass.crawl` (guarded), and `hotpass.ta.check`.  
  - Quality gates QG‑1 → QG‑5 now run end-to-end via `scripts/quality/run_qg*.py`, `scripts/quality/run_all_gates.py`, and the GitHub workflow `.github/workflows/quality-gates.yml`.  
  - Supply-chain automation publishes SBOM, provenance, and checksums directly from `.github/workflows/process-data.yml`, backed by `scripts/supply_chain/` utilities.  
- **In progress**  
  - Adaptive research orchestrator and research MCP verbs remain to be implemented (`hotpass.crawl` currently returns a placeholder and no `hotpass.plan.research` exists).  
  - Profile-first linkage and assertion migration require additional coverage; the `expect()` helper is present but bare `assert` calls remain in several tests.  
  - Docs navigation uplift and long-tail telemetry/performance benchmarking are partially complete and need follow-on sign-offs.  
- **Blockers / dependencies**  
  - Staging access is still required to capture live Marquez lineage evidence and ARC runner smoke logs.  
  - Docker buildx cache reuse work has not begun; pipeline cost reductions remain blocked pending that PR.  
  - Adaptive research enhancements depend on defining provider rate limits and human-in-the-loop guardrails before enabling network defaults.

---

## 1. Implementation Status Dashboard

### 1.1 Next Steps alignment (tasks)

| Item | Due | Owner | Status | Evidence / Notes |
| --- | --- | --- | --- | --- |
| Confirm Phase 5 T5.5 completion against programme expectations | 2025-12-30 | Programme | Pending sign-off | Roadmap milestone is marked complete, but stakeholder confirmation is outstanding (`ROADMAP.md`). |
| Execute full E2E runs with canonical configuration toggles | 2025-12-31 | QA | Open | Requires running `uv run hotpass overview/refine/enrich/qa` with `hotpass-e2e-staging`; no artefact recorded yet. |
| Validate Prefect backfill deployment guardrails in staging | 2026-01-05 | Platform | In progress | Prefect manifests exist (`prefect/backfill.yaml`, `prefect/refinement.yaml`); staging validation still pending. |
| Benchmark `HotpassConfig.merge` on large payloads | 2026-01-15 | Engineering | Not started | No benchmark harness or artefact committed. |
| Extend orchestrate/resolve CLI coverage for advanced profiles | 2026-01-15 | Engineering & QA | In progress | Resolve command exists (`src/hotpass/cli/commands/resolve.py`), but advanced profile fixtures/tests remain to be authored. |
| Merge Prefect deployment manifests and validate idempotent schedules | 2025-11-26 | Platform | Complete | Manifests landed (`prefect/backfill.yaml`, `prefect/refinement.yaml`) and CLI deployment tests cover overrides (`tests/cli/test_deploy_command.py`). |
| Exercise OpenLineage + Marquez hardening follow-up | 2025-11-29 | Engineering & QA | Blocked on staging | Compose stack and tests ready (`tests/infrastructure/test_marquez_stack.py`, `tests/test_lineage.py`); waiting for staging lineage smoke. |
| Harden uv-based CI quality gates | 2025-12-03 | Platform | Complete | Gate scripts orchestrated in `scripts/quality/run_qg*.py`; workflow `.github/workflows/quality-gates.yml` enforces them. |
| Ship CodeQL + secrets scanning | 2025-12-06 | Security | Complete | Workflows `.github/workflows/codeql.yml` and `.github/workflows/secret-scanning.yml` active; SARIF uploads configured. |
| Enable Docker buildx cache reuse | 2025-12-09 | Platform | Not started | No `ci/docker-cache` workflow yet; caching remains manual. |
| Publish SBOM + SLSA attestations | 2025-12-13 | Platform | Complete | `.github/workflows/process-data.yml` `supply-chain` job runs `scripts/supply_chain/generate_sbom.py` / `generate_provenance.py` and uploads artefacts. |
| Complete ARC runner rollout and OIDC wiring | 2025-12-18 | Platform | In progress | ARC manifests and smoke workflow exist (`infra/arc/runner-scale-set.yaml`, `.github/workflows/arc-ephemeral-runner.yml`, `scripts/arc/verify_runner_lifecycle.py`); live staging rehearsal pending access. |
| Finalise OpenTelemetry exporter propagation | 2025-12-20 | Engineering | Complete | Telemetry bootstrap integrated in CLI (`src/hotpass/cli/shared.py`, `src/hotpass/cli/commands/run.py`, `src/hotpass/telemetry/bootstrap.py`). |
| Finish Diátaxis navigation uplift follow-on | 2026-01-07 | Docs & UX | In progress | Navigation doc merged (`docs/governance/data-governance-navigation.md`) and surfaced via `docs/index.md`; follow-on UX review scheduled. |
| Release `cli/doctor` + `cli/init` onboarding refinements | 2026-01-10 | Engineering & UX | Complete | Commands and docs shipped (`src/hotpass/cli/commands/doctor.py`, `docs/reference/cli.md`). |

### 1.2 Next Steps — hygiene, steps, and deliverables

- **PR hygiene reminder** — ongoing rolling reminder. Continue updating `Next_Steps.md` after each PR hand-off.
- **Manifest-driven Prefect deployments** — manifests are committed; remaining work is staging validation plus doc update in `docs/how-to-guides/prefect-manifests.md` (todo).
- **Marquez lineage smoke scheduling** — blocked until optional dependencies land on staging; track via `tests/infrastructure/test_marquez_stack.py` and staging access ticket.
- **Assertion migration (due 2025-11-05)** — partially complete; 36 suites still contain bare `assert` (e.g. `tests/test_evidence.py`).
- **Telemetry/mypy audit (due 2025-11-07)** — first pass removed six mypy issues; remaining errors ~171 (run `uv run mypy src tests scripts`).

**Deliverable status**

- **Marquez lineage smoke evidence** — instrumentation and automated checks exist, but live evidence (logs/screenshots) still outstanding pending staging access.

**Quality gate status**

- **QG‑1 (CLI integrity)** — ✅ Passing via `scripts/quality/run_qg1.py` and workflow job.
- **QG‑2 (Data quality)** — ✅ Passing locally/CI; outputs archived under `dist/quality-gates/qg2-data-quality`.
- **QG‑3 (Enrichment chain)** — ✅ Passing using deterministic fixtures in `tests/cli/test_quality_gates.py::TestQG3EnrichmentChain`.
- **QG‑4 (MCP discoverability)** — ✅ Passing; MCP server exposes tool list via stdio and gate script asserts presence.
- **QG‑5 (Docs/instructions)** — ✅ Passing; instructions verified by gate script and CI job.

### 1.3 Gap closure tracker (from 30 Oct audit)

| Gap | Status | Evidence | Next action |
| --- | --- | --- | --- |
| QG‑2 only performed schema checks | Resolved | `scripts/quality/run_qg2.py` runs full GE checkpoints; uploads in `.github/workflows/quality-gates.yml`. | Monitor GE dependency availability; ensure sample workbooks stay in `data/`. |
| Sprint 5 automation stubs | Resolved with follow-ups | Gate scripts and MCP `hotpass.ta.check` implemented (`scripts/quality/run_qg*.py`, `src/hotpass/mcp/server.py`); `hotpass.qa` delegates to scripts (`src/hotpass/cli/commands/qa.py`). | Implement real crawler handler for `hotpass.crawl` and add MCP integration tests. |
| Documentation misalignment | Resolved | CLI reference refreshed (`docs/reference/cli.md`), instructions mention core verbs in `.github/copilot-instructions.md` & `AGENTS.md`. | Extend reference set with MCP/quality gate pages. |
| Research APIs promised but not exposed | Outstanding | No public `hotpass.research` CLI/MCP wrapper; `_run_crawl` is placeholder (`src/hotpass/mcp/server.py`). | Decide on HTTP client surface vs documentation downgrade; implement CLI/MCP verbs accordingly. |
| Assert-free pytest migration incomplete | Outstanding | Bare asserts present (e.g. `tests/test_evidence.py`). | Continue migrating to shared `expect()` helper per `docs/how-to-guides/assert-free-pytest.md`. |
| Next Steps backlog alignment | Ongoing | This dashboard now mirrors outstanding work; maintain weekly review cadence (starting 2025-11-07). | Update `Next_Steps.md` & this section after each closure. |

### 1.4 Strategic enhancements (from `UPGRADE_B.md`)

| Enhancement | Status | Notes |
| --- | --- | --- |
| Research-first positioning across docs/README | In progress | README/landing copy still emphasises refinement over research; update messaging once orchestrator lands. |
| Adaptive research orchestrator module (`src/hotpass/research/orchestrator.py`) | Not started | Deterministic fetchers exist but no orchestrator module or planner loop yet. |
| Relationship & identity mapping (Splink, graph view) | Partially delivered | Linkage module active (`src/hotpass/linkage/`); need profile-driven graph export and UI hooks. |
| Agent-native research planning tools (`hotpass.plan.research`, MCP hooks, audit log) | Not started | MCP server lacks plan tool; `.hotpass/mcp-audit.log` not yet written. |
| Live spreadsheet UI with provenance badges | Not started | Streamlit dashboard exists in legacy branch only; no AG Grid / Handsontable integration here. |
| CLI export formats (`--export xlsx,csv,pipe`) | Not started | CLI presently writes XLSX/CSV explicitly; expose shared export flag and docs. |
| Frontier-grade guarantees (single system, adaptive research, provenance, human-in-loop) | Dependent | Achieved partially through CLI+MCP parity and quality gates; full guarantee requires orchestrator, UI, and audit hooks above. |

---

## 2. Sprint Plan (phased roadmap)

### Sprint 1 – CLI & MCP parity (**Status: ✅ Complete**)

- Exposed required CLI verbs under `src/hotpass/cli/commands/` and ensured `uv run hotpass overview/refine/enrich/qa/contracts` share a consistent parser.
- Implemented MCP stdio server (`src/hotpass/mcp/server.py`) registering `hotpass.refine`, `hotpass.enrich`, `hotpass.qa`, `hotpass.crawl` (guarded), `hotpass.explain_provenance`, and `hotpass.ta.check`.
- Repo instructions updated (`.github/copilot-instructions.md`, `AGENTS.md`) to describe CLI + MCP usage.
- **Quality gate:** `uv run hotpass overview` (QG‑1) enforced in CI.

### Sprint 2 – Enrichment translation (**Status: ✅ Complete, monitor placeholders**)

- Introduced deterministic and research fetchers under `src/hotpass/enrichment/fetchers/` with environment guardrails in `research.py`.
- `src/hotpass/enrichment/pipeline.py` orchestrates deterministic-first enrichment with provenance tracking (`provenance.py`).
- CLI `hotpass enrich` implements `--allow-network` toggle aligned with env flags.
- **Quality gate:** `uv run hotpass enrich --allow-network=false` run in QG‑3; research fetchers currently contain placeholder API integrations.

### Sprint 3 – Profiles & compliance unification (**Status: ⚠️ In progress**)

- Profile linter (`tools/profile_lint.py`) validates ingest/refine/enrich/compliance blocks.
- Contract tests and Great Expectations suites validate active profiles.
- Remaining work: finish assertion migration, extend `docs/reference/profiles.md`, and wire profile validation output into QG summary.

### Sprint 4 – Docs & agent UX (**Status: ✅ Complete with follow-ons**)

- Docs refreshed (`docs/reference/cli.md`, `.github/copilot-instructions.md`, `AGENTS.md`) and MCP instructions included.
- Additional work planned: navigation uplift QA (due 2026-01-07) and agent walkthrough updates tied to adaptive research features.

### Sprint 5 – Technical Acceptance automation (**Status: ⚠️ In progress**)

- Gate scripts and `hotpass qa ta` delegate to `scripts/quality/run_all_gates.py`.
- MCP `hotpass.ta.check` calls the consolidated runner.
- Outstanding: implement real crawler tool, add MCP integration tests, and tighten TA reporting to emit structured JSON artefacts.

### Sprint 6 – Adaptive research orchestrator (**Status: 🚧 Planned**)

- Deliver `src/hotpass/research/orchestrator.py` implementing the 5-step loop (local/authority → OSS extraction → native crawl → backfill → stop condition).
- Add rate-limited Scrapy/Playwright pipelines, provenance annotations, and profile-driven authority_sources.
- Expose MCP tool (`hotpass.plan.research`) and CLI wrappers; log to `./.hotpass/mcp-audit.log`.

### Sprint 7 – Agent-first UI & exports (**Status: 🚧 Planned**)

- Embed Streamlit dashboard with AG Grid / Handsontable status matrix, provenance badges, and re-run controls.
- Require human approval for low-confidence merges and network escalation.
- Surface multi-format exports via shared `--export` flag; extend docs and tests.

---

## 3. CLI & MCP Contract

Hotpass must keep the CLI surface predictable and short-form to suit Copilot/Codex planners.

### 3.1 Canonical CLI verbs

```
uv run hotpass overview
uv run hotpass refine --input-dir ./data --output-path ./dist/refined.xlsx --profile <profile> --archive
uv run hotpass enrich --input ./dist/refined.xlsx --output ./dist/enriched.xlsx --profile <profile> --allow-network=<true|false>
uv run hotpass qa <target>
uv run hotpass contracts emit --profile <profile>
```

- `overview` lists available commands, profiles, and quick start hints.
- `refine` runs deterministic cleaning using the selected profile.
- `enrich` performs deterministic-first enrichment, promoting network fetchers only when `--allow-network=true` and environment flags permit.
- `qa` targets (`all`, `cli`, `contracts`, `docs`, `profiles`, `fitness`, `data-quality`, `ta`) and delegates to gate scripts.
- `contracts emit` regenerates governed schemas for downstream consumers.

### 3.2 MCP tooling requirements

Expose the same capabilities via MCP stdio:

| Tool | Purpose | Notes |
| --- | --- | --- |
| `hotpass.refine` | Shells to CLI refine | Accepts `input_path`, `output_path`, `profile`, `archive`. |
| `hotpass.enrich` | Shells to CLI enrich | Honors `allow_network` and env guardrails. |
| `hotpass.qa` | Runs `hotpass qa <target>` | Default `target="all"`. |
| `hotpass.crawl` | Reserved for research orchestrator | Currently returns placeholder response; implement during Sprint 6. |
| `hotpass.explain_provenance` | Reads provenance columns for a row | Works on XLSX outputs with provenance fields. |
| `hotpass.ta.check` | Runs consolidated quality gates | Optional `gate` argument filters to a specific gate. |

Ensure `tools/list` returns the full tool set and that the server logs tool invocations (future: write to `./.hotpass/mcp-audit.log` once implemented).

---

## 4. Adaptive Research Orchestrator (planned work)

To make Hotpass research-first, implement a planner under `src/hotpass/research/orchestrator.py` with the following loop:

1. **Local & authority pass** — reuse existing refined outputs, archives, and authority sources declared per profile (extend profile schema with `authority_sources` and historical lookup hints).
2. **OSS-first extraction** — try Playwright + `trafilatura` / `readability-lxml`, `unstructured`, `pdfplumber` before invoking vendor APIs.
3. **Hotpass native crawl** — embed Scrapy + Playwright-based crawlers with per-domain concurrency caps, robots.txt compliance, and provenance events.
4. **Backfill retry** — only for profile-approved fields; mark provenance entries with `strategy=backfill` and capture warnings when falling back to general web.
5. **Stop condition** — emit low-confidence result when the loop exhausts options.

Deliverables:

- Orchestrator module and tests.
- Profile schema updates documenting authority/backfill behaviour.
- Rate limiting via Prefect or internal semaphores.
- CLI/MCP wrappers (`hotpass plan.research`, `hotpass.crawl` real implementation).
- Provenance annotations (source, timestamp, confidence, strategy, network usage).

---

## 5. Relationship & Identity Mapping

Existing linkage tooling (`src/hotpass/linkage/`) provides Splink + RapidFuzz matching with Label Studio integration.

Focus areas:

- Integrate linkage results into enrichment provenance and orchestrator decisions.
- Extend profiles with identity configuration (e.g. `identity.match_on`, `identity.resolver`, `identity.backfill_from_related`).
- Surface graph exports or review artefacts via CLI (`hotpass resolve --export-graph`) and Streamlit UI.
- Ensure Label Studio connector records reviewer decisions and merges them back into datasets.

---

## 6. Agent UX, UI, and Human-in-the-loop

Planned enhancements:

- Streamlit dashboard upgrade with AG Grid/Handsontable for live status:
  - Colour legend: pending (grey), refined (green), enriched deterministic (blue), enriched network (orange), backfilled low confidence (red).
  - Buttons to rerun adaptive research with expanded budget.
  - Inline warnings for crawler rate limits and provenance anomalies.
- Approval workflow:
  - Require human approval for low-confidence merges, enabling network fetchers, and probabilistic matches below configurable Splink threshold.
  - Record approvals in audit log for compliance review.

---

## 7. Data Quality Gates & Automation

Quality gates guard every stage:

| Gate | Command | Pass criteria | Artefact |
| --- | --- | --- | --- |
| QG‑1 CLI integrity | `scripts/quality/run_qg1.py` | CLI verbs present, help text works | Summary JSON under `dist/quality-gates/qg1-cli-integrity`. |
| QG‑2 Data quality | `scripts/quality/run_qg2.py` | GE checkpoints succeed; Data Docs generated | Data Docs archived under `dist/quality-gates/qg2-data-quality/<timestamp>/`. |
| QG‑3 Enrichment chain | `scripts/quality/run_qg3.py` | Deterministic enrichment produces output with provenance; network skipped when disabled | Test fixtures under `tests/data/`. |
| QG‑4 MCP discoverability | `scripts/quality/run_qg4.py` | MCP server lists required tools | JSON summary from gate script. |
| QG‑5 Docs/instructions | `scripts/quality/run_qg5.py` | Instruction files present and contain key phrases | Summary JSON plus optional markdown excerpts. |

Use `scripts/quality/run_all_gates.py --json` for consolidated runs (called by `hotpass qa ta` and MCP `hotpass.ta.check`). Ensure workflow artefacts remain accessible for audits.

---

## 8. Technical Acceptance Criteria

TA is achieved when:

1. **Single-tool rule** — All user-facing operations route through `uv run hotpass ...` or MCP equivalents (validated via QG‑1/QG‑4).
2. **Profile completeness** — Every profile includes ingest/refine/enrich/compliance blocks validated by `tools/profile_lint.py` and QG‑2.
3. **Offline-first enrichment** — `hotpass enrich --allow-network=false` succeeds with provenance showing network disabled.
4. **Network safety** — Respect `FEATURE_ENABLE_REMOTE_RESEARCH` and `ALLOW_NETWORK_RESEARCH`; provenance notes when network skipped.
5. **MCP parity** — All CLI verbs exposed via MCP and listed in `tools/list`.
6. **Quality gates wired** — QG‑1 → QG‑5 runnable locally and in CI, with artefacts uploaded.
7. **Docs ready** — `.github/copilot-instructions.md` and `AGENTS.md` emphasise profile-first, deterministic-first, provenance.

Failing any TA item should block releases until scripts/docs/tests are corrected and gates rerun.

---

## 9. Research, Investigation, and Backfilling Mode

Agents must support both local and remote research pipelines:

1. **Authority-first search** — Profiles declare preferred registries/directories; orchestrator hits them before web.
2. **Deterministic enrichments** — Use local lookup tables, historical archives, and derived fields (already implemented via deterministic fetchers).
3. **Adaptive research (planned)** — Once orchestrator lands, promote network crawlers only when flags permit and budgets allow.
4. **Backfill control** — Only mutate fields the profile marks as backfillable; preserve originals and record provenance with strategy/backfill confidence.
5. **Entity resolution loop** — Re-run linkage when enrichment introduces conflicting data; integrate Splink results and reviewer decisions.

Post-research, rerun `uv run hotpass qa all` and invoke `hotpass.explain_provenance` to keep the audit trail complete.

---

## 10. Search Strategies & Source Prioritisation

1. **Authority sources first** — Regulator, government, or profile-declared authority endpoints.
2. **Focused Hotpass research search** — (Planned) `hotpass.plan.research` and future `hotpass.research.search` should query provider APIs with temporal filters.
3. **Temporal filtering** — Restrict to recent results for volatile data (past day/week/month).
4. **Structural crawl** — Use deterministic crawler or orchestrator step to map unknown site structures within rate limits.
5. **Exhaustive sweep** — Broader web search only when higher authority sources fail; emit warnings when using general web data.

Always validate results via GE expectations and provenance metadata.

---

## 11. Threat Model & Hardening

- Restrict MCP tool exposure to Hotpass plus required GitHub defaults; avoid enabling unrelated tools.
- Require explicit user approval for filesystem/network actions (aligned with Copilot CLI security posture).
- Implement prompt-injection guardrails: detect instructions that attempt to disable validation or leak secrets; log and abort.
- Log MCP tool calls (planned path: `./.hotpass/mcp-audit.log`) with timestamps, arguments, and outcomes for compliance.
- Honour environment-controlled network toggles; never fetch remote data when disabled.
- On Windows deployments, keep MCP server bound to stdio/local named pipe and rely on OS prompts for consent.

---

## 12. OSS-first Extractors & Fallbacks

Maintain vendor-neutral extraction defaults:

- HTML → text: prefer `trafilatura` or `readability-lxml`.
- JS-heavy: render with Playwright headless (possibly via `scrapy-playwright`).
- Bulk/domain jobs: schedule focused crawls with Scrapy/Crawlee; store raw HTML/JSONL under `./.hotpass/cache/`.
- Documents/PDF: convert using `unstructured` or `pdfplumber` before enrichment.
- Data quality expansion: integrate Soda Core or whylogs alongside Great Expectations if additional drift checks are required.

Only escalate to third-party/vendor APIs after OSS paths fail or when profiles explicitly opt in.

---

This runbook is the single source of truth for Hotpass upgrades. Update it whenever tasks close (alongside `Next_Steps.md`, `ROADMAP.md`, and `IMPLEMENTATION_PLAN.md`) and archive superseded artefacts rather than letting parallel plans drift.
