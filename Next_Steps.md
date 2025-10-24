# Next Steps

## Tasks

- [x] Establish reproducible data refinement pipeline architecture (Owner: Agent, Due: 2025-01-31)
- [ ] Implement comprehensive data quality validation suite (Owner: Agent, Due: 2025-01-31)
- [x] Harden CI-quality tooling coverage (Owner: Agent, Due: 2025-01-31)
- [x] Document SSOT CLI behaviour and validation pipeline (Owner: Agent, Due: 2025-01-31)
- [x] Add provenance-aware aggregation for conflicting source data (Owner: Agent, Due: 2025-01-31)
- [x] Add performance instrumentation, chunked ingestion toggles, and benchmark tooling (Owner: Agent, Due: 2025-01-31)
- [ ] Evaluate production data throughput regressions using benchmark harness (Owner: Ops, Due: 2025-02-15)

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
- [x] Replace standalone script with packaged CLI, structured logging, and optional report exports
- [x] Publish architecture overview, field dictionary, mapping, and expectation catalogue under `docs/`
- [x] Instrument pipeline stages with runtime metrics and expose results via CLI/report output
- [x] Provide benchmark script and API for capturing throughput guardrails

## Deliverables

- [x] `src/hotpass` package with modular pipeline implementation
- [x] `tests/` suite with synthetic fixtures verifying pipeline behaviour
- [ ] Refined workbook generated on demand via CLI (artifact only, not committed)
- [x] Tooling configuration files (`pyproject.toml`, expectation suites, etc.)
- [x] Documentation covering CLI usage, architecture, schema, and validation outputs
- [x] Workflow publishing of packaged refined workbook archive (artifact + branch)
- [x] Benchmarking script (`scripts/benchmark_pipeline.py`) and metrics reporting additions

## Quality Gates

- [x] Pytest with coverage ≥ 80%
- [x] Ruff lint + format clean
- [x] Mypy type checks scoped to project packages
- [x] Bandit security scan clean
- [x] Email/phone/website expectations require ≥85% regex match among non-null/non-blank values (configurable per run)
- [x] GitHub Actions `qa` job must pass before processing artifacts
- [x] Data validation schema + Great Expectations suite succeed with zero critical errors
- [x] Ensure refined workbook artifacts remain gitignored and reproducible
- [x] Performance metrics emitted for each run and benchmark harness available for regression checks

## Links

- Tests: `pytest` (see chunk `9b49c4`)
- Lint: `ruff check` (see chunk `6bdf1a`)
- Types: `mypy src tests scripts` (see chunk `20c7f7`)
- Security: `bandit -r src scripts` (see chunk `0347a7`)
- CLI run: `python scripts/process_data.py` (chunk `b62601`)
- Archive packaging tests: `pytest` (chunk `9b49c4`)
- Lint run: `ruff check` (chunk `6bdf1a`)
- Format check: `ruff format --check` (chunk `156308`)
- Type check: `mypy src tests scripts` (chunk `20c7f7`)
- Security scan: `bandit -r src scripts` (chunk `0347a7`)
- Workflow packaging update: `.github/workflows/process-data.yml`
- Latest regression: `pytest` (chunk `9b49c4`)
- Most recent pytest run: `pytest` (chunk `9b49c4`)
- Latest lint: `ruff check` (chunk `6bdf1a`)
- Latest format check: `ruff format --check` (chunk `156308`)
- Latest type check: `mypy src tests scripts` (chunk `20c7f7`)
- Latest security scan: `bandit -r src scripts` (chunk `0347a7`)
- Latest build: `python -m build` (chunk `d2e11d`)
- Architecture overview: `docs/architecture-overview.md`
- Field dictionary: `docs/ssot-field-dictionary.md`
- Source mapping: `docs/source-to-target-mapping.md`
- Expectation catalogue: `docs/expectation-catalogue.md`

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
- `hotpass` console script replaces `scripts/process_data.py`; ensure downstream automation (including workflows) depends on the new entry point going forward.
- Chunked Excel ingestion leverages iterative parsing; consider adding pyarrow if parquet staging becomes mandatory for production workloads.
- Benchmark harness available under `scripts/benchmark_pipeline.py`; schedule periodic baseline captures to detect performance regressions.
