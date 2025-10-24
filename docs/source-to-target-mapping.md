# Source-to-Target Mapping

Use this catalogue to trace how upstream source columns populate the SSOT schema defined in `docs/ssot-field-dictionary.md`. Update mappings whenever ingestion adapters evolve or new providers are onboarded.

| SSOT Field | SACAA Registry | ReachOut CRM | Legacy Contact DB | Transformation Notes |
| --- | --- | --- | --- | --- |
| `school_id` | `provider_uuid` | `crm_id` | `legacy_key` | Generated via deterministic hashing across available source identifiers ordered by reliability (SACAA > ReachOut > Legacy).
| `school_name` | `institution_name` | `account_name` | `provider_name` | Normalise whitespace, apply title casing, and strip trailing campus descriptors moved to `campus_name`.
| `campus_name` | `campus` | `location_name` | `branch_name` | Prefer SACAA `campus`; fallback to ReachOut when blank.
| `province` | `province` | `province` | `province` | Harmonise to ISO 3166-2 codes via lookup table.
| `city` | `city` | `city` | `town` | Fuzzy match to canonical list; log mismatches for steward review.
| `address_line_1` | `street_address` | `street_1` | `address_primary` | Combine unit numbers and street names; drop PO Boxes when a street exists.
| `address_line_2` | `suburb` | `street_2` | `address_secondary` | Preserved when provided after normalisation.
| `postal_code` | `postal_code` | `zip` | `postal_code` | Validate against SAPO list; fallback to ReachOut when SACAA missing.
| `contact_primary_name` | `primary_contact` | `primary_contact_name` | `main_contact` | Split into first/last internally for analytics while retaining display form.
| `contact_primary_email` | `primary_email` | `email` | `email_main` | Deduplicate using case-insensitive comparison; expectation threshold 0.85.
| `contact_primary_phone` | `primary_phone` | `phone` | `tel_main` | Normalise to E.164; drop extensions for now.
| `contact_secondary_email` | `secondary_email` | `alt_email` | `email_secondary` | Multi-email sources split before loading.
| `contact_secondary_phone` | `secondary_phone` | `alt_phone` | `tel_secondary` | Only persisted when valid after `phonenumbers` parsing.
| `website` | `website` | `website` | `url` | Enforce HTTPS preference and canonical host lower-casing.
| `accreditation_status` | `status` | _n/a_ | `accreditation_flag` | Use SACAA when present; fallback to Legacy flag mapping.
| `last_validated_at` | `last_audit_date` | `last_reviewed` | `last_verified` | Convert to timezone-aware UTC.
| `source_rank` | Derived | Derived | Derived | Set to 1 for SACAA, 2 for ReachOut, 3 for Legacy contact DB.
| `source_dataset` | `SACAA` | `ReachOut` | `LegacyContacts` | Recorded for provenance trail.
| `notes` | `remarks` | `notes` | `notes` | Merge free-text with precedence SACAA > ReachOut > Legacy.

## Maintenance Workflow
1. Capture mapping updates in a feature branch alongside adapter code changes.
2. Run the full QA workflow (`ruff`, `pytest`, `mypy`, `bandit`, `python -m build`) before requesting review.
3. Document any temporary deviations (e.g., missing fields) in `Next_Steps.md` under *Risks / Notes* with expected resolution timelines.
