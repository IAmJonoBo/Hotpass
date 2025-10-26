# Next Steps

## Tasks

- [x] Consolidate planning collateral into `docs/roadmap.md` and simplify top-level release docs (Owner: Product, Due: 2025-10-25)
- [x] Publish Diátaxis-aligned docs set with style and contributing guidance (Owner: Docs, Due: 2025-10-25)
- [x] Validate Docker image build and publish pipeline in CI (Owner: DevOps, Due: 2025-11-08)
- [x] Quieten Prefect/OpenTelemetry console handlers to prevent ValueError on process shutdown during QA tooling (Owner: Engineering, Due: 2025-11-08)
- [x] Re-enable skipped integration suites once optional dependencies can be installed in CI without instability (Owner: Engineering, Due: 2025-11-15)
- [x] Merge entity registry history during deduplication to unlock roadmap follow-up (Owner: Engineering, Due: 2025-11-01)
- [x] Add regression coverage for dashboard persistence helpers (Owner: Engineering, Due: 2025-11-01)
- [x] Confirm Streamlit dashboard authentication and hosting controls (Owner: Platform, Due: 2025-11-22)
- [x] Decide secrets management approach for registry connectors and telemetry endpoints (Owner: DevOps, Due: 2025-11-22)
- [x] Harden Streamlit dashboard authentication and filesystem allowlists (Owner: Platform, Due: 2025-11-22)
- [x] Enforce Prefect deployment parameter validation and policies (Owner: Engineering, Due: 2025-11-22)
- [x] Replace curl-pipe installer in Dockerfile with pinned, verified artefacts (Owner: DevOps, Due: 2025-11-15)
- [x] Pin GitHub Actions to commit SHAs and add artifact checksum publication (Owner: DevOps, Due: 2025-11-15)
- [x] Implement CLI log redaction strategy for PII-bearing metrics (Owner: Engineering, Due: 2025-11-22)
- [x] Improve mutation kill rate for quality/pipeline flows via additional assertions or fixtures (Owner: Engineering, Due: 2025-11-29)
- [x] Establish compliance baseline matrices and backlog (Owner: Compliance, Due: 2025-10-25)
- [x] Automate consent validation per POPIA-001 (Owner: Product & Engineering, Due: 2025-11-22)
- [x] Build comprehensive asset register per ISO27001-002 (Owner: Security & Platform, Due: 2025-11-29)
- [x] Maintain SOC 2 risk register seeded from threat model (Owner: Security, Due: 2025-11-22)
- [x] Implement Vault-backed secret delivery for CI workflows and Prefect deployments (Owner: DevOps, Due: 2025-12-06)
- [x] Capture consent validation audit logs within Prefect evidence exports (Owner: Product & Engineering, Due: 2025-12-06)
- [x] Harden refined data confidentiality controls (Owner: Platform, Due: 2025-12-13)
- [x] Launch quarterly compliance verification cadence (Owner: Compliance, Due: 2025-01-15)
- [x] Consolidate CLI and Prefect orchestration logic with structured error handling (Owner: Engineering, Due: 2025-12-13)
- [x] Remove Prefect console handler monkey patch in favour of scoped logging (Owner: Platform, Due: 2025-12-13)
- [x] Wire cron scheduling/work pool options through `deploy_pipeline` and add regression tests (Owner: Engineering, Due: 2025-12-20)
- [x] Harden entity history parsing to avoid `ast.literal_eval` and add fixtures (Owner: Engineering, Due: 2025-12-20)
- [x] Optimise geospatial distance calculations and expose actionable errors (Owner: Data, Due: 2025-12-20)
- [x] Add deterministic evidence logging tests covering consent/export helpers (Owner: Compliance & QA, Due: 2025-12-06)
- [x] Create dependency-light fixtures so enhanced CLI/geospatial/entity resolution paths run in CI (Owner: QA, Due: 2025-12-27)

## Steps

- [x] Migrated documentation to Diátaxis structure and removed duplicate legacy pages
- [x] Added docs CI workflow executing strict Sphinx builds and link checking
- [x] Refreshed README to act as a lightweight entry point into docs
- [x] Create dedicated fixtures for observability and orchestration to reduce reliance on global state between tests
- [x] Capture outcomes from docs workflow once it runs on `main` (see `uv run sphinx-build` & linkcheck outputs)【5a78d4†L1-L26】【f029ee†L1-L24】
- [x] Automated quarterly verification logging via `scripts/compliance/run_verification.py`
- [x] Executed repository-wide Ruff formatting sweep and cleared lingering lint/security warnings (2025-10-26)
- [x] Added CI artifact checksum publication alongside pinned GitHub Actions references
- [x] Restore lint/type gates after refactoring observability and orchestration modules
- [x] Implement entity registry history merge flow and regression coverage
- [x] Marked roadmap phases complete and verified enhanced pipeline package contracts
- [x] Drafted governance charter and metrics instrumentation plan to guide upcoming telemetry work
- [x] Authored Structurizr DSL architecture views and documented trust boundaries, attack surfaces, and SPOFs
- [x] Flagged dashboard auth, secrets management, CI artefact handling, and Docker distribution for follow-up interviews
- [x] Compiled multi-surface STRIDE/MITRE threat model with mitigation backlog in `docs/security/threat-model.md`
- [x] Captured compliance baseline matrices, evidence catalog, and verification plan under `docs/compliance/`
- [x] Highlighted cross-framework high-risk compliance gaps with evidence pointers in `docs/compliance/index.md`
- [x] Documented SPACE-informed developer experience audit and platform backlog
- [x] Stood up developer experience playbooks, Backstage scaffolding, and supply-chain scripts with automation entry points
- [x] Completed critical reasoning checks and consolidated upgrade handover report in `docs/governance/upgrade-final-report.md`
- [x] Enforced Prefect flow parameter validation and added regression coverage for invalid inputs
- [x] Added configurable structured log redaction with default PII masks and documented usage
- [x] Secured Streamlit dashboard behind shared-secret authentication and filesystem allowlists with regression coverage and documentation updates
- [x] Documented Vault-based secrets management strategy with rollout plan
- [x] Automated POPIA consent validation with compliance reporting and regression coverage
- [x] Linked governance and security documentation into the Diátaxis toctree and cleared Sphinx cross-reference warnings
- [x] Expanded mutation regression tests around compliance/evidence flows to raise kill rate for quality and pipeline modules
- [x] Implemented Vault-backed secret sync tooling for CI and Prefect orchestrations
- [x] Persisted consent validation audit logs and refined export access evidence with updated documentation
- [x] Resolved Vault session typing gaps so mypy accepts StubSession fixtures and aligned evidence logging timestamps with `datetime.UTC`
- [x] Captured orchestration, entity resolution, geospatial, and evidence gaps ahead of research/validation overhaul (2025-10-26)
- [x] Track remediation progress for the documented gap analysis recommendations

- [x] Vendored Semgrep ruleset to unblock static analysis in sandbox environments (2025-10-26)
- [x] Embedded dashboard remediation guidance with glossary and operations links (2025-10-26)
- [x] Suppressed Great Expectations and sqlite resource warnings under `pytest -W error` via targeted filters and cleanup (2025-11-29)【4701d5†L1-L1】【09f95e†L1-L40】
## Deliverables

- [x] `docs/` reorganised into tutorials, how-to guides, reference, explanations, roadmap, contributing, and style content
- [x] `.github/ISSUE_TEMPLATE/` populated with bug, docs, and task templates plus Slack contact link
- [x] `.github/workflows/docs.yml` enforces strict Sphinx builds and link checking
- [x] README, implementation status, and release summary files now point to canonical roadmap documentation
- [x] Entity registry merges optional history files while preserving identifiers and status timelines
- [x] Governance gap analysis captured in `docs/governance/gap-analysis.md` (2025-10-26)
- [x] Pytest with coverage ≥ 80% (current: 87%)
- [x] Centralised runtime warning suppression module guards pytest -W error runs (`src/hotpass/_warning_filters.py`)
- [x] Top-level package exports expose the enhanced pipeline configuration for downstream clients
- [x] Ruff lint clean (`uv run ruff check`)【619137†L1-L2】
- [x] Ruff formatting clean (`uv run ruff format --check`)【fa5cfd†L1-L2】
- [x] Mypy type checks clean (`uv run mypy src tests scripts`)【ac3eaf†L1-L20】
- [x] Bandit security scan clean (`uv run bandit -r src scripts`)【689a9e†L1-L20】
- [x] Detect-secrets scan clean (`uv run detect-secrets scan src tests scripts`)【9668ed†L1-L60】
- [x] Package build succeeds (`uv run uv build`)【733457†L1-L110】
- [x] Docs build strict mode passes (`uv run sphinx-build -n -W -b html docs docs/_build/html`)【5a78d4†L1-L26】
- [x] Docs link check executes with curated ignore list (`uv run sphinx-build -b linkcheck docs docs/_build/linkcheck`)【f029ee†L1-L24】
- [x] Structurizr DSL workspace captures context, container, and component views (`docs/architecture/hotpass-architecture.dsl`)
- [x] Governance charter recorded in `docs/governance/project-charter.md`; metrics instrumentation captured in `docs/metrics/metrics-plan.md`
- [x] Baseline QA suite re-run prior to threat modelling (`uv run pytest --cov=src --cov=tests --cov-report=term-missing`)【6cdc80†L1-L48】
- [x] Lint/type/security/build checks re-run (`uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests scripts`; `uv run bandit -r src scripts`; `uv run detect-secrets scan src tests scripts`; `uv run uv build`)【7ea5ac†L1-L2】【19132d†L1-L2】【5a1833†L1-L2】【0f1459†L1-L32】【2503e8†L1-L60】【cb9751†L1-L103】
- [x] Security threat model documented with STRIDE/MITRE mapping (`docs/security/threat-model.md`)
- [x] Compliance baseline established with matrices and backlog (`docs/compliance/index.md`, `docs/compliance/remediation-backlog.md`)
- [x] Verification cadence and evidence catalog recorded (`docs/compliance/verification-plan.md`, `docs/compliance/evidence-catalog.md`)
- [x] High-risk compliance summary table links backlog items to evidence directories (`docs/compliance/index.md`)
- [x] Developer experience audit captured (`docs/metrics/devex-audit.md`)
- [x] Supply-chain automation documented with SBOM/provenance tooling and Backstage catalog entries (`scripts/supply_chain/*`, `templates/backstage/`, `catalog-info.yaml`)
- [x] Final upgrade report published with pre-mortem, FMEA, attacker review, control matrix, and runbook (`docs/governance/upgrade-final-report.md`)
- [x] GitHub Actions workflows pinned to commit SHAs and publishing checksum manifests for refined data and supply-chain artefacts
- [x] Prefect refinement flow validates parameters via Pydantic models and rejects unsafe paths/chunk sizes with dedicated tests
- [x] Structured logging redacts configurable sensitive fields and documentation calls out the new `--sensitive-field` option
- [x] Streamlit dashboard authentication and filesystem allowlists implemented with docs, threat model, and resilience plan updates
- [x] Secrets management strategy defined with Vault rollout guidance (`docs/governance/secrets-management.md`)
- [x] Asset inventory captured in `data/inventory/asset-register.yaml` with custodians and classifications
- [x] SOC 2 risk register established with scoring and owners (`docs/security/risk-register.md`)
- [x] Enhanced pipeline enforces consent validation with overrides and compliance reporting updates
- [x] Enhanced pipeline feature orchestration extracted into helper module to satisfy fitness function limits
- [x] Consent validation audit logs persisted to `data/logs/prefect/` alongside documentation updates
- [x] Export access logs captured under `dist/logs/access/` with hashing metadata for SOC 2 evidence
- [x] Vault integration shipped for Prefect flows and CI via `hotpass.secrets` utilities and `scripts/secrets/pull_vault_secrets.py`
- [x] Quarterly verification automation script writes ledger and JSON summary (`scripts/compliance/run_verification.py`, `data/compliance/verification-log.json`)
- [x] Repository formatting normalized via `uv run ruff format` and Bandit allowlist adjustments (2025-10-26)
- [x] Shared orchestration helpers expose `PipelineRunOptions` for CLI and Prefect flows with regression coverage
- [x] Geospatial distance matrix vectorised with deterministic `GeospatialError` signalling
- [x] Evidence logging accepts deterministic clocks with dedicated tests for consent/export paths

## Quality Gates

- [x] Pytest with coverage ≥ 80% (current: 87%)【287104†L1-L80】
- [x] Ruff lint clean (`uv run ruff check`)【619137†L1-L2】
- [x] Ruff formatting clean (`uv run ruff format --check`)【fa5cfd†L1-L2】
- [x] Mypy type checks clean (`uv run mypy src tests scripts`)【ac3eaf†L1-L20】
- [x] Bandit security scan clean (`uv run bandit -r src scripts`)【689a9e†L1-L20】
- [x] Detect-secrets scan clean (`uv run detect-secrets scan src tests scripts`)【9668ed†L1-L60】
- [x] Package build succeeds (`uv run uv build`)【733457†L1-L110】
- [x] Quarterly compliance verification cadence executed (first cycle due 2025-01-15)【65fb01†L1-L3】
- [x] Accessibility smoke tests pass (`uv run pytest -m accessibility`)【1b98d5†L1-L13】
- [x] Mutation testing harness executes (`uv run python scripts/qa/run_mutation_tests.py`)【0b6520†L1-L3】
- [x] Fitness functions satisfied (`uv run python scripts/quality/fitness_functions.py`)【8eab1a†L1-L2】
- [x] SBOM generation script writes CycloneDX output (`uv run python scripts/supply_chain/generate_sbom.py`)【8b644b†L1-L2】
- [x] Provenance statement emitted (`uv run python scripts/supply_chain/generate_provenance.py`)【efd15c†L1-L2】
- [x] Semgrep static analysis (`uv run semgrep --config=policy/semgrep/hotpass.yml --metrics=off`)【467a00†L1-L24】
- [x] Compliance evidence catalog refreshed (due 2025-01-15)【F:docs/compliance/evidence-catalog.md†L13-L20】

## Links

- Tests: `uv run pytest --cov=src --cov=tests --cov-report=term-missing` (chunk `287104`)
- Lint: `uv run ruff check` (chunk `619137`)
- Format: `uv run ruff format --check` (chunk `fa5cfd`)
- Warning gate: `uv run pytest -W error --maxfail=1` (chunk `09f95e`)
- Types: `uv run mypy src tests scripts` (chunk `ac3eaf`)
- Security: `uv run bandit -r src scripts` (chunk `689a9e`)
- Secrets: `uv run detect-secrets scan src tests scripts` (chunk `9668ed`)
- Build: `uv run uv build` (chunk `733457`)
- Docs build: `uv run sphinx-build -n -W -b html docs docs/_build/html` (chunk `e173e2`)
- Docs linkcheck: `uv run sphinx-build -b linkcheck docs docs/_build/linkcheck` (chunk `2b87dd`)
- Accessibility: `uv run pytest -m accessibility` (chunk `1b98d5`)
- Mutation: `uv run python scripts/qa/run_mutation_tests.py` (chunk `0b6520`)
- Fitness functions: `uv run python scripts/quality/fitness_functions.py` (chunk `8eab1a`)
- SBOM: `uv run python scripts/supply_chain/generate_sbom.py` (chunk `8b644b`)
- Provenance: `uv run python scripts/supply_chain/generate_provenance.py` (chunk `efd15c`)
- Semgrep: `uv run semgrep --config=policy/semgrep/hotpass.yml --metrics=off` (chunk `467a00`)
- Compliance cadence: `uv run python scripts/compliance/run_verification.py --reviewer "Compliance Bot" --notes "Initial automation baseline"` (chunk `65fb01`)
- Compliance baseline: `docs/compliance/index.md`
- Compliance backlog: `docs/compliance/remediation-backlog.md`
- Verification cadence: `docs/compliance/verification-plan.md`
- Evidence catalog: `docs/compliance/evidence-catalog.md`
- DevEx audit: `docs/metrics/devex-audit.md`

## Risks / Notes

- Observability exporters now suppress shutdown ValueErrors; monitor CI logs after enabling full telemetry backends.
- Docker build validation now executes in CI via workflow docker build step; monitor runtime and cache behaviour in hosted runners.
- Prefect telemetry exporters still raise SSL errors when orchestrating flows in offline environments; needs hardened configuration or opt-out for air-gapped runs.
- Docs link checking ignores selected external domains because of certificate issues in the sandbox; confirm connectivity in GitHub-hosted runners.
- Metrics instrumentation relies on access to Prefect Orion API, Slack webhooks, and optional Four Keys stack—validate connectivity and compliance approvals before rollout.
- Trust-boundary updates highlight new follow-ups (dashboard auth, secrets handling, CI artefact retention, Docker distribution); track owners above.
- Compliance matrices highlight outstanding DSAR automation, supplier assessments, and storage hardening—monitor backlog deadlines and update evidence catalog after each delivery.
- Gap analysis surfaced orchestration duplication, logging shims, entity history parsing, geospatial scaling, and audit logging coverage gaps—see new tasks for mitigation sequencing.
- Evidence paths (`data/logs/prefect/`, `data/compliance/dsar/`, `data/inventory/`, `dist/logs/access/`) now ship with READMEs; confirm retention SLAs with Compliance and Platform owners.
- Vault strategy published; next step is implementing Vault-backed delivery for CI and Prefect plus monitoring audit logs post-cutover.
- Local Semgrep ruleset focuses on high-risk patterns (eval, shell=True); expand coverage with additional rules as the backlog evolves.
- Mutation suite now exercises observability toggles in `pipeline_enhanced`; rerun kill rate report after next mutation sweep.
- Shared-secret dashboard password still requires rotation and monitoring until SSO-backed auth replaces it; integrate Vault-issued credentials during rollout.
- Consent validation logs need exporting to evidence catalog once Prefect automation is wired up; track via new audit task.
- Quarterly verification automation now logs cadences; future runs must attach DSAR and supplier review findings to keep evidence meaningful.
- Ruff formatter drift resolved via repository-wide sweep; keep formatter gate enforced in CI and rerun after major merges.
