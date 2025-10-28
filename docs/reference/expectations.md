---
title: Reference — data quality expectations
summary: Catalogue of Great Expectations suites enforced by the Hotpass pipeline.
last_updated: 2025-10-25
---

# Reference — data quality expectations

Hotpass uses [Great Expectations](https://greatexpectations.io/) to protect downstream consumers. Expectations are grouped by domain and run during validation and orchestration.

## Core dataset checks

| Expectation                                  | Description                                       |
| -------------------------------------------- | ------------------------------------------------- |
| `expect_table_row_count_to_be_between`       | Validates overall row counts per source workbook. |
| `expect_table_columns_to_match_ordered_list` | Ensures the canonical SSOT schema is intact.      |
| `expect_table_columns_to_not_be_null`        | Asserts that required fields are populated.       |

## Contact quality

| Expectation                               | Description                                              |
| ----------------------------------------- | -------------------------------------------------------- |
| `expect_column_values_to_match_regex`     | Validates email, phone, and URL formats.                 |
| `expect_column_values_to_be_unique`       | Prevents duplicate contact identifiers within a dataset. |
| `expect_column_values_to_not_match_regex` | Blocks placeholder values such as `test@example.com`.    |

## Compliance and PII

| Expectation                               | Description                                                                |
| ----------------------------------------- | -------------------------------------------------------------------------- |
| `expect_column_values_to_not_contain_pii` | Flags sensitive personal information detected by Presidio.                 |
| `expect_column_values_to_be_in_set`       | Restricts status values to the approved list (`active`, `inactive`, etc.). |

## Enrichment coverage

| Expectation                                              | Description                                                                                  |
| -------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `expect_column_values_to_not_be_null`                    | Verifies that enrichment fields (geocodes, registry IDs) are populated for critical records. |
| `expect_select_column_values_to_be_unique_within_record` | Ensures enrichment sources do not emit duplicate identifiers for the same record.            |

## Observability metrics

Validation outputs are published to the quality report and to Prefect logs. Metrics include:

- `hotpass.validation.failures`
- `hotpass.validation.warnings`
- `hotpass.validation.runtime`

Refer to the [telemetry how-to](../how-to-guides/orchestrate-and-observe.md) for guidance on exporting these metrics.

## Probabilistic linkage metrics

Probabilistic linkage runs emit scored pairs and review queues alongside the
refined dataset. A synthetic 600-record benchmark (300 unique entities, 300
duplicates) produced the following metrics using RapidFuzz-backed blocking:

| Scenario                                   | Total records | Unique entities | Matches scored | Review queue | Runtime |
| ------------------------------------------ | ------------- | --------------- | -------------- | ------------ | ------- |
| Rule-based linkage (0.9 match, 0.7 review) | 600           | 300             | 300            | 0            | 0.2s    |

Persisted artefacts contain match probabilities, review routing thresholds, and
any reviewer decisions retrieved from Label Studio to support retraining and
auditing.
