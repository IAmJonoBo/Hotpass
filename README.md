# Hotpass Data Refinement Repository

This repository is optimized for validating, normalizing, processing, and refining multiple Excel documents into a highly-refined single source of truth. It uses Python with libraries like pandas, pandera, and great-expectations for data quality assurance.

## Project Structure

- `data/`: Contains input Excel files. Run the pipeline to regenerate the refined workbook (ignored in git).
- `scripts/`: Python scripts for data processing.
- `docs/`: Additional documentation.
- `.github/workflows/`: GitHub Actions for automated processing.

## Setup

1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Place your Excel files in the `data/` directory.
4. Run the processing script to regenerate the refined workbook: `python scripts/process_data.py`. Pass `--archive` to also produce a timestamped, checksum-stamped zip under `dist/` for distribution.

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

- **Local runs**: `python scripts/process_data.py --archive` writes the refined workbook to `data/refined_data.xlsx` and a zip archive named `refined-data-<timestamp>-<checksum>.zip` to `dist/`. The archive contains the workbook and a `SHA256SUMS` manifest so the checksum in the filename can be verified.
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

## Contributing

1. Make changes in a branch.
2. Test locally.
3. Create a PR; GitHub Actions will run the processing pipeline.
