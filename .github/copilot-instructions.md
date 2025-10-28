# Hotpass Guidance for AI Agents

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
