# Hotpass Architecture Overview

## Purpose

The Hotpass pipeline transforms heterogeneous Excel source workbooks into a governed single source of truth (SSOT) workbook and corresponding packaged archive. The architecture is optimised for repeatable refinement, quality assurance, and provenance tracking so downstream consumers can trust the consolidated outputs.

## High-Level Flow

1. **Ingestion** – `hotpass.data_sources` loads vendor-specific Excel extracts, applies adapters for schema drift, and records provenance metadata.
2. **Normalization** – `hotpass.normalization` standardises field names, datatypes, and formats (e.g., phone, email, URL) while splitting multi-valued attributes into canonical structures.
3. **Expectation Validation** – `hotpass.quality` orchestrates Great Expectations (or the fallback equivalent) to evaluate column-level rules and aggregate data quality metrics.
4. **Aggregation & Conflict Resolution** – `hotpass.pipeline` merges normalised tables, prioritising records by configured reliability and recency scores while persisting the decision trail.
5. **Packaging & Distribution** – `hotpass.artifacts` writes the refined workbook to `data/refined_data.xlsx`, produces a checksum-stamped archive in `dist/`, and surfaces manifest metadata for publication.

## Operational Cadence & Research Guidance

- **Source Discovery** – Review new vendor feeds quarterly. Validate each candidate source by running it through the ingestion adapters in a sandbox branch and capturing expectation deltas. Capture decisions and rationale in `docs/source-to-target-mapping.md`.
- **Schema Drift Watch** – Monitor Great Expectations results in CI for threshold regressions. When match rates drop below configured tolerances, log the follow-up in `docs/upgrade-roadmap.md` and schedule schema alignment within the sprint.
- **Source Validation** – For every new or updated data provider, confirm license terms, run the full QA workflow locally (`uv run ruff`, `uv run pytest`, `uv run mypy`, `uv run bandit`), and document adjustments to normalization or mapping rules in this directory before merging.

## Privacy & Compliance

The pipeline must continue to honour POPIA-aligned privacy controls documented in this suite. Limit PII exposure by:

- Redacting optional contact attributes from shared QA reports.
- Ensuring archives contain only the refined workbook and checksum manifest.
- Restricting access to raw source dumps to authorised analysts and purging local copies after validation runs.

## Future Enhancements

- Integrate automated data catalog updates so field dictionary revisions propagate to dependent systems.
- Add observability hooks (metrics and alerts) for expectation drift and ingestion failures.
- Evaluate migrating to the modern Great Expectations `Validator` API once stable for Pandas 2.x.
