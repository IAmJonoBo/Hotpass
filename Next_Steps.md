# Next Steps

## Tasks
- [ ] Restore ≥85% coverage by expanding integration tests for enhanced CLI, observability, enrichment, and geospatial flows (Owner: Engineering, Due: 2025-11-07)
- [x] Refactor `hotpass-enhanced dashboard` subprocess launch to satisfy Bandit B603/B607 (Owner: Engineering, Due: 2025-11-06)
- [ ] Validate Docker image build and publish pipeline in CI (Owner: DevOps, Due: 2025-11-08)
- [x] Harden Splink fallback path to operate when slug data is missing (Owner: Engineering, Due: 2025-11-07)
- [x] Update public docs (README, Implementation Status) to reflect current coverage (67%) and outstanding risk items (Owner: Product, Due: 2025-11-06)

## Steps
- [x] Added mandatory runtime dependencies (Prefect, OpenTelemetry, Requests, Trafilatura, Detect-Secrets, types-PyYAML) to unblock imports across orchestration/enrichment paths
- [x] Guarded compliance/enrichment/geospatial tests with `pytest.importorskip` to make optional integrations explicit
- [x] Patched Presidio fallback to expose stub attributes for mocking when the library is absent
- [ ] Re-enable skipped integration suites once optional dependencies can be installed in CI without instability
- [ ] Create dedicated fixtures for observability and orchestration to reduce reliance on global state between tests

## Deliverables
- [x] Updated `pyproject.toml` and `uv.lock` reflecting required runtime dependencies for observability/orchestration/enrichment
- [x] Adjusted tests under `tests/test_observability.py`, `tests/test_orchestration.py`, `tests/test_pipeline_enhanced.py`, `tests/test_enrichment.py`, and `tests/test_geospatial.py` to skip gracefully when integrations are missing
- [x] Enhanced `src/hotpass/compliance.py` to expose stubbed Presidio APIs when unavailable, keeping tests patchable
- [x] Add regression tests for Splink fallback covering slug synthesis and empty-column scenarios
- [x] Document required extras per CLI command in README/Implementation_Status

## Quality Gates
- [ ] Pytest with coverage ≥ 80% (current: 67% – optional integration suites skipped)【8f7334†L1-L46】
- [x] Ruff lint clean (`uv run ruff check`)【9c91b8†L1-L2】
- [x] Mypy type checks clean (`uv run mypy src tests scripts`)【6e8155†L1-L3】
- [x] Bandit security scan clean (`uv run bandit -r src scripts`)【38ecea†L1-L20】
- [x] Detect-secrets scan clean (`uv run detect-secrets scan src tests scripts`)【8802b3†L1-L62】
- [ ] Docker image build validated (pending CI execution)
- [x] Documentation alignment (README/Implementation_Status updated)【F:README.md†L4-L11】【F:IMPLEMENTATION_STATUS.md†L160-L178】

## Links
- Tests: `uv run pytest --cov=src --cov=tests --cov-report=term-missing` (chunk `8f7334`)
- Lint: `uv run ruff check` (chunk `9c91b8`)
- Types: `uv run mypy src tests scripts` (chunk `6e8155`)
- Security: `uv run bandit -r src scripts` (chunk `38ecea`)
- Secrets: `uv run detect-secrets scan src tests scripts` (chunk `8802b3`)
- Build: `uv build` (chunk `db1520`)

## Risks / Notes
- Coverage regression to 67% driven by skipped integration suites; enabling dependencies or providing hermetic fakes is required to recover gates.
- Docker build validation remains unverified within current environment—ensure CI pipeline exercises Dockerfile and records results.
- Prefect telemetry exporters previously raised SSL errors; verify after dependency alignment.
- Updated dependency surface increases install footprint—monitor for longer build times in CI and adjust caching strategies accordingly.
