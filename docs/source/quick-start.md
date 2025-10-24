# Quick Start: Using Hotpass Enhanced Features

This guide shows how to quickly get started with the new Hotpass capabilities for intelligent data consolidation.

## For First-Time Users

### 1. Choose Your Industry Profile

Hotpass now works for any industry, not just aviation:

```python
from hotpass.config import get_default_profile

# Aviation (flight schools, training centers)
profile = get_default_profile("aviation")

# Or generic business
profile = get_default_profile("generic")
```

### 2. Automatically Map Your Columns

Don't worry about exact column names - Hotpass figures it out:

```python
from hotpass.column_mapping import ColumnMapper
import pandas as pd

# Load your data
df = pd.read_excel("your_data.xlsx")

# Create mapper with synonyms from profile
mapper = ColumnMapper(profile.column_synonyms)

# Auto-map columns
result = mapper.map_columns(list(df.columns))
print("Mapped:", result["mapped"])
print("Needs review:", result["suggestions"])

# Apply mapping
df = mapper.apply_mapping(df, result["mapped"])
```

### 3. Profile Your Data Quality

Get instant insights about your data:

```python
from hotpass.column_mapping import profile_dataframe

profile = profile_dataframe(df)
print(f"Rows: {profile['row_count']}")
print(f"Columns: {profile['column_count']}")
print(f"Duplicates: {profile['duplicate_rows']}")

# Check each column
for col, stats in profile["columns"].items():
    print(f"{col}: {stats['missing_percentage']:.1f}% missing")
```

### 4. Handle Multiple Contacts Gracefully

If you have multiple contacts per organization:

```python
from hotpass.contacts import consolidate_contacts_from_rows

# Consolidate contacts from your rows
org_contacts = consolidate_contacts_from_rows(
    organization_name="Acme Corp",
    rows=df[df["organization_name"] == "Acme Corp"],
    source_priority={"Source A": 3, "Source B": 1}
)

# Get best contact automatically
primary = org_contacts.get_primary_contact()
print(f"Primary: {primary.name} - {primary.email}")

# Get all contacts
all_emails = org_contacts.get_all_emails()
print(f"All emails: {', '.join(all_emails)}")
```

### 5. Export with Professional Formatting

Create beautiful Excel files automatically:

```python
from hotpass.formatting import export_to_multiple_formats
from pathlib import Path

# Export to multiple formats at once
outputs = export_to_multiple_formats(
    df=df,
    base_path=Path("output/data"),
    formats=["excel", "csv"],
)

print(f"Excel: {outputs['excel']}")
print(f"CSV: {outputs['csv']}")
```

## For Existing Users

### Migrating to Industry Profiles

If you're currently using Hotpass for aviation data:

```python
# Old way - hard-coded
# from hotpass.pipeline import run_pipeline

# New way - configurable
from hotpass.config import load_industry_profile
from hotpass.pipeline import run_pipeline, PipelineConfig

profile = load_industry_profile("aviation")
config = PipelineConfig(
    input_dir=Path("data"),
    output_path=Path("data/refined.xlsx"),
    country_code=profile.default_country_code,
)

result = run_pipeline(config)
```

### Adding Error Tracking

Track and report errors systematically:

```python
from hotpass.error_handling import ErrorHandler, ErrorContext, ErrorCategory, ErrorSeverity

handler = ErrorHandler(fail_fast=False)

# During processing, report errors
if some_validation_fails:
    context = ErrorContext(
        category=ErrorCategory.VALIDATION_FAILURE,
        severity=ErrorSeverity.WARNING,
        message="Email format invalid",
        suggested_fix="Ensure email contains @ symbol",
    )
    handler.handle_error(context)

# At the end, get report
report = handler.get_report()
if report.has_errors():
    print(report.to_markdown())
```

## Common Scenarios

### Scenario 1: New Data Source with Unknown Schema

```python
from hotpass.column_mapping import ColumnMapper, profile_dataframe
from hotpass.config import load_industry_profile
import pandas as pd

# 1. Load the unknown data
df = pd.read_excel("new_source.xlsx")

# 2. Profile it to understand structure
profile_data = profile_dataframe(df)
print(f"Found {profile_data['column_count']} columns")

# 3. Infer types
for col, dtype in profile_data["inferred_types"].items():
    print(f"{col}: {dtype}")

# 4. Map to standard schema
profile = load_industry_profile("generic")
mapper = ColumnMapper(profile.column_synonyms)
mapping = mapper.map_columns(list(df.columns))

# 5. Review suggestions and apply
print("Suggested mappings:", mapping["suggestions"])
df_mapped = mapper.apply_mapping(df, mapping["mapped"])
```

### Scenario 2: Consolidating Multiple Files

```python
from hotpass.column_mapping import ColumnMapper
from hotpass.config import load_industry_profile
import pandas as pd

profile = load_industry_profile("generic")
mapper = ColumnMapper(profile.column_synonyms)

all_dfs = []
for file in ["file1.xlsx", "file2.xlsx", "file3.xlsx"]:
    df = pd.read_excel(file)

    # Map each file's columns
    mapping = mapper.map_columns(list(df.columns))
    df_mapped = mapper.apply_mapping(df, mapping["mapped"])

    all_dfs.append(df_mapped)

# Combine all with consistent columns
combined = pd.concat(all_dfs, ignore_index=True)
```

### Scenario 3: Creating Custom Industry Profile

```yaml
# Save as: src/hotpass/profiles/retail.yaml
name: retail
display_name: Retail Stores
default_country_code: US

organization_term: store
organization_type_term: store_type
organization_category_term: retail_category

column_synonyms:
  organization_name:
    - store_name
    - location_name
    - branch_name
  contact_email:
    - email
    - store_email
    - manager_email
  contact_phone:
    - phone
    - store_phone

required_fields:
  - organization_name

optional_fields:
  - contact_primary_email
  - address_primary
```

Then use it:

```python
from hotpass.config import load_industry_profile

retail_profile = load_industry_profile("retail")
print(retail_profile.display_name)  # "Retail Stores"
```

## Tips for Success

1. **Start with profiling** - Always profile unknown data first
2. **Review mapping suggestions** - Check medium-confidence mappings before proceeding
3. **Use error handlers** - Catch and report issues systematically
4. **Test with small datasets** - Verify mappings work before processing large files
5. **Customize profiles** - Create industry-specific profiles for your domain
6. **Track contact preferences** - Use scoring to select best contacts automatically

## Next Steps

- Read the full [Implementation Guide](implementation-guide.md)
- Review [Gap Analysis](gap-analysis.md) for upcoming features
- Check [Architecture Overview](architecture-overview.md) for system design
- Explore test files for more examples: `tests/test_*.py`

## Getting Help

If you encounter issues:

1. Check the error report generated by `ErrorHandler`
2. Review column mapping suggestions
3. Examine data profile output for anomalies
4. Consult the [Implementation Guide](implementation-guide.md)
5. Look at test files for working examples
