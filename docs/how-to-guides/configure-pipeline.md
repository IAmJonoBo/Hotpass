---
title: How-to — configure Hotpass for your organisation
summary: Customise industry profiles, column mapping, and runtime options to fit your data landscape.
last_updated: 2025-10-26
---

# How-to — configure Hotpass for your organisation

Hotpass ships with aviation defaults but can be tailored to any industry. Follow these steps to align the platform with your organisation’s data.

## 1. Select or create an industry profile

Profiles define synonyms, validation thresholds, and contact preferences.

```python
from hotpass.config import get_default_profile

profile = get_default_profile("aviation")
print(profile.display_name)
```

To create your own profile, add a YAML file under `src/hotpass/profiles/`:

```yaml
name: healthcare
display_name: Healthcare Facilities
default_country_code: US
organization_term: facility
source_priorities:
  Cms Database: 3
  State Registry: 2
column_synonyms:
  organization_name:
    - facility_name
    - provider_name
```

Reload the profile in Python:

```python
from hotpass.config import load_industry_profile
healthcare = load_industry_profile("healthcare")
```

## 2. Tune the pipeline configuration

Copy `config/pipeline.example.yaml` and adjust the options you need:

- `input_dir` / `output_path`: point to your source and destination folders.
- `archive`: enable to keep the original spreadsheets for auditing.
- `country_code`: default for phone and address parsing.
- `validation`: override thresholds per field type.

Run the pipeline with the custom config:

```bash
uv run hotpass --config config/pipeline.healthcare.yaml
```

## 3. Extend column mapping

Add business-specific column names directly in the profile or register them at runtime:

```python
from hotpass.column_mapping import ColumnMapper

mapper = ColumnMapper(profile.column_synonyms)
result = mapper.map_columns(["facility", "mail", "phone_number"])
print(result.mapped)
```

Use the `profile.column_synonyms` dictionary to audit which columns are automatically detected and which need manual mapping.

## 4. Configure contact management

Hotpass can consolidate multiple contacts per organisation. Set source priority and deduplication behaviour in your profile or config:

```yaml
contacts:
  prefer_roles:
    - Primary Contact
    - Account Manager
  fallback_to_first_seen: true
```

```python
from hotpass.contacts import consolidate_contacts_from_rows
consolidated = consolidate_contacts_from_rows(
    organization_name="Acme Corp",
    rows=df[df["organization_name"] == "Acme Corp"],
    source_priority={"CRM": 3, "Spreadsheet": 1},
)
primary = consolidated.get_primary_contact()
```

## 5. Validate the configuration

Run tests before promoting changes:

```bash
uv run pytest tests/test_config.py tests/test_contacts.py
```

A green test suite confirms your configuration behaves as expected across the supported use cases.

## 6. Enforce consent validation

The enhanced pipeline now enforces consent for POPIA-regulated fields. When you enable compliance with `EnhancedPipelineConfig(enable_compliance=True)`, the pipeline checks that every record requiring consent has a granted status.

1. **Capture consent sources** — Extend your upstream data to include a `consent_status` column (`granted`, `pending`, `revoked`, etc.).
2. **Map overrides** — Provide overrides per organisation when you orchestrate the pipeline:

   ```python
   from hotpass.pipeline_enhanced import EnhancedPipelineConfig

   config = EnhancedPipelineConfig(
       enable_compliance=True,
       consent_overrides={
           "test-org-1": "granted",
           "Example Flight School": "granted",
       },
   )
   ```

   Overrides can use the organisation slug (`organization_slug`) or the display name; they update the `consent_status` column before validation runs.
3. **Review the compliance report** — `PipelineResult.compliance_report` includes a summary of consent statuses and any violations detected. A `ConsentValidationError` stops the run if any required record lacks a granted status.

Consent statuses are case-insensitive. The defaults treat `granted`/`approved` as valid, `pending`/`unknown` as awaiting action, and `revoked`/`denied` as blockers. Adjust `consent_granted_statuses`, `consent_pending_statuses`, or `consent_denied_statuses` via `POPIAPolicy` if your organisation uses different terminology.
