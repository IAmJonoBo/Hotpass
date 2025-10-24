# Hotpass Data Refinement Repository

[![Release Status](https://img.shields.io/badge/status-release--ready-brightgreen)](https://github.com/IAmJonoBo/Hotpass)
[![Test Coverage](https://img.shields.io/badge/coverage-87%25-brightgreen)](https://github.com/IAmJonoBo/Hotpass)
[![Python Version](https://img.shields.io/badge/python-3.13-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Proprietary-red)](LICENSE)

This repository is optimized for validating, normalizing, processing, and refining multiple Excel documents into a highly-refined single source of truth. It uses Python with libraries like pandas, pandera, and great-expectations for data quality assurance.

**🎉 RELEASE READY**: Hotpass has reached release state with 87% test coverage (152 tests), comprehensive QA gates, orchestration with Prefect, entity resolution with Splink, and real-time monitoring dashboard. See [Implementation Status](IMPLEMENTATION_STATUS.md) for detailed roadmap progress.

**NEW FEATURES**:
- ✨ **Orchestration**: Prefect-based workflow orchestration with retry logic and scheduling
- ✨ **Observability**: OpenTelemetry metrics and monitoring
- ✨ **Entity Resolution**: Probabilistic duplicate detection with Splink
- ✨ **Dashboard**: Real-time Streamlit monitoring dashboard
- ✨ **Enhanced CLI**: New commands for orchestration, entity resolution, and dashboard

## Key Features

- 🎯 **Industry-Agnostic**: Configurable profiles for aviation, healthcare, or any business domain
- 🧠 **Intelligent Column Mapping**: Automatic fuzzy matching and synonym detection
- 🔍 **Data Profiling**: Comprehensive statistics and quality insights
- 👥 **Multi-Contact Support**: Advanced contact management per organization
- ⚠️ **Enhanced Error Handling**: Structured error reporting with recovery suggestions
- 🎨 **Rich Formatting**: Professional Excel output with conditional formatting
- 📊 **Multiple Output Formats**: Export to Excel, CSV, Parquet, or JSON
- ✅ **Configurable Validation**: Industry-specific thresholds and rules
- 📝 **Comprehensive Logging**: Full audit trail of pipeline execution
- 💡 **Quality Recommendations**: Actionable insights for data improvement
- 🔧 **Configuration Doctor**: Auto-diagnose and fix configuration issues
- 🔀 **Conflict Resolution**: Transparent tracking of data source conflicts

## Project Structure

- `data/`: Contains input Excel files. Run the pipeline to regenerate the refined workbook (ignored in git).
- `scripts/`: Python scripts for data processing.
- `docs/`: Additional documentation including:
  - [Implementation Guide](docs/implementation-guide.md) - How to use new features
  - [Gap Analysis](docs/gap-analysis.md) - Comprehensive enhancement roadmap
  - [Architecture Overview](docs/architecture-overview.md) - System design
  - [SSOT Field Dictionary](docs/ssot-field-dictionary.md) - Schema definitions
  - [Source Mapping](docs/source-to-target-mapping.md) - Column lineage
  - [Expectation Catalogue](docs/expectation-catalogue.md) - Validation rules
- `.github/workflows/`: GitHub Actions for automated processing.

## Installation

### Prerequisites
- Python 3.13
- [uv](https://github.com/astral-sh/uv) package manager

### Basic Installation
```bash
# Install uv (one-time)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repository
git clone https://github.com/IAmJonoBo/Hotpass.git
cd Hotpass

# Create virtual environment and install dependencies
uv venv
uv sync --extra dev --extra docs

# Install pre-commit hooks
uv run pre-commit install
```

### Feature-Specific Installation

**With Orchestration & Monitoring:**
```bash
uv sync --extra dev --extra docs --extra orchestration --extra dashboards
```

**With Entity Resolution:**
```bash
uv sync --extra dev --extra docs --extra entity_resolution
```

**Full Installation (All Features):**
```bash
uv sync --extra dev --extra docs --extra orchestration --extra entity_resolution --extra ml_scoring --extra enrichment --extra geospatial --extra compliance --extra dashboards --extra caching
```

## Quick Start

### Standard Pipeline Run
```bash
# Basic usage
hotpass

# With options
hotpass --input-dir ./data --output-path ./output/refined.xlsx --archive
```

### Orchestrated Run (NEW)
```bash
# Run with Prefect orchestration
hotpass-enhanced orchestrate --profile aviation --archive

# Deploy to Prefect for scheduled runs
hotpass-enhanced deploy --name hotpass-prod --schedule "0 2 * * *"
```

### Entity Resolution (NEW)
```bash
# Deduplicate data with probabilistic matching
hotpass-enhanced resolve \
  --input-file data/duplicates.xlsx \
  --output-file data/clean.xlsx \
  --threshold 0.8 \
  --use-splink
```

### Monitoring Dashboard (NEW)
```bash
# Launch real-time monitoring dashboard
hotpass-enhanced dashboard --port 8501
```

## CLI Usage

The CLI is distributed as a console script (`hotpass`) that exposes the full pipeline with structured logging:

```bash
# Run the pipeline with rich terminal output and enhanced features
hotpass --archive

# Emit JSON logs for automation and write the quality report to Markdown
hotpass \
  --log-format json \
  --report-path dist/quality-report.md \
  --report-format markdown

# Load defaults from a TOML configuration file and override the output path
hotpass --config config/pipeline.toml --output-path /tmp/refined.xlsx
```

### New Enhancement Features

The pipeline now includes powerful enhancement features:

- **Enhanced Formatting**: Professional Excel output with conditional formatting, auto-sized columns, and summary sheets
- **Configurable Validation**: Industry-specific validation thresholds based on your profile
- **Audit Trail**: Complete logging of all pipeline operations
- **Quality Recommendations**: Actionable suggestions for improving data quality
- **Conflict Resolution**: Transparent tracking of how data conflicts are resolved

See [Enhancement Guide](docs/enhancement-guide.md) for detailed usage examples.

Supported configuration files are JSON or TOML. CLI flags always take precedence over configuration values. When `--report-path` is provided the tool renders the `QualityReport` to Markdown by default, or HTML when `--report-format html` (or a `.html`/`.htm` extension) is used.

Structured logs can be emitted in JSON (`--log-format json`) for ingestion by automation tooling, or as rich tables (`--log-format rich`, the default) for human-friendly summaries. Each CLI run now reports detailed performance metrics – including per-stage durations and throughput – in both the console summary and generated quality reports so ops teams can track runtime trends.

### Performance tuning flags

Large Excel inputs can be streamed and optionally staged to parquet for reuse:

- `--excel-chunk-size <rows>` – enable chunked reads for all source workbooks.
- `--excel-engine <name>` – override the pandas engine (e.g. `pyxlsb` for `.xlsb` inputs).
- `--excel-stage-dir <path>` – persist chunked reads to parquet so subsequent runs can reuse staged data.

## GitHub Actions

The repository uses ephemeral runners via GitHub Actions to automatically lint, test, and package data on pushes and pull requests. The workflow now relies on `astral-sh/setup-uv` to provision Python 3.13 and the `uv` resolver for reproducible installs:

- `uv sync --extra dev --frozen` ensures QA jobs respect the lock file.
- `uv run ruff check` and `uv run ruff format --check` enforce style and formatting.
- `uv run pytest`, `uv run mypy src scripts`, and `uv run bandit -r scripts` provide unit, type, and security coverage.
- The processing job executes `uv run hotpass --archive --dist-dir dist` before collecting artifacts.

Successful runs upload the refined workbook and zipped archive; pushes to `main` still publish the archive to the `data-artifacts` branch.

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
- [Enhancement Guide](docs/enhancement-guide.md) – NEW: Comprehensive guide to new features including formatting, validation, logging, and recommendations.
- [Implementation Guide](docs/implementation-guide.md) – How to use advanced features.
- [Gap Analysis](docs/gap-analysis.md) – Roadmap for future enhancements.
- [Quick Start](docs/quick-start.md) – Common usage scenarios.

### Building the documentation site

```bash
uv run sphinx-build -b html docs/source docs/_build/html
open docs/_build/html/index.html  # macOS; use xdg-open on Linux
```

The build consumes Markdown via MyST and auto-generates API documentation from the `src/` package.

## Contributing

1. Make changes in a branch.
2. Test locally.
3. Create a PR; GitHub Actions will run the processing pipeline.

## Benchmarking and performance monitoring

Use the lightweight benchmarking helper to capture baseline throughput and guard against regressions:

```bash
uv run python scripts/benchmark_pipeline.py \
  --input-dir data \
  --output-path dist/benchmark.xlsx \
  --runs 5 \
  --excel-chunk-size 5000 \
  --json
```

The command runs the pipeline multiple times, aggregates average stage timings (load, aggregation, expectations, write), and emits both JSON summaries and human-readable output. The data is also available programmatically via `hotpass.benchmarks.run_benchmark` for integration into CI checks or monitoring dashboards.
