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
- [x] **2025-11-01 · Docs & Engineering** — Update README/CONTRIBUTING onboarding flow (quickstarts, preflight, doc links) and sync Diátaxis landing page/navigation with new data governance assets (Data Docs, Marquez, schema/reference).【376708†L1-L40】【8c8202†L1-L93】
- [x] **2025-10-28 · Engineering/Docs** — Implement dataset contract models, regeneration tooling, docs reference, and ADR (landed via contracts module + docs automation).
- [x] **2025-10-28 · QA & Engineering** — Add OpenLineage fallback coverage and tighten lineage typing (new `tests/test_lineage.py`, mypy cluster resolved via importlib guard).
- [ ] **2025-12-10 · Engineering/QA** — Validate Marquez compose stack and lineage emission post-instrumentation (coordinate smoke test covering CLI + Prefect flows with QA ownership).
- [x] **2025-12-12 · Engineering** — Finalise OpenTelemetry bootstrap (CLI orchestrate + Prefect flows wiring, exporter toggles, shutdown guards) and land docs/ADR/tests.

## Steps

- [x] Bootstrap environment with `pip install -e .[dev]` (2025-10-28).
- [x] Baseline QA audit (`pytest`, `ruff`, `mypy`, `bandit`, `detect-secrets`, `uv build`) — commands rerun on 2025-10-29; see Quality Gates for current failures by gate.
- [x] Repository context review — README, doc structure (Diátaxis), governance roadmap, CI workflows, CODEOWNERS, and PR template catalogued to confirm documentation strategy + quality expectations (2025-10-29).【376708†L1-L40】【153305†L1-L43】【d7a74a†L1-L120】【a24b00†L1-L5】【d59c13†L1-L12】【8695aa†L1-L26】
- [x] Refreshed docs navigation, governance reference pages, README/CONTRIBUTING quickstarts, and ADR index alignment (2025-10-29).【b17fde†L1-L76】【c42979†L11-L64】【60028f†L1-L34】【f068cc†L1-L42】
- [x] Design dataset contract specification layer and registry.
- [x] Implement JSON Schema/docs regeneration workflow and associated tests.
- [x] Capture contract architecture decision and update reference docs/toctree.
- [x] Introduce Hypothesis property suites and deterministic pipeline hooks for formatting and pipeline execution (2025-10-28).
- [x] Instrument CLI and Prefect pipeline runs with OpenLineage and document Marquez quickstart (2025-12-02).
- [ ] Introduce manifest-driven Prefect deployments with CLI/docs/ADR updates (in progress 2025-10-29).
- [x] Centralise OpenTelemetry bootstrap across CLI + Prefect flows and document exporter toggles (completed 2025-12-02 with updated docs/ADR/tests).
- [x] Exercised telemetry-focused pytest suites (`tests/test_pipeline_enhanced.py`, `tests/test_telemetry_bootstrap.py`, `tests/cli/test_telemetry_options.py`) to validate bootstrap wiring (2025-12-02).【0e3de5†L1-L87】

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
- [ ] Tests — `uv run pytest --cov=src --cov=tests` (fails: import error for `hotpass.evidence`, optional dependency gap).【caccca†L1-L18】
- [x] Tests (telemetry focus) — `uv run pytest tests/test_pipeline_enhanced.py tests/test_telemetry_bootstrap.py tests/cli/test_telemetry_options.py` (pass; validates bootstrap wiring).【0e3de5†L1-L87】
- [ ] Format — `uv run ruff format --check` (fails: 118 files would be reformatted, repo-wide drift).【670e83†L1-L87】
- [ ] Lint — `uv run ruff check` (fails: import ordering and unused imports across legacy modules).【9f2dbe†L1-L73】
- [ ] Types — `uv run mypy src tests scripts` (fails: 169 errors across legacy modules, including telemetry stubs and Prefect fixtures).【571738†L1-L33】【8a3cb6†L1-L38】
- [ ] Security — `uv run bandit -r src scripts` (fails: low severity subprocess usage and try/except pass patterns).【586f55†L1-L118】
- [x] Secrets — `uv run detect-secrets scan src tests scripts` (pass: no findings).【2688f8†L1-L61】
- [x] Build — `uv run uv build` (pass: source distribution and wheel generated).【570ce6†L1-L226】
- [ ] Docs — `uv run sphinx-build -n -W -b html docs docs/_build/html` (fails: existing heading hierarchy/toctree gaps across legacy pages, unchanged by this work).【5436cb†L1-L118】
- [ ] Lineage — Dedicated lineage pytest matrix not rerun; blocked on optional dependency installation tracked under Tests gate. Refer to global pytest failure for context.【860a1f†L1-L18】

## Links

- `schemas/` — current frictionless contracts to be regenerated.
- `src/hotpass/orchestration.py` — pipeline payload helpers requiring baseline fix.
- `docs/index.md` — landing page now surfacing governance artefacts; monitor follow-up requests.
- `docs/reference/data-docs.md` & `docs/reference/schema-exports.md` — new reference pages for Data Docs + JSON Schema consumers.
- `docs/adr/index.md` — documentation strategy alignment summary.
- `prefect/` — manifest library consumed by the revamped deployment loader.

## Risks/Notes

- Prefect pipeline task payload fix merged; continue monitoring downstream Prefect deployments for regressions when toggling `backfill`/`incremental` flags.
- Format gate currently red because repository-wide drift predates this work; coordinate with maintainers before applying automated formatting across the codebase.
- Bandit reports tolerated `try/except/pass`; confirm acceptable risk or remediate while touching orchestration.
- Watch list: monitor uv core build availability and Semgrep CA bundle rollout for future updates (owners retained from prior plan).
- Marquez compose stack introduced for lineage verification; schedule periodic image refreshes and ensure QA smoke tests capture CLI + Prefect flows.
