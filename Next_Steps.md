# Next Steps

## Tasks

- [ ] **2025-12-13 · QA & Engineering** — Add regression coverage for modular pipeline stages (finalise `tests/pipeline/fixtures/` by 2025-12-09; pair nightly dry-run after CLI stress test).
- [ ] **2025-12-20 · QA** — Exercise CLI progress reporting under high-volume fixtures (generate 10k-run dataset in `tests/cli/fixtures/progress_high_volume.json` and reserve 02:00–04:00 UTC window).
- [ ] **2025-12-31 · QA** — Execute full E2E runs with canonical configuration toggles (book staging slot on 2025-12-18; reuse Prefect deployment `hotpass-e2e-staging`).
- [ ] **2025-12-31 · Engineering** — Add Prefect flow integration tests for canonical overrides (extend `tests/test_orchestration.py`; capture fixtures during the 2025-12-18 staging run alongside QA).
- [ ] **2026-01-05 · Platform** — Validate Prefect backfill deployment guardrails in staging (share staging credentials and freeze changes week of 2025-12-29 to avoid holiday overlap).
- [ ] **2026-01-15 · Engineering** — Benchmark `HotpassConfig.merge` on large payloads (run benchmarks alongside December integration tests; feed results into January ADR updates).
- [ ] **2026-01-15 · QA & Engineering** — Extend orchestrate/resolve CLI coverage for advanced profiles (draft scope by 2025-12-19; reuse CLI stress fixtures and add resolve scenarios in `tests/cli/test_resolve.py`).
- [x] **2025-10-28 · Engineering/Docs** — Implement dataset contract models, regeneration tooling, docs reference, and ADR (landed via contracts module + docs automation).

## Steps

- [x] Bootstrap environment with `pip install -e .[dev]` (2025-10-28).
- [ ] Baseline QA audit (`pytest`, `ruff`, `mypy`, `bandit`, `detect-secrets`, `uv build`) — failing due to pre-existing defects (see Quality Gates).
- [x] Design dataset contract specification layer and registry.
- [x] Implement JSON Schema/docs regeneration workflow and associated tests.
- [x] Capture contract architecture decision and update reference docs/toctree.

## Deliverables

- [x] Dataset contract module under `src/hotpass/contracts/` with Pydantic and Pandera coverage (Owner: Engineering).
- [x] Deterministic schema regeneration utilities syncing `schemas/*.json` and models (Owner: Engineering).
- [x] `docs/reference/schemas.md` generated from contracts plus toctree registration (Owner: Docs/Engineering).
- [x] ADR documenting contract strategy and lifecycle (Owner: Architecture/Engineering).
- [x] Baseline orchestration payload fix ensuring `backfill`/`incremental` keys present (Owner: Engineering).

## Quality Gates

- [x] Tests — `pytest --cov=src --cov=tests --cov-report=term-missing` (pass: 341 passed, 5 skipped, 38 warnings in 93.88s; run 2025-10-28).
- [ ] Lint — `ruff check` (fails: extensive legacy violations across CLI/pipeline modules; latest run 2025-10-28 still reports 100+ issues despite contracts cleanup).
- [ ] Format — `ruff format --check` (fails: 111 files require formatting, run 2025-10-28).
- [ ] Types — `mypy src tests scripts` (fails: 219 errors across repo, run 2025-10-28).
- [ ] Security — `bandit -r src scripts` (low severity `B110` try/except pass in `src/hotpass/orchestration.py:849`, run 2025-10-28).
- [x] Secrets — `python -m detect_secrets scan src tests scripts` (pass, run 2025-10-28).
- [x] Build — `uv build` (pass, run 2025-10-28).

## Links

- `schemas/` — current frictionless contracts to be regenerated.
- `src/hotpass/orchestration.py` — pipeline payload helpers requiring baseline fix.
- `docs/index.md` — toctree needing schema reference registration.
- `docs/adr/` — ADR catalog for contract strategy addition.

## Risks/Notes

- Prefect pipeline task payload fix merged; continue monitoring downstream Prefect deployments for regressions when toggling `backfill`/`incremental` flags.
- Repository-wide Ruff formatting and mypy checks are failing pre-change; large remediation backlog may require phased plan.
- Bandit reports tolerated `try/except/pass`; confirm acceptable risk or remediate while touching orchestration.
- Watch list: monitor uv core build availability and Semgrep CA bundle rollout for future updates (owners retained from prior plan).
