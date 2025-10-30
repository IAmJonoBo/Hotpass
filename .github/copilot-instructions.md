# Hotpass Guidance for AI Agents

## Project Purpose

Hotpass is a data refinement platform that transforms messy spreadsheets into a governed single source of truth. It normalizes columns, resolves duplicates, enriches data, and publishes quality signals with industry-ready profiles, POPIA compliance, and production-grade orchestration.

## Orientation

- Python 3.13 project managed with uv; run `uv sync --extra dev --extra docs` once and prefer `uv run ...` for every command.
- Primary CLI lives in `src/hotpass/cli.py` (exposed as `uv run hotpass`); enhanced features hang off `cli_enhanced.py` and `pipeline_enhanced.py`.
- Core package code sits under `src/hotpass/`; automation scripts are in `scripts/`; documentation (MyST + Sphinx) is under `docs/`.
- Test data fixtures in `tests/conftest.py` write sample Excel workbooks into a temp `data/` directory—mirror that structure when adding new sources.

## Architecture Map

- `hotpass.pipeline` orchestrates the end-to-end refinement: Excel ingest via `data_sources`, normalisation + slug generation, provenance tracking, quality scoring, progress events, and Excel output through `formatting` + `artifacts`.
- `data_sources` adapters (`load_reachout_database`, `load_contact_database`, `load_sacaa_cleaned`) use `ExcelReadOptions` for chunked reads and optional parquet staging; keep column semantics and chunking guards intact.
- Supporting modules (`normalization`, `entity_resolution`, `pipeline_reporting`, `quality`) provide deterministic helpers. Preserve `SSOT_COLUMNS`, slug rules, and `QualityReport` serialization because downstream consumers and tests rely on them.
- Enhanced workloads flow through `pipeline_enhancements`: gated by `EnhancedPipelineConfig` to enable entity resolution, geospatial normalisation, web enrichment, and POPIA compliance. Every branch must degrade gracefully when optional deps (Splink, requests, trafilatura, Presidio) are missing—log and return the original frame.
- Observability lives in `observability.py`; `pipeline_enhanced` wires counters/spans via `get_pipeline_metrics` and `trace_operation`. Tests assert that fallbacks still work when OpenTelemetry is absent.
- Prefect orchestration in `orchestration.py` wraps the pipeline with optional decorators. Maintain the `PipelineRunOptions` contract and `_execute_pipeline` summary shape because CLI + deployments consume it.

## Workflow & QA

- Typical refinement run: `uv run hotpass --input-dir ./data --output-path ./dist/refined.xlsx --archive`. CLI options resolve through `_resolve_options` and are mirrored in `contracts/hotpass-cli-contract.yaml`.
- When adding pipeline features, update the matching pytest suites: `tests/test_pipeline*.py`, `tests/test_cli*.py`, `tests/test_pipeline_enhanced.py`, plus extras-specific suites (`test_compliance*.py`, `test_geospatial.py`, `test_enrichment.py`).
- Local QA mirrors `.github/workflows/process-data.yml`: run `uv run pytest`, `uv run ruff check`, `uv run mypy src scripts`, and `uv run python scripts/quality/fitness_functions.py` (guards LOC and observability imports). Add `uv run bandit -r src scripts` and `uv run detect-secrets scan src tests scripts` when touching security-sensitive paths.
- Pytest files must avoid bare `assert`; reuse the shared `expect(..., message)` helper (see `docs/how-to-guides/assert-free-pytest.md`) so Bandit rule **B101** stays green without waivers.
- Documentation is generated with `uv run sphinx-build docs docs/_build`; keep `docs/architecture/fitness-functions.md` and relevant how-to guides in sync with behavioural or threshold changes.

## Conventions & Invariants

- Respect the `SSOT_COLUMNS` order, provenance JSON schema, and `QualityReport.to_dict()` keys—tests load these structures directly.
- Thread new configuration flags through `PipelineConfig`, CLI parsing, orchestration, and tests. Keep defaults aligned with `config.get_default_profile` and industry profiles under `src/hotpass/profiles/`.
- `ExcelReadOptions` must reject non-positive chunk sizes and preserve staging semantics; avoid introducing side effects in helper functions used by chunked reads.
- Progress instrumentation relies on the `PIPELINE_EVENT_*` constants; CLI progress UI (`PipelineProgress`) expects those exact event names.
- Optional dependency fallbacks (Great Expectations, Prefect, Presidio, OpenTelemetry) are deliberate. Preserve import guards and ensure new code paths handle their absence without raising.
- Compliance flows (`POPIAPolicy`, `add_provenance_columns`, consent overrides) power POPIA reporting. Changing column names or statuses requires coordinated updates to tests and policy docs.
- `scripts/process_data.py` remains a thin shim around the CLI; keep it aligned with package entrypoints for legacy automation.

## Key References

- Pipeline core: `src/hotpass/pipeline.py`, `pipeline_enhanced.py`, `pipeline_enhancements.py`, `pipeline_reporting.py`.
- Data ingestion & cleaning: `data_sources.py`, `normalization.py`, `entity_resolution.py`, `geospatial.py`, `enrichment.py`.
- Compliance & quality: `compliance.py`, `quality.py`, `artifacts.py`.
- Interfaces & orchestration: `cli.py`, `cli_enhanced.py`, `orchestration.py`, `observability.py`.
- Tests to mirror: `tests/test_pipeline.py`, `tests/test_cli.py`, `tests/test_pipeline_enhanced.py`, `tests/test_compliance.py`, `tests/test_geospatial.py`, `tests/test_enrichment.py`.

## Acceptance Criteria for Changes

When submitting changes, ensure:

1. **Tests pass**: All relevant test suites run successfully (`uv run pytest`)
2. **Linting clean**: No ruff, mypy, or bandit violations in changed code
3. **Documentation updated**: Sync docs if changing public APIs or behavior
4. **Backwards compatible**: Existing pipelines, configs, and outputs remain valid unless explicitly breaking
5. **Security checked**: No secrets committed; run `uv run detect-secrets scan` on new files
6. **Observability preserved**: Metrics, logs, and traces maintain their contract for monitoring tools
7. **No bare assertions**: Use `expect(..., message)` helper in pytest files per `docs/how-to-guides/assert-free-pytest.md`

## Common Pitfalls

- **Chunk size changes**: Modifying `ExcelReadOptions.chunk_size` semantics breaks memory profiling and staging logic. Keep validation and behavior intact.
- **SSOT column reordering**: Downstream tools expect the exact order in `SSOT_COLUMNS`. Add new columns at the end or coordinate schema migration.
- **Missing optional deps**: Code must gracefully fall back when Great Expectations, Prefect, Presidio, or OpenTelemetry are unavailable. Always guard imports and preserve core functionality.
- **Breaking provenance schema**: JSON structure in `add_provenance_columns` is consumed by compliance audits. Additions are safe; changes to existing keys require migration.
- **Pipeline event names**: CLI progress UI depends on exact `PIPELINE_EVENT_*` constants. Renaming breaks visual feedback; add new events instead.
- **Industry profile defaults**: Changes to `config.get_default_profile` or profiles under `src/hotpass/profiles/` affect production pipelines. Document and test cross-profile behavior.

## Dependencies Overview

| Extra          | Key Packages                    | Purpose                                              |
| -------------- | ------------------------------- | ---------------------------------------------------- |
| `dev`          | pytest, ruff, mypy, pre-commit  | Testing, linting, type checking, commit hooks        |
| `docs`         | sphinx, myst-parser             | Documentation generation                             |
| `orchestration`| prefect>=3.0                    | Workflow scheduling and monitoring                   |
| `enrichment`   | requests, trafilatura           | Web scraping and data enrichment                     |
| `geospatial`   | geopandas, geopy                | Geocoding and spatial operations                     |
| `compliance`   | presidio-analyzer, presidio-anonymizer | PII detection and POPIA compliance           |
| `dashboards`   | streamlit                       | Interactive data exploration UI                      |

Install combinations as needed: `uv sync --extra dev --extra orchestration --extra geospatial` or use `make sync EXTRAS="dev orchestration geospatial"` for convenience.
