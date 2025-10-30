# Hotpass Guidance for AI Agents

These notes equip GitHub Copilot CLI, Copilot Agent HQ, and Codex-based agents to work safely and efficiently inside the Hotpass repository.

---

## 1. Mission Snapshot

- **What Hotpass does**: Refine messy spreadsheets, enrich them with deterministic and optional research fetchers, run relationship/linkage analysis, and publish governed outputs with provenance.
- **Primary interfaces**: The CLI (`uv run hotpass <verb>`) and the MCP stdio server (`python -m hotpass.mcp.server`) expose the same operations. MCP tools mirror the CLI verbs (`refine`, `enrich`, `qa`, `contracts`) plus provenance explainers and TA checks.
- **Default stance**: Deterministic-first, offline-safe. Network enrichment requires `FEATURE_ENABLE_REMOTE_RESEARCH=1`, `ALLOW_NETWORK_RESEARCH=1`, and the `--allow-network=true` flag.

---

## 2. Getting Started (Agent Playbook)

1. **Sync dependencies**
   ```bash
   uv venv
   export HOTPASS_UV_EXTRAS="dev orchestration enrichment"
   bash scripts/uv_sync_extras.sh
   ```
2. **Discover the surface**
   ```bash
   uv run hotpass overview
   ```
   Confirm that `refine`, `enrich`, `qa`, and `contracts` appear.
3. **Run the core pipeline**
   ```bash
   uv run hotpass refine \
     --input-dir ./data \
     --output-path ./dist/refined.xlsx \
     --profile generic \
     --archive
   ```
4. **Optionally enrich deterministically**
   ```bash
   uv run hotpass enrich \
     --input ./dist/refined.xlsx \
     --output ./dist/enriched.xlsx \
     --profile generic \
     --allow-network=false
   ```
5. **Execute quality gates**
   ```bash
   uv run hotpass qa all
   ```
6. **Expose MCP tools (when needed)**
   ```bash
   uv run python -m hotpass.mcp.server
   ```
   Use `/mcp list` (Copilot CLI) to verify `hotpass.refine`, `hotpass.enrich`, `hotpass.qa`, `hotpass.explain_provenance`, `hotpass.crawl`, and `hotpass.ta.check`.

---

## 3. Repository Map

- `src/hotpass/cli/commands/` — CLI entry points (`overview`, `refine`, `enrich`, `qa`, `contracts`, `resolve`, etc.). Extend parsers here and keep help text concise.
- `src/hotpass/enrichment/` — Deterministic and research fetchers, pipeline orchestration, and provenance tracking.
- `src/hotpass/linkage/` — Splink/RapidFuzz entity resolution with optional Label Studio review queues.
- `src/hotpass/mcp/server.py` — MCP stdio server implementation; mirrors CLI behaviour. Update tool registration when adding new verbs.
- `scripts/quality/` — Quality gate runners (`run_qg*.py`, `run_all_gates.py`) referenced by CI and `hotpass qa`.
- `docs/` — MyST/Sphinx documentation organised by Diátaxis; `docs/reference/cli.md` is the authoritative CLI spec.
- `tests/` — Pytest suites using the shared `expect(condition, message)` helper (no bare `assert`).

---

## 4. QA & Safety Checklist

- **Before PRs**: run `make qa`, `uv run hotpass qa all`, and `uv run python scripts/validation/refresh_data_docs.py`.
- **Quality gates**: QG‑1 → QG‑5 must stay green. Use `scripts/quality/run_all_gates.py --json` for structured summaries or call `hotpass.ta.check` via MCP.
- **Testing conventions**: Replace bare `assert` with `expect(...)` (see `docs/how-to-guides/assert-free-pytest.md`). Keep fixtures under `tests/data` and `tests/fixtures`.
- **Optional dependencies**: Handle missing Great Expectations, Prefect, Splink, requests, trafilatura, etc. gracefully. Never import them at module top level without guards.
- **Security**: Respect POPIA compliance helpers, provenance schema, and audit logging. When touching network code, honour environment toggles and rate-limit guidance.

---

## 5. Agent Guardrails

- Never request or print secrets; rely on environment variables.
- Honour network policy: run deterministic enrichment first; escalate to network fetchers only when explicitly enabled.
- Keep CLI output succinct. Help text should highlight required flags and the `--profile` expectation.
- Log MCP tool invocations when extending the server (planned location: `./.hotpass/mcp-audit.log`).
- Validate documentation updates alongside behavioural changes (`docs/reference/cli.md`, `AGENTS.md`, `UPGRADE.md`).

---

## 6. Key References

- `UPGRADE.md` — Canonical roadmap and sprint plan.
- `Next_Steps.md` — Date-bound tasks and ownership.
- `docs/reference/cli.md` — Full CLI option matrix.
- `docs/reference/data-docs.md` & `dist/quality-gates/` — Validation artefacts.
- `.github/workflows/quality-gates.yml` — CI implementation of QG‑1 → QG‑5.

Keep this file aligned with the runbook. When CLI or MCP surfaces change, update this guidance, `AGENTS.md`, and `UPGRADE.md` in the same PR.
