# Next Steps

## Tasks

- [x] Consolidate planning collateral into `docs/roadmap.md` and simplify top-level release docs (Owner: Product, Due: 2025-10-25)
- [x] Publish Diátaxis-aligned docs set with style and contributing guidance (Owner: Docs, Due: 2025-10-25)
- [ ] Validate Docker image build and publish pipeline in CI (Owner: DevOps, Due: 2025-11-08)
- [x] Quieten Prefect/OpenTelemetry console handlers to prevent ValueError on process shutdown during QA tooling (Owner: Engineering, Due: 2025-11-08)
- [ ] Re-enable skipped integration suites once optional dependencies can be installed in CI without instability (Owner: Engineering, Due: 2025-11-15)
- [x] Merge entity registry history during deduplication to unlock roadmap follow-up (Owner: Engineering, Due: 2025-11-01)
- [x] Add regression coverage for dashboard persistence helpers (Owner: Engineering, Due: 2025-11-01)

## Steps

- [x] Migrated documentation to Diátaxis structure and removed duplicate legacy pages
- [x] Added docs CI workflow executing strict Sphinx builds and link checking
- [x] Refreshed README to act as a lightweight entry point into docs
- [x] Create dedicated fixtures for observability and orchestration to reduce reliance on global state between tests
- [ ] Capture outcomes from docs workflow once it runs on `main`
- [x] Restore lint/type gates after refactoring observability and orchestration modules
- [x] Implement entity registry history merge flow and regression coverage

## Deliverables

- [x] `docs/` reorganised into tutorials, how-to guides, reference, explanations, roadmap, contributing, and style content
- [x] `.github/ISSUE_TEMPLATE/` populated with bug, docs, and task templates plus Slack contact link
- [x] `.github/workflows/docs.yml` enforces strict Sphinx builds and link checking
- [x] README, implementation status, and release summary files now point to canonical roadmap documentation
- [x] Entity registry merges optional history files while preserving identifiers and status timelines
- [x] Pytest with coverage ≥ 80% (current: 86%)【3a3259†L1-L66】
- [x] Ruff lint clean (`uv run ruff check`)【0e4123†L1-L2】
- [x] Ruff formatting clean (`uv run ruff format --check`)【830fa6†L1-L1】
- [x] Mypy type checks clean (`uv run mypy src tests scripts`)【c2d9a7†L1-L22】
- [x] Bandit security scan clean (`uv run bandit -r src scripts`)【c15d63†L1-L19】
- [x] Detect-secrets scan clean (`uv run detect-secrets scan src tests scripts`)【67e65d†L1-L63】
- [x] Package build succeeds (`uv run uv build`)【1340b0†L1-L115】
- [x] Docs build strict mode passes (`uv run sphinx-build -n -W -b html docs docs/_build/html`)【f63725†L1-L25】
- [x] Docs link check passes with curated ignore list (`uv run sphinx-build -b linkcheck docs docs/_build/linkcheck`)【0ad91b†L1-L33】

## Links

- Tests: `uv run pytest --cov=src --cov=tests --cov-report=term-missing` (chunk `3a3259`)
- Lint: `uv run ruff check` (chunk `0e4123`)
- Format: `uv run ruff format --check` (chunk `830fa6`)
- Types: `uv run mypy src tests scripts` (chunk `c2d9a7`)
- Security: `uv run bandit -r src scripts` (chunk `c15d63`)
- Secrets: `uv run detect-secrets scan src tests scripts` (chunk `67e65d`)
- Build: `uv run uv build` (chunk `1340b0`)
- Docs build: `uv run sphinx-build -n -W -b html docs docs/_build/html` (chunk `f63725`)
- Docs linkcheck: `uv run sphinx-build -b linkcheck docs docs/_build/linkcheck` (chunk `0ad91b`)

## Risks / Notes

- Observability exporters now suppress shutdown ValueErrors; monitor CI logs after enabling full telemetry backends.
- Docker build validation remains unverified within current environment—ensure CI pipeline exercises Dockerfile and records results.
- Prefect telemetry exporters still raise SSL errors when orchestrating flows in offline environments; needs hardened configuration or opt-out for air-gapped runs.
- Docs link checking ignores selected external domains because of certificate issues in the sandbox; confirm connectivity in GitHub-hosted runners.
