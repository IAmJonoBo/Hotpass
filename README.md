# Hotpass Data Refinement Repository

This repository is optimized for validating, normalizing, processing, and refining multiple Excel documents into a highly-refined single source of truth. It uses Python with libraries like pandas, pandera, and great-expectations for data quality assurance.

## Project Structure

- `data/`: Contains input Excel files. Run the pipeline to regenerate the refined workbook (ignored in git).
- `scripts/`: Python scripts for data processing.
- `docs/`: Additional documentation (see below).
- `.github/workflows/`: GitHub Actions for automated processing.

## Setup

1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Place your Excel files in the `data/` directory.
4. Run the packaged CLI to regenerate the refined workbook: `hotpass`. Pass `--archive` to also produce a timestamped, checksum-stamped zip under `dist/` for distribution.

## CLI Usage

The CLI is distributed as a console script (`hotpass`) that exposes the full pipeline with structured logging:

```bash
# Run the pipeline with rich terminal output
hotpass --archive

# Emit JSON logs for automation and write the quality report to Markdown
hotpass \
  --log-format json \
  --report-path dist/quality-report.md \
  --report-format markdown

# Load defaults from a TOML configuration file and override the output path
hotpass --config config/pipeline.toml --output-path /tmp/refined.xlsx
```

Supported configuration files are JSON or TOML. CLI flags always take precedence over configuration values. When `--report-path` is provided the tool renders the `QualityReport` to Markdown by default, or HTML when `--report-format html` (or a `.html`/`.htm` extension) is used.

Structured logs can be emitted in JSON (`--log-format json`) for ingestion by automation tooling, or as rich tables (`--log-format rich`, the default) for human-friendly summaries. Each CLI run now reports detailed performance metrics – including per-stage durations and throughput – in both the console summary and generated quality reports so ops teams can track runtime trends.

### Performance tuning flags

Large Excel inputs can be streamed and optionally staged to parquet for reuse:

- `--excel-chunk-size <rows>` – enable chunked reads for all source workbooks.
- `--excel-engine <name>` – override the pandas engine (e.g. `pyxlsb` for `.xlsb` inputs).
- `--excel-stage-dir <path>` – persist chunked reads to parquet so subsequent runs can reuse staged data.

## GitHub Actions

The repository uses ephemeral runners via GitHub Actions to automatically process data on pushes to the main branch. A `qa` job provisions Python 3.13 with cached dependencies and enforces quality controls before any data processing runs:

- `pip install -r requirements.txt`
- `ruff check`
- `ruff format --check`
- `pytest`
- `mypy src tests scripts`
- `bandit -r src scripts`

Only after these checks succeed does the `process-data` job execute the refinement script, upload the refined workbook, and package the matching archive as artifacts.

## Retrieving Packaged Artifacts

- **Local runs**: `hotpass --archive` writes the refined workbook to `data/refined_data.xlsx` and a zip archive named `refined-data-<timestamp>-<checksum>.zip` to `dist/`. The archive contains the workbook and a `SHA256SUMS` manifest so the checksum in the filename can be verified.
- **GitHub Actions artifacts**: Successful workflow runs publish two artifacts—`refined-data` (the Excel workbook) and `refined-data-archive` (the packaged zip). Download them directly from the workflow summary page.
- **Data artifacts branch**: On pushes to `main`, the `publish-artifact` job downloads the packaged zip and force-pushes it to the `data-artifacts` branch using the `DATA_ARTIFACT_PAT` secret. Consumers can fetch the branch to retrieve the latest archive without navigating workflow logs.

## Data Quality Expectations

Hotpass uses Great Expectations when available, with a manual fallback that mirrors its behaviour. Email, phone, and website columns must match their respective regex patterns for at least 85% of non-null, non-blank rows by default (configurable via `run_expectations`). Blank strings are normalised to null-equivalent values prior to validation so that optional fields do not count against match rates. Override the default `mostly` thresholds only when a specific dataset justifies a different tolerance, and record the rationale in project documentation.

## Copilot Instructions

When using GitHub Copilot for this project:

- **Validation**: Use pandera schemas to define data expectations. Example: "Create a schema for validating flight school data with columns for name, location, and contact."

- **Normalization**: Focus on cleaning data: "Normalize phone numbers and addresses in the dataframe."

- **Merging**: "Merge multiple dataframes on common keys, handling duplicates."

- **Quality Assurance**: "Add great-expectations tests for data integrity."

- **Optimization**: "Optimize the script for large datasets using chunked reading."

Ensure all code follows best practices for data processing and includes error handling.

## Documentation

Centralised documentation lives under `docs/`:

- [Architecture Overview](docs/architecture-overview.md) – Pipeline flow, operational cadence, and privacy guardrails.
- [SSOT Field Dictionary](docs/ssot-field-dictionary.md) – Canonical schema definitions and stewardship practices.
- [Source-to-Target Mapping](docs/source-to-target-mapping.md) – Column-level lineage across core data providers.
- [Expectation Catalogue](docs/expectation-catalogue.md) – Active data quality rules, thresholds, and operational notes.

## Contributing

1. Make changes in a branch.
2. Test locally.
3. Create a PR; GitHub Actions will run the processing pipeline.
## Benchmarking and performance monitoring

Use the lightweight benchmarking helper to capture baseline throughput and guard against regressions:

```bash
python scripts/benchmark_pipeline.py \
  --input-dir data \
  --output-path dist/benchmark.xlsx \
  --runs 5 \
  --excel-chunk-size 5000 \
  --json
```

The command runs the pipeline multiple times, aggregates average stage timings (load, aggregation, expectations, write), and emits both JSON summaries and human-readable output. The data is also available programmatically via `hotpass.benchmarks.run_benchmark` for integration into CI checks or monitoring dashboards.

