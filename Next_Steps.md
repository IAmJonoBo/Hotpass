# Next Steps

## Tasks

- [x] Consolidate planning collateral into `docs/roadmap.md` and simplify top-level release docs (Owner: Product, Due: 2025-10-25)
- [x] Publish Diátaxis-aligned docs set with style and contributing guidance (Owner: Docs, Due: 2025-10-25)
- [ ] Validate Docker image build and publish pipeline in CI (Owner: DevOps, Due: 2025-11-08)
- [ ] Quieten Prefect/OpenTelemetry console handlers to prevent ValueError on process shutdown during QA tooling (Owner: Engineering, Due: 2025-11-08)
- [ ] Re-enable skipped integration suites once optional dependencies can be installed in CI without instability (Owner: Engineering, Due: 2025-11-15)

## Steps

- [x] Migrated documentation to Diátaxis structure and removed duplicate legacy pages
- [x] Added docs CI workflow executing strict Sphinx builds and link checking
- [x] Refreshed README to act as a lightweight entry point into docs
- [x] Create dedicated fixtures for observability and orchestration to reduce reliance on global state between tests
- [ ] Capture outcomes from docs workflow once it runs on `main`

## Deliverables

- [x] `docs/` reorganised into tutorials, how-to guides, reference, explanations, roadmap, contributing, and style content
- [x] `.github/ISSUE_TEMPLATE/` populated with bug, docs, and task templates plus Slack contact link
- [x] `.github/workflows/docs.yml` enforces strict Sphinx builds and link checking
- [x] README, implementation status, and release summary files now point to canonical roadmap documentation
- [ ] Pytest with coverage ≥ 80% (current: 78% with optional suites mocked for coverage)【7fa6db†L1-L34】
- [x] Ruff lint clean (`uv run ruff check`)【5de868†L1-L2】
- [x] Mypy type checks clean (`uv run mypy src tests scripts`)【5dc602†L1-L3】
- [x] Bandit security scan clean (`uv run bandit -r src scripts`)【58a47f†L1-L23】
- [x] Detect-secrets scan clean (`uv run detect-secrets scan src tests scripts`)【cf9c79†L1-L49】
- [x] Package build succeeds (`uv build`)【fd9482†L1-L115】
- [x] Docs build strict mode passes (`uv run sphinx-build -n -W -b html docs docs/_build/html`)【f63725†L1-L25】
- [x] Docs link check passes with curated ignore list (`uv run sphinx-build -b linkcheck docs docs/_build/linkcheck`)【0ad91b†L1-L33】

## Links

- Tests: `uv run pytest --cov=src --cov=tests --cov-report=term-missing` (chunk `32108d`)
- Lint: `uv run ruff check` (chunk `5de868`)
- Types: `uv run mypy src tests scripts` (chunk `5dc602`)
- Security: `uv run bandit -r src scripts` (chunk `58a47f`)
- Secrets: `uv run detect-secrets scan src tests scripts` (chunk `cf9c79`)
- Build: `uv build` (chunk `fd9482`)
- Docs build: `uv run sphinx-build -n -W -b html docs docs/_build/html` (chunk `f63725`)
- Docs linkcheck: `uv run sphinx-build -b linkcheck docs docs/_build/linkcheck` (chunk `0ad91b`)

## Risks / Notes

- Observability console exporter raises `ValueError: I/O operation on closed file` after QA commands due to Prefect handlers flushing to a closed stream; ensure graceful shutdown before enabling in CI.
- Docker build validation remains unverified within current environment—ensure CI pipeline exercises Dockerfile and records results.
- Prefect telemetry exporters still raise SSL errors when orchestrating flows in offline environments; needs hardened configuration or opt-out for air-gapped runs.
- Docs link checking ignores selected external domains because of certificate issues in the sandbox; confirm connectivity in GitHub-hosted runners.
