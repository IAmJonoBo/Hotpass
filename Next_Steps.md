# Next Steps

## Tasks

- [x] Establish reproducible data refinement pipeline architecture (Owner: Agent, Due: 2025-01-31)
- [ ] Implement comprehensive data quality validation suite (Owner: Agent, Due: 2025-01-31)
- [x] Harden CI-quality tooling coverage (Owner: Agent, Due: 2025-01-31)
- [ ] Document SSOT CLI behaviour and validation pipeline (Owner: Agent, Due: 2025-01-31)
- [x] Add provenance-aware aggregation for conflicting source data (Owner: Agent, Due: 2025-01-31)

## Steps

- [x] Document repository context and outstanding assumptions
- [x] Design target SSOT schema and normalization rules
- [x] Create automated tests covering ingestion, normalization, and validation
- [x] Refactor processing script into modular pipeline with reporting
- [x] Update lint/type/security configurations and ensure green baseline
- [x] Expand expectation coverage to eliminate contact email format failure
- [x] Gate CI processing behind QA workflow checks (lint, format, tests, types, security)
- [x] Align fallback expectation thresholds with GE defaults and normalise blank contact values
- [ ] Monitor override needs for contact expectation thresholds using fresh vendor samples
- [x] Add checksum-stamped archive packaging and CI publication flow for refined workbook
- [x] Prioritise aggregation selections using source reliability, recency, and persist provenance trail

## Deliverables

- [x] `src/hotpass` package with modular pipeline implementation
- [x] `tests/` suite with synthetic fixtures verifying pipeline behaviour
- [ ] Refined workbook generated on demand via CLI (artifact only, not committed)
- [x] Tooling configuration files (`pyproject.toml`, expectation suites, etc.)
- [ ] Documentation describing CLI usage, schema, and validation outputs
- [x] Workflow publishing of packaged refined workbook archive (artifact + branch)

## Quality Gates

- [x] Pytest with coverage ≥ 80%
- [x] Ruff lint + format clean
- [x] Mypy type checks scoped to project packages
- [x] Bandit security scan clean
- [x] Email/phone/website expectations require ≥85% regex match among non-null/non-blank values (configurable per run)
- [x] GitHub Actions `qa` job must pass before processing artifacts
- [x] Data validation schema + Great Expectations suite succeed with zero critical errors
- [x] Ensure refined workbook artifacts remain gitignored and reproducible

## Links

- Tests: `pytest` (see chunk `f66374`)
- Lint: `ruff check` (see chunk `cf1849`)
- Types: `mypy src tests scripts` (see chunk `8af340`)
- Security: `bandit -r src scripts` (see chunk `8d39c5`)
- CLI run: `python scripts/process_data.py` (chunk `b62601`)
- Archive packaging tests: `pytest` (chunk `130a27`)
- Lint run: `ruff check` (chunk `ff31db`)
- Format check: `ruff format --check` (chunk `54cd19`)
- Type check: `mypy src tests scripts` (chunk `903177`)
- Security scan: `bandit -r src scripts` (chunk `97ff89`)
- Workflow packaging update: `.github/workflows/process-data.yml`
- Latest regression: `pytest` (chunk `6f3f4e`)
- Latest lint: `ruff check` (chunk `a7d22d`)
- Latest format check: `ruff format --check` (chunk `5a323f`)
- Latest type check: `mypy src tests scripts` (chunk `26510a`)
- Latest security scan: `bandit -r src scripts` (chunk `57bd11`)

## Risks / Notes

- Multi-email contacts now split across primary/secondary fields, resolving the previous `contact_primary_email` expectation failure.
- Great Expectations still runs via manual fallback because `PandasDataset` is unavailable; revisit once GE dataset API stabilises.
- Need to ensure POPIA compliance by redacting/limiting PII exposure in outputs and reports.
- Refined workbook now generated per-run; confirm CI artifact upload remains configured.
- QA workflow now blocks artifact generation if lint/test/type/security checks fail.
- Ruff `UP024` warning in `src/hotpass/pipeline.py` resolved by consolidating error handling under `OSError`.
- `scripts/process_data.py` reformatted with `ruff format` to match repository standards; monitor for future drift.
- Pending decision on final SSOT schema fields and deduplication rules.
- Pandera emits deprecation warning on top-level imports; plan migration to `pandera.pandas` namespace.
- Contact expectation defaults documented: blanks are treated as null-equivalent, and threshold tuning (default 0.85) must be justified when deviating for specific datasets.
- `DATA_ARTIFACT_PAT` secret must be provisioned for the `publish-artifact` job to succeed on pushes.
- Source reliability precedence currently assumes SACAA > Reachout > Contact Database; revisit mapping with data governance stakeholders.
