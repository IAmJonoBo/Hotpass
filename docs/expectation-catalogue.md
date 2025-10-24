# Expectation Catalogue

This catalogue records the active data quality expectations enforced by `hotpass.quality`. Update it whenever thresholds shift or new rules are introduced so stakeholders can anticipate impacts.

| Expectation | Target Table / Column | Rule Type | Default Threshold | Notes |
| --- | --- | --- | --- | --- |
| `expect_table_row_count_to_be_between` | `schools` | Row count | min 1 | Guards against empty extracts before downstream processing.
| `expect_column_values_to_not_be_null` | `schools.school_name` | Completeness | 1.0 | Zero tolerance for missing institution names.
| `expect_column_values_to_be_in_set` | `schools.province` | Domain | 1.0 | Validates against ISO 3166-2 province list.
| `expect_column_values_to_match_regex` | `schools.contact_primary_email` | Format | 0.85 `mostly` | Matches RFC5322-inspired email regex; blanks treated as null-equivalent.
| `expect_column_values_to_match_regex` | `schools.contact_primary_phone` | Format | 0.85 `mostly` | Uses E.164 regex; integrates with `phonenumbers` clean-up.
| `expect_column_values_to_match_regex` | `schools.website` | Format | 0.85 `mostly` | Ensures URLs include scheme and host.
| `expect_column_values_to_be_unique` | `schools.school_id` | Uniqueness | 1.0 | Guarantees deduplicated SSOT identifiers.
| `expect_column_pair_values_A_to_be_greater_than_B` | `schools.last_validated_at` vs. `ingestion_timestamp` | Consistency | 1.0 | Ensures validation timestamps lag ingestion by ≤0 seconds.

## Operational Notes
- When expectation failures occur, capture remediation plans in `Next_Steps.md` under *Steps* and *Risks / Notes*.
- Adjust `mostly` thresholds only with data governance approval. Document the rationale, dataset scope, and rollback trigger here.
- During research cadences outlined in `docs/architecture-overview.md`, rerun the full expectation suite against candidate sources and record variance in this file.

## Privacy Reminder
Expectation outputs may surface sample values in debugging logs. Continue to mask or redact PII when sharing run artefacts to remain aligned with the POPIA guidance captured in `Next_Steps.md` and reiterated in the architecture overview.
