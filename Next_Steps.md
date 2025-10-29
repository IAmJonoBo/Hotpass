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
- [x] **2025-12-08 · Engineering/Docs** — Ship `hotpass doctor` / `hotpass init` onboarding commands with docs, ADR, and regression coverage.
- [x] **2025-11-08 · Programme (Phase 1)** — Reconcile Phase 1 foundation scope with programme leads and document baseline stabilisation deliverables ahead of retro PR `operations/foundation-retro` (owner: Programme). Completed via the published retro plan and roadmap alignment.【F:docs/operations/foundation-retro.md†L1-L64】【F:docs/roadmap.md†L1-L36】
- [ ] **2025-11-12 · Engineering (Phase 2)** — Land ROADMAP T2.1 canonical dataset contracts via PR `contracts/new-dataset-schemas`, including JSON Schema exports and docs sync (owner: Engineering).【d9a97b†L8-L16】【7786e5†L36-L53】
- [x] **2025-11-15 · QA & Docs (Phase 2)** — Close ROADMAP T2.2 Great Expectations gate hardening with PR `docs/data-governance-nav` and associated checkpoint automation (owners: QA & Docs). Governance navigation guide published to link Data Docs, schemas, lineage, and evidence flows.【F:docs/governance/data-governance-navigation.md†L1-L52】【F:docs/index.md†L63-L81】
- [ ] **2025-11-19 · QA (Phase 2)** — Deliver Hypothesis expansion for ROADMAP T2.3 via PR `qa/property-tests-round-two`, covering ingestion/export idempotency (owner: QA).【d9a97b†L8-L19】【7786e5†L48-L53】
- [ ] **2025-11-26 · Platform (Phase 3)** — Merge Prefect deployment manifests from PR `prefect/deployment-manifests` and validate idempotent schedules (owner: Platform).【d9a97b†L18-L24】【7786e5†L55-L63】
- [ ] **2025-11-29 · Engineering & QA (Phase 3)** — Exercise OpenLineage + Marquez hardening in follow-up to PR `observability/marquez-bootstrap`, capturing lineage QA evidence (owners: Engineering & QA).【d9a97b†L24-L29】【7786e5†L63-L72】
- [x] **2025-10-28 · Engineering (Phase 3)** — Persist refined outputs & data versioning (completed via PR `telemetry/bootstrap` follow-ons).【d9a97b†L29-L34】【7786e5†L63-L72】
- [x] **2025-10-28 · Engineering (Phase 4)** — Finalise MLflow tracking and registry (Phase 4 T4.1 complete; PR `mlflow/lifecycle`).【d9a97b†L34-L37】【7786e5†L75-L91】
- [ ] **2025-12-03 · Platform (Phase 5)** — Harden uv-based CI quality gates in PR `ci/uv-quality-gates` to unblock coverage enforcement (owner: Platform).【d9a97b†L40-L44】【7786e5†L93-L101】
- [ ] **2025-12-06 · Security (Phase 5)** — Ship PR `security/codeql-and-secrets` enabling CodeQL, detect-secrets diff mode, and Bandit SARIF (owner: Security).【d9a97b†L44-L47】【7786e5†L101-L108】
- [ ] **2025-12-09 · Platform (Phase 5)** — Enable Docker buildx cache reuse through PR `ci/docker-cache` (owner: Platform).【d9a97b†L47-L50】【7786e5†L108-L113】
- [ ] **2025-12-13 · Platform (Phase 5)** — Publish SBOM + SLSA attestations via PR `supply-chain/provenance` (owner: Platform).【d9a97b†L50-L53】【7786e5†L108-L113】
- [ ] **2025-12-18 · Platform (Phase 5)** — Complete ARC runner rollout and OIDC wiring through PR `infra/arc-rollout`, coordinating with QA for smoke tests (owner: Platform).【d9a97b†L53-L56】【7786e5†L93-L101】
- [ ] **2025-12-20 · Engineering (Phase 5)** — Finalise OpenTelemetry exporter propagation post-PR `telemetry/bootstrap` with additional QA sign-off (owner: Engineering).【d9a97b†L56-L59】【7786e5†L108-L113】
- [ ] **2026-01-07 · Docs & UX (Phase 6)** — Finish Diátaxis navigation uplift in PR `docs/data-governance-nav` follow-on, ensuring governance artefacts surfaced (owner: Docs & UX).【d9a97b†L59-L63】【7786e5†L111-L118】
- [ ] **2026-01-10 · Engineering & UX (Phase 6)** — Release `cli/doctor-and-init` onboarding UX refinements and regression coverage (owner: Engineering & UX).【d9a97b†L63-L66】【7786e5†L118-L125】

## Steps

- [x] Bootstrap environment with `pip install -e .[dev]` (2025-10-28).
- [x] Baseline QA audit (`pytest`, `ruff`, `mypy`, `bandit`, `detect-secrets`, `uv build`) — commands rerun on 2025-10-29; see Quality Gates for current failures by gate.
- [x] Repository context review — README, doc structure (Diátaxis), governance roadmap, CI workflows, CODEOWNERS, and PR template catalogued to confirm documentation strategy + quality expectations (2025-10-29).【376708†L1-L40】【153305†L1-L43】【d7a74a†L1-L120】【a24b00†L1-L5】【d59c13†L1-L12】【8695aa†L1-L26】
- [x] Refreshed docs navigation, governance reference pages, README/CONTRIBUTING quickstarts, and ADR index alignment (2025-10-29).【b17fde†L1-L76】【c42979†L11-L64】【60028f†L1-L34】【f068cc†L1-L42】
- [ ] Reconfirm post-PR hygiene: ensure `Next_Steps.md` updated alongside each PR hand-off as per contributing guide (rolling reminder for all owners).【2ed7b7†L71-L71】
- [x] Design dataset contract specification layer and registry.
- [x] Implement JSON Schema/docs regeneration workflow and associated tests.
- [x] Capture contract architecture decision and update reference docs/toctree.
- [x] Introduce Hypothesis property suites and deterministic pipeline hooks for formatting and pipeline execution (2025-10-28).
- [x] Instrument CLI and Prefect pipeline runs with OpenLineage and document Marquez quickstart (2025-12-02).
- [ ] Introduce manifest-driven Prefect deployments with CLI/docs/ADR updates (in progress 2025-10-29).
- [x] Centralise OpenTelemetry bootstrap across CLI + Prefect flows and document exporter toggles (completed 2025-12-02 with updated docs/ADR/tests).
- [x] Exercised telemetry-focused pytest suites (`tests/test_pipeline_enhanced.py`, `tests/test_telemetry_bootstrap.py`, `tests/cli/test_telemetry_options.py`) to validate bootstrap wiring (2025-12-02).【0e3de5†L1-L87】
- [ ] Schedule Marquez lineage smoke against `observability/marquez-bootstrap` follow-up once optional dependencies land (target 2025-11-29) using the quickstart workflow.【d9a97b†L24-L29】【b3de0d†L1-L42】
- [x] Pair platform + QA to run ARC lifecycle verification via `scripts/arc/verify_runner_lifecycle.py` and GitHub workflow smoke job ahead of PR `infra/arc-rollout` (target 2025-12-18). Snapshot scenario exercised locally with recorded output; live cluster follow-up remains on the Platform roadmap.【F:scripts/arc/examples/hotpass_arc_idle.json†L1-L12】【e5372e†L1-L3】

- [x] Documented ARC runner provisioning and lifecycle verification (2025-10-29).
- [x] Delivered CLI doctor/init onboarding workflow with targeted QA run and documentation updates (2025-12-08).【f5a08d†L1-L82】【e4f00a†L1-L3】【bf7d68†L1-L2】【cce017†L1-L23】【549e24†L1-L59】

## Deliverables

- [x] Dataset contract module under `src/hotpass/contracts/` with Pydantic and Pandera coverage (Owner: Engineering).
- [x] Deterministic schema regeneration utilities syncing `schemas/*.json` and models (Owner: Engineering).
- [x] `docs/reference/schemas.md` generated from contracts plus toctree registration (Owner: Docs/Engineering).
- [x] ADR documenting contract strategy and lifecycle (Owner: Architecture/Engineering).
- [x] Baseline orchestration payload fix ensuring `backfill`/`incremental` keys present (Owner: Engineering).
- [x] ARC runner infrastructure manifests and Terraform baseline committed under `infra/arc/` (Owner: Platform).
- [ ] Marquez lineage smoke evidence captured with screenshots/log export following quickstart (Owner: QA & Engineering).【b3de0d†L1-L42】
- [x] ARC lifecycle automation: workflow logs + `scripts/arc/verify_runner_lifecycle.py` report stored in QA artefacts (Owner: Platform). Snapshot run and sample scenario captured to unblock infrastructure rehearsal.【F:scripts/arc/examples/hotpass_arc_idle.json†L1-L12】【e5372e†L1-L3】

## Quality Gates

- [ ] Infrastructure — ARC runner smoke test workflow (`ARC runner smoke test`) reports healthy lifecycle across staging namespace (offline snapshot verification completed; awaiting staging access for live run).【e5372e†L1-L3】
- [ ] Tests — `uv run pytest --cov=src --cov=tests` (fails: import error for `hotpass.evidence`, optional dependency gap).【caccca†L1-L18】
- [x] Tests (doctor/init) — `pytest tests/cli/test_doctor_command.py tests/cli/test_init_command.py` (pass; targeted coverage for new subcommands).【f5a08d†L1-L82】
- [x] Tests (telemetry focus) — `uv run pytest tests/test_pipeline_enhanced.py tests/test_telemetry_bootstrap.py tests/cli/test_telemetry_options.py` (pass; validates bootstrap wiring).【0e3de5†L1-L87】
- [ ] Format — `uv run ruff format --check` (fails: 118 files would be reformatted, repo-wide drift).【670e83†L1-L87】
  - [x] Targeted format applied to new CLI/test modules via `ruff format` (pass).【d7b838†L1-L3】
- [ ] Lint — `uv run ruff check` (fails: import ordering and unused imports across legacy modules).【9f2dbe†L1-L73】
  - [x] Targeted lint on new modules via `ruff check` (pass).【e4f00a†L1-L3】
- [ ] Types — `uv run mypy src tests scripts` (fails: 169 errors across legacy modules, including telemetry stubs and Prefect fixtures).【571738†L1-L33】【8a3cb6†L1-L38】
  - [x] Targeted mypy for doctor/init modules and tests (pass).【bf7d68†L1-L2】
- [ ] Security — `uv run bandit -r src scripts` (fails: low severity subprocess usage and try/except pass patterns).【586f55†L1-L118】
  - [x] Targeted bandit scan for doctor/init modules (pass).【cce017†L1-L23】
- [x] Secrets — `uv run detect-secrets scan src tests scripts` (pass: no findings).【2688f8†L1-L61】
  - [x] Targeted detect-secrets scan for new CLI/tests/docs (pass).【549e24†L1-L59】
- [x] Build — `uv run uv build` (pass: source distribution and wheel generated).【570ce6†L1-L226】
- [ ] Docs — `uv run sphinx-build -n -W -b html docs docs/_build/html` (fails: existing heading hierarchy/toctree gaps across legacy pages, unchanged by this work).【5436cb†L1-L118】
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

- Prefect pipeline task payload fix merged; continue monitoring downstream Prefect deployments for regressions when toggling `backfill`/`incremental` flags.
- Format gate currently red because repository-wide drift predates this work; coordinate with maintainers before applying automated formatting across the codebase.
- Bandit reports tolerated `try/except/pass`; confirm acceptable risk or remediate while touching orchestration.
- Watch list: monitor uv core build availability and Semgrep CA bundle rollout for future updates (owners retained from prior plan).
- Marquez compose stack introduced for lineage verification; schedule periodic image refreshes and ensure QA smoke tests capture CLI + Prefect flows.
- ARC lifecycle verification rehearsed via snapshot; continue tracking live staging access to close the infrastructure gate.
