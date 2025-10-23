# Next Steps

## Tasks

- [x] Establish reproducible data refinement pipeline architecture (Owner: Agent, Due: 2025-01-31)
- [ ] Implement comprehensive data quality validation suite (Owner: Agent, Due: 2025-01-31)
- [x] Harden CI-quality tooling coverage (Owner: Agent, Due: 2025-01-31)
- [ ] Document SSOT CLI behaviour and validation pipeline (Owner: Agent, Due: 2025-01-31)

## Steps

- [x] Document repository context and outstanding assumptions
- [x] Design target SSOT schema and normalization rules
- [x] Create automated tests covering ingestion, normalization, and validation
- [x] Refactor processing script into modular pipeline with reporting
- [x] Update lint/type/security configurations and ensure green baseline
- [ ] Expand expectation coverage to eliminate contact email format failure

## Deliverables

- [x] `src/hotpass` package with modular pipeline implementation
- [x] `tests/` suite with synthetic fixtures verifying pipeline behaviour
- [ ] Refined workbook generated on demand via CLI (artifact only, not committed)
- [x] Tooling configuration files (`pyproject.toml`, expectation suites, etc.)
- [ ] Documentation describing CLI usage, schema, and validation outputs

## Quality Gates

- [x] Pytest with coverage ≥ 80%
- [x] Ruff lint + format clean
- [x] Mypy type checks scoped to project packages
- [x] Bandit security scan clean
- [ ] Data validation schema + Great Expectations suite succeed with zero critical errors
- [ ] Ensure refined workbook artifacts remain gitignored and reproducible

## Links

- Tests: `pytest` (see chunk `ca47d4`)
- Lint: `ruff check` (see chunk `871f88`)
- Types: `mypy src scripts` (see chunk `ea84d8`)
- Security: `python -m bandit -r src scripts` (see chunk `79fc15`)
- CLI run: `python scripts/process_data.py` (chunk `4dc178`)

## Risks / Notes

- Great Expectations suite currently fails `contact_primary_email format`; investigate expectation definitions or normalization rules.
- Need to ensure POPIA compliance by redacting/limiting PII exposure in outputs and reports.
- Refined workbook now generated per-run; confirm CI artifact upload remains configured.
- Pending decision on final SSOT schema fields and deduplication rules.
- Pandera emits deprecation warning on top-level imports; plan migration to `pandera.pandas` namespace.
