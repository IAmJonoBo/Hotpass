# SSOT Field Dictionary

This reference enumerates the canonical columns emitted by the Hotpass refined workbook. Use it to harmonise upstream mappings and downstream consumption contracts.

| Field Name | Data Type | Description | Notes |
| --- | --- | --- | --- |
| `school_id` | `string` | Stable UUID assigned by Hotpass during aggregation. | Generated from source identity keys and provenance metadata.
| `school_name` | `string` | Official provider name after normalisation. | Trims whitespace and title-cases common particles.
| `campus_name` | `string` | Campus or satellite site name. | Optional; blank when the provider is single-site.
| `province` | `string` | Province aligned to South African ISO 3166-2 codes. | Derived via lookup table maintained in `data/reference/province_map.csv`.
| `city` | `string` | Primary municipality or town. | Normalised using fuzzy matching to reduce spelling drift.
| `address_line_1` | `string` | First line of the mailing address. | Removes PO Box markers when a street address is available.
| `address_line_2` | `string` | Second line of the mailing address. | Optional.
| `postal_code` | `string` | Four-digit South African postal code. | Validated against the official SAPO reference list.
| `contact_primary_name` | `string` | Primary contact full name. | Splits composite name fields into first/last components for analytics.
| `contact_primary_email` | `string` | Primary contact email address. | Must satisfy expectation `expect_column_values_to_match_regex` with 0.85 `mostly` threshold.
| `contact_primary_phone` | `string` | Primary contact phone in E.164 format. | Normalised using `phonenumbers` with ZA defaults.
| `contact_secondary_email` | `string` | Secondary email where available. | Captured when multi-email sources are ingested.
| `contact_secondary_phone` | `string` | Secondary phone where available. | Only populated for records with verified alternate contacts.
| `website` | `string` | Public website URL. | Canonicalised with scheme and host lower-casing.
| `accreditation_status` | `string` | Accreditation classification (e.g., `Approved`, `Suspended`). | Derived from SACAA and supplemental data feeds.
| `last_validated_at` | `datetime` | Timestamp when expectations last passed for the record. | Updated after each successful pipeline run.
| `source_rank` | `integer` | Reliability ranking of the selected source record. | Lower numbers indicate higher trust (e.g., 1 = SACAA).
| `source_dataset` | `string` | Name of the contributing dataset. | Provides traceability for downstream audits.
| `notes` | `string` | Free-form data steward annotations. | Use to capture overrides or contextual flags.

## Stewardship Practices
- Reflect field additions or removals here as part of any schema change PR.
- Capture rationale for expectation threshold adjustments alongside the relevant field row.
- Reference POPIA guidance from `docs/architecture-overview.md` when proposing new PII fields.
