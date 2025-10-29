# Next Steps

## Tasks

- [ ] **2025-11-05 · Platform** — Deploy GitHub ARC runner scale set to staging and exercise OIDC smoke workflow (align with infra runbooks, target week of 2025-11-04).
- [ ] **2025-12-13 · QA & Engineering** — Add regression coverage for modular pipeline stages (finalise `tests/pipeline/fixtures/` by 2025-12-09; pair nightly dry-run after CLI stress test).
- [ ] **2025-12-20 · QA** — Exercise CLI progress reporting under high-volume fixtures (generate 10k-run dataset in `tests/cli/fixtures/progress_high_volume.json` and reserve 02:00–04:00 UTC window).
- [ ] **2025-12-31 · QA** — Execute full E2E runs with canonical configuration toggles (book staging slot on 2025-12-18; reuse Prefect deployment `hotpass-e2e-staging`).
- [ ] **2025-12-31 · Engineering** — Add Prefect flow integration tests for canonical overrides (extend `tests/test_orchestration.py`; capture fixtures during the 2025-12-18 staging run alongside QA).
- [ ] **2026-01-05 · Platform** — Validate Prefect backfill deployment guardrails in staging (share staging credentials and freeze changes week of 2025-12-29 to avoid holiday overlap).
- [ ] **2026-01-15 · Engineering** — Benchmark `HotpassConfig.merge` on large payloads (run benchmarks alongside December integration tests; feed results into January ADR updates).
- [ ] **2026-01-15 · QA & Engineering** — Extend orchestrate/resolve CLI coverage for advanced profiles (draft scope by 2025-12-19; reuse CLI stress fixtures and add resolve scenarios in `tests/cli/test_resolve.py`).
- [x] **2025-10-28 · Engineering/Docs** — Implement dataset contract models, regeneration tooling, docs reference, and ADR (landed via contracts module + docs automation).
- [x] **2025-10-28 · QA & Engineering** — Add OpenLineage fallback coverage and tighten lineage typing (new `tests/test_lineage.py`, mypy cluster resolved via importlib guard).
- [ ] **2025-12-10 · Engineering/QA** — Validate Marquez compose stack and lineage emission post-instrumentation (coordinate smoke test covering CLI + Prefect flows with QA ownership).

## Steps

- [x] Bootstrap environment with `pip install -e .[dev]` (2025-10-28).
- [x] Baseline QA audit (`pytest`, `ruff`, `mypy`, `bandit`, `detect-secrets`, `uv build`) — commands rerun on 2025-10-28 with current branch; see Quality Gates for updated status notes.
- [x] Design dataset contract specification layer and registry.
- [x] Implement JSON Schema/docs regeneration workflow and associated tests.
- [x] Capture contract architecture decision and update reference docs/toctree.
- [x] Introduce Hypothesis property suites and deterministic pipeline hooks for formatting and pipeline execution (2025-10-28).
- [x] Instrument CLI and Prefect pipeline runs with OpenLineage and document Marquez quickstart (2025-12-02).
- [ ] Introduce manifest-driven Prefect deployments with CLI/docs/ADR updates (in progress 2025-10-29).

- [x] Documented ARC runner provisioning and lifecycle verification (2025-10-29).

## Deliverables

- [x] Dataset contract module under `src/hotpass/contracts/` with Pydantic and Pandera coverage (Owner: Engineering).
- [x] Deterministic schema regeneration utilities syncing `schemas/*.json` and models (Owner: Engineering).
- [x] `docs/reference/schemas.md` generated from contracts plus toctree registration (Owner: Docs/Engineering).
- [x] ADR documenting contract strategy and lifecycle (Owner: Architecture/Engineering).
- [x] Baseline orchestration payload fix ensuring `backfill`/`incremental` keys present (Owner: Engineering).
- [x] ARC runner infrastructure manifests and Terraform baseline committed under `infra/arc/` (Owner: Platform).

## Quality Gates

- [ ] Infrastructure — ARC runner smoke test workflow (`ARC runner smoke test`) reports healthy lifecycle across staging namespace.
- [ ] Tests — `pytest` (fails: import error for optional dependency `duckdb` when collecting `tests/automation/test_hooks.py`; see baseline run on 2025-12-02).【0ae58a†L1-L27】
- [ ] Format — `make qa` (fails: `ruff format --check` wants to reformat 118 files; drift predates current work, rerun 2025-12-02).【bd4b4c†L1-L119】
- [x] Types — `mypy` (pass: no issues reported in targeted modules, run 2025-12-02).【1565f3†L1-L2】
- [ ] Security — `bandit -r src -q` (low severity `B110` try/except pass persists at `src/hotpass/orchestration.py:898`, run 2025-12-02).【0ac4ca†L1-L26】
- [x] Build — `uv build` (pass: source distribution and wheel built successfully, run 2025-12-02).【91605d†L1-L136】
- [ ] Lineage — `uv run pytest tests/test_orchestration_lineage.py tests/cli/test_run_lineage_integration.py` (skipped locally pending optional dependencies `duckdb`, `polars`, `pyarrow`, and `frictionless`, run 2025-12-02).【0ae58a†L1-L27】【dacec3†L7-L11】

## Links

- `schemas/` — current frictionless contracts to be regenerated.
- `src/hotpass/orchestration.py` — pipeline payload helpers requiring baseline fix.
- `docs/index.md` — toctree needing schema reference registration.
- `docs/adr/` — ADR catalog for contract strategy addition.
- `prefect/` — manifest library consumed by the revamped deployment loader.

## Risks/Notes

- Prefect pipeline task payload fix merged; continue monitoring downstream Prefect deployments for regressions when toggling `backfill`/`incremental` flags.
- Format gate currently red because repository-wide drift predates this work; coordinate with maintainers before applying automated formatting across the codebase.
- Bandit reports tolerated `try/except/pass`; confirm acceptable risk or remediate while touching orchestration.
- Watch list: monitor uv core build availability and Semgrep CA bundle rollout for future updates (owners retained from prior plan).
- Marquez compose stack introduced for lineage verification; schedule periodic image refreshes and ensure QA smoke tests capture CLI + Prefect flows.
