# Next Steps

## Tasks

- [x] Consolidate planning collateral into `docs/roadmap.md` and simplify top-level release docs (Owner: Product, Due: 2025-10-25)
- [x] Publish Diátaxis-aligned docs set with style and contributing guidance (Owner: Docs, Due: 2025-10-25)
- [ ] Validate Docker image build and publish pipeline in CI (Owner: DevOps, Due: 2025-11-08)
- [x] Quieten Prefect/OpenTelemetry console handlers to prevent ValueError on process shutdown during QA tooling (Owner: Engineering, Due: 2025-11-08)
- [ ] Re-enable skipped integration suites once optional dependencies can be installed in CI without instability (Owner: Engineering, Due: 2025-11-15)
- [x] Merge entity registry history during deduplication to unlock roadmap follow-up (Owner: Engineering, Due: 2025-11-01)
- [x] Add regression coverage for dashboard persistence helpers (Owner: Engineering, Due: 2025-11-01)
- [ ] Confirm Streamlit dashboard authentication and hosting controls (Owner: Platform, Due: 2025-11-22)
- [ ] Decide secrets management approach for registry connectors and telemetry endpoints (Owner: DevOps, Due: 2025-11-22)
- [ ] Harden Streamlit dashboard authentication and filesystem allowlists (Owner: Platform, Due: 2025-11-22)
- [ ] Enforce Prefect deployment parameter validation and policies (Owner: Engineering, Due: 2025-11-22)
- [ ] Replace curl-pipe installer in Dockerfile with pinned, verified artefacts (Owner: DevOps, Due: 2025-11-15)
- [ ] Pin GitHub Actions to commit SHAs and add artifact checksum publication (Owner: DevOps, Due: 2025-11-15)
- [ ] Implement CLI log redaction strategy for PII-bearing metrics (Owner: Engineering, Due: 2025-11-22)
- [x] Establish compliance baseline matrices and backlog (Owner: Compliance, Due: 2025-10-25)
- [ ] Automate consent validation per POPIA-001 (Owner: Product & Engineering, Due: 2025-11-22)
- [ ] Build comprehensive asset register per ISO27001-002 (Owner: Security & Platform, Due: 2025-11-29)
- [ ] Maintain SOC 2 risk register seeded from threat model (Owner: Security, Due: 2025-11-22)
- [ ] Harden refined data confidentiality controls (Owner: Platform, Due: 2025-12-13)
- [ ] Launch quarterly compliance verification cadence (Owner: Compliance, Due: 2025-01-15)

## Steps

- [x] Migrated documentation to Diátaxis structure and removed duplicate legacy pages
- [x] Added docs CI workflow executing strict Sphinx builds and link checking
- [x] Refreshed README to act as a lightweight entry point into docs
- [x] Create dedicated fixtures for observability and orchestration to reduce reliance on global state between tests
- [ ] Capture outcomes from docs workflow once it runs on `main`
- [x] Restore lint/type gates after refactoring observability and orchestration modules
- [x] Implement entity registry history merge flow and regression coverage
- [x] Marked roadmap phases complete and verified enhanced pipeline package contracts
- [x] Drafted governance charter and metrics instrumentation plan to guide upcoming telemetry work
- [x] Authored Structurizr DSL architecture views and documented trust boundaries, attack surfaces, and SPOFs
- [x] Flagged dashboard auth, secrets management, CI artefact handling, and Docker distribution for follow-up interviews
- [x] Compiled multi-surface STRIDE/MITRE threat model with mitigation backlog in `docs/security/threat-model.md`
- [x] Captured compliance baseline matrices, evidence catalog, and verification plan under `docs/compliance/`
- [x] Documented SPACE-informed developer experience audit and platform backlog

## Deliverables

- [x] `docs/` reorganised into tutorials, how-to guides, reference, explanations, roadmap, contributing, and style content
- [x] `.github/ISSUE_TEMPLATE/` populated with bug, docs, and task templates plus Slack contact link
- [x] `.github/workflows/docs.yml` enforces strict Sphinx builds and link checking
- [x] README, implementation status, and release summary files now point to canonical roadmap documentation
- [x] Entity registry merges optional history files while preserving identifiers and status timelines
- [x] Pytest with coverage ≥ 80% (current: 86%)【41c28f†L1-L73】
- [x] Top-level package exports expose the enhanced pipeline configuration for downstream clients
- [x] Ruff lint clean (`uv run ruff check`)【316f32†L1-L2】
- [x] Ruff formatting clean (`uv run ruff format --check`)【6b058c†L1-L2】
- [x] Mypy type checks clean (`uv run mypy src tests scripts`)【756cc4†L1-L20】
- [x] Bandit security scan clean (`uv run bandit -r src scripts`)【d96b77†L1-L23】
- [x] Detect-secrets scan clean (`uv run detect-secrets scan src tests scripts`)【2a010b†L1-L58】
- [x] Package build succeeds (`uv run uv build`)【46d874†L1-L84】
- [x] Docs build strict mode passes (`uv run sphinx-build -n -W -b html docs docs/_build/html`)【f63725†L1-L25】
- [x] Docs link check passes with curated ignore list (`uv run sphinx-build -b linkcheck docs docs/_build/linkcheck`)【0ad91b†L1-L33】
- [x] Structurizr DSL workspace captures context, container, and component views (`docs/architecture/hotpass-architecture.dsl`)
- [x] Governance charter recorded in `docs/governance/project-charter.md`; metrics instrumentation captured in `docs/metrics/metrics-plan.md`
- [x] Baseline QA suite re-run prior to threat modelling (`uv run pytest --cov=src --cov=tests --cov-report=term-missing`)【150a53†L1-L74】
- [x] Lint/type/security/build checks re-run (`uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests scripts`; `uv run bandit -r src scripts`; `uv run detect-secrets scan src tests scripts`; `uv run uv build`)【6b0e7e†L1-L3】【0632b6†L1-L2】【3f68f9†L1-L24】【f75107†L1-L18】【f75013†L1-L67】【28ec86†L1-L119】
- [x] Security threat model documented with STRIDE/MITRE mapping (`docs/security/threat-model.md`)
- [x] Compliance baseline established with matrices and backlog (`docs/compliance/index.md`, `docs/compliance/remediation-backlog.md`)
- [x] Verification cadence and evidence catalog recorded (`docs/compliance/verification-plan.md`, `docs/compliance/evidence-catalog.md`)
- [x] Developer experience audit captured (`docs/metrics/devex-audit.md`)

## Quality Gates

- [x] Pytest with coverage ≥ 80% (latest run: 86%)【41c28f†L1-L73】
- [x] Ruff lint clean (`uv run ruff check`)【316f32†L1-L2】
- [x] Ruff formatting clean (`uv run ruff format --check`)【6b058c†L1-L2】
- [x] Mypy type checks clean (`uv run mypy src tests scripts`)【756cc4†L1-L20】
- [x] Bandit security scan clean (`uv run bandit -r src scripts`)【d96b77†L1-L23】
- [x] Detect-secrets scan clean (`uv run detect-secrets scan src tests scripts`)【2a010b†L1-L58】
- [x] Package build succeeds (`uv run uv build`)【46d874†L1-L84】
- [ ] Quarterly compliance verification cadence executed (first cycle due 2025-01-15)
- [ ] Compliance evidence catalog refreshed (due 2025-01-15)

## Links

- Tests: `uv run pytest --cov=src --cov=tests --cov-report=term-missing` (chunk `41c28f`)
- Lint: `uv run ruff check` (chunk `316f32`)
- Format: `uv run ruff format --check` (chunk `6b058c`)
- Types: `uv run mypy src tests scripts` (chunk `756cc4`)
- Security: `uv run bandit -r src scripts` (chunk `d96b77`)
- Secrets: `uv run detect-secrets scan src tests scripts` (chunk `2a010b`)
- Build: `uv run uv build` (chunk `46d874`)
- Docs build: `uv run sphinx-build -n -W -b html docs docs/_build/html` (chunk `f63725`)
- Docs linkcheck: `uv run sphinx-build -b linkcheck docs docs/_build/linkcheck` (chunk `0ad91b`)
- Compliance baseline: `docs/compliance/index.md`
- Compliance backlog: `docs/compliance/remediation-backlog.md`
- Verification cadence: `docs/compliance/verification-plan.md`
- Evidence catalog: `docs/compliance/evidence-catalog.md`
- DevEx audit: `docs/metrics/devex-audit.md`

## Risks / Notes

- Observability exporters now suppress shutdown ValueErrors; monitor CI logs after enabling full telemetry backends.
- Docker build validation remains unverified within current environment—ensure CI pipeline exercises Dockerfile and records results.
- Prefect telemetry exporters still raise SSL errors when orchestrating flows in offline environments; needs hardened configuration or opt-out for air-gapped runs.
- Docs link checking ignores selected external domains because of certificate issues in the sandbox; confirm connectivity in GitHub-hosted runners.
- Metrics instrumentation relies on access to Prefect Orion API, Slack webhooks, and optional Four Keys stack—validate connectivity and compliance approvals before rollout.
- Trust-boundary updates highlight new follow-ups (dashboard auth, secrets handling, CI artefact retention, Docker distribution); track owners above.
- Compliance matrices highlight outstanding DSAR automation, supplier assessments, and storage hardening—monitor backlog deadlines and update evidence catalog after each delivery.
- Pending decision on preferred secrets management platform may affect POPIA cross-border control implementation timeline.
