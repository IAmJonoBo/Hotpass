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

## Deliverables

- [x] `docs/` reorganised into tutorials, how-to guides, reference, explanations, roadmap, contributing, and style content
- [x] `.github/ISSUE_TEMPLATE/` populated with bug, docs, and task templates plus Slack contact link
- [x] `.github/workflows/docs.yml` enforces strict Sphinx builds and link checking
- [x] README, implementation status, and release summary files now point to canonical roadmap documentation
- [x] Entity registry merges optional history files while preserving identifiers and status timelines
- [x] Pytest with coverage ≥ 80% (current: 87%)【fd246f†L1-L73】
- [x] Top-level package exports expose the enhanced pipeline configuration for downstream clients
- [x] Ruff lint clean (`uv run ruff check`)【2938de†L1-L2】
- [x] Ruff formatting clean (`uv run ruff format --check`)【263f00†L1-L2】
- [x] Mypy type checks clean (`uv run mypy src tests scripts`)【accad6†L1-L22】
- [x] Bandit security scan clean (`uv run bandit -r src scripts`)【eba966†L1-L20】
- [x] Detect-secrets scan clean (`uv run detect-secrets scan src tests scripts`)【31297d†L1-L69】
- [x] Package build succeeds (`uv run uv build`)【89fcc8†L1-L92】
- [x] Docs build strict mode passes (`uv run sphinx-build -n -W -b html docs docs/_build/html`)【f63725†L1-L25】
- [x] Docs link check passes with curated ignore list (`uv run sphinx-build -b linkcheck docs docs/_build/linkcheck`)【0ad91b†L1-L33】
- [x] Structurizr DSL workspace captures context, container, and component views (`docs/architecture/hotpass-architecture.dsl`)
- [x] Governance charter recorded in `docs/governance/project-charter.md`; metrics instrumentation captured in `docs/metrics/metrics-plan.md`

## Links

- Tests: `uv run pytest --cov=src --cov=tests --cov-report=term-missing` (chunk `fd246f`)
- Lint: `uv run ruff check` (chunk `2938de`)
- Format: `uv run ruff format --check` (chunk `263f00`)
- Types: `uv run mypy src tests scripts` (chunk `accad6`)
- Security: `uv run bandit -r src scripts` (chunk `eba966`)
- Secrets: `uv run detect-secrets scan src tests scripts` (chunk `31297d`)
- Build: `uv run uv build` (chunk `89fcc8`)
- Docs build: `uv run sphinx-build -n -W -b html docs docs/_build/html` (chunk `f63725`)
- Docs linkcheck: `uv run sphinx-build -b linkcheck docs docs/_build/linkcheck` (chunk `0ad91b`)

## Risks / Notes

- Observability exporters now suppress shutdown ValueErrors; monitor CI logs after enabling full telemetry backends.
- Docker build validation remains unverified within current environment—ensure CI pipeline exercises Dockerfile and records results.
- Prefect telemetry exporters still raise SSL errors when orchestrating flows in offline environments; needs hardened configuration or opt-out for air-gapped runs.
- Docs link checking ignores selected external domains because of certificate issues in the sandbox; confirm connectivity in GitHub-hosted runners.
- Metrics instrumentation relies on access to Prefect Orion API, Slack webhooks, and optional Four Keys stack—validate connectivity and compliance approvals before rollout.
- Trust-boundary updates highlight new follow-ups (dashboard auth, secrets handling, CI artefact retention, Docker distribution); track owners above.
