---
title: Explanation — architecture overview
summary: High-level view of Hotpass components and how data flows between them.
last_updated: 2025-10-25
---

# Explanation — architecture overview

Hotpass ingests disparate spreadsheets, applies validation, enrichment, and consolidation logic, and emits a governed single source of truth. The platform is composed of the following layers.

## 1. Ingestion

- **CLI and orchestration**: Users trigger runs via the CLI or Prefect deployments.
- **Profiles**: YAML-defined industry profiles provide configuration for synonyms, validation thresholds, and contact preferences.
- **Data loaders**: Parsers convert Excel, CSV, and Parquet into Pandas dataframes while preserving lineage metadata.

## 2. Processing

- **Column mapping**: Fuzzy matching and synonym dictionaries align source headers with canonical fields.
- **Entity resolution**: Splink-based duplicate detection merges overlapping organisations with deterministic fallbacks.
- **Validation**: Great Expectations suites ensure data quality and compliance with POPIA.
- **Enrichment**: Optional connectors add registry data, scraped insights, and geospatial coordinates.

## 3. Output

- **Formatter**: Produces Excel workbooks with consistent styling, plus CSV and Parquet exports.
- **Quality report**: Generates JSON and Markdown reports summarising validation outcomes.
- **Observability**: Emits Prefect task logs and OpenTelemetry metrics for pipeline health monitoring.

## 4. Supporting services

- **Dashboard**: Streamlit app visualises run history, validation failures, and enrichment coverage in real time.
- **Configuration doctor**: Diagnoses missing dependencies, misconfigured profiles, and schema drift.
- **Benchmarks**: Performance benchmarks guard against regressions in core operations.

The architecture emphasises modularity—each layer can be extended independently without disrupting the pipeline contract. See the [platform scope explanation](./platform-scope.md) for upcoming investments.
