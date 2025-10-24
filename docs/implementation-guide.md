# Hotpass Enhancement Implementation Guide

This guide explains how to use the new features added in the comprehensive upgrade to make Hotpass more flexible, intelligent, and industry-agnostic.

## Table of Contents

1. [Industry Profiles](#industry-profiles)
2. [Intelligent Column Mapping](#intelligent-column-mapping)
3. [Enhanced Error Handling](#enhanced-error-handling)
4. [Advanced Contact Management](#advanced-contact-management)
5. [Data Profiling](#data-profiling)
6. [Enhanced Output Formatting](#enhanced-output-formatting)

## Industry Profiles

Industry profiles allow you to customize Hotpass for different business domains beyond aviation.

### Using Built-in Profiles

```python
from hotpass.config import get_default_profile, load_industry_profile

# Get the aviation profile (default)
aviation_profile = get_default_profile("aviation")
print(aviation_profile.display_name)  # "Aviation & Flight Training"

# Get the generic business profile
generic_profile = get_default_profile("generic")
```

### Creating Custom Profiles

Create a YAML file in `src/hotpass/profiles/` directory:

```yaml
# healthcare.yaml
name: healthcare
display_name: Healthcare Facilities
default_country_code: US

organization_term: facility
organization_type_term: facility_type
organization_category_term: specialty

email_validation_threshold: 0.85
phone_validation_threshold: 0.85
website_validation_threshold: 0.75

source_priorities:
  CMS Database: 3
  State Registry: 2
  Contact List: 1

column_synonyms:
  organization_name:
    - facility_name
    - hospital_name
    - clinic_name
    - provider_name
  contact_email:
    - email
    - contact_email
    - admin_email
  contact_phone:
    - phone
    - main_phone
    - facility_phone

required_fields:
  - organization_name
  - contact_primary_email

optional_fields:
  - website
  - address_primary
```

Load your custom profile:

```python
from hotpass.config import load_industry_profile

healthcare_profile = load_industry_profile("healthcare")
```

## Intelligent Column Mapping

Automatically map source columns to target schema using fuzzy matching and synonyms.

### Basic Column Mapping

```python
from hotpass.column_mapping import ColumnMapper
from hotpass.config import get_default_profile
import pandas as pd

# Load profile with column synonyms
profile = get_default_profile("aviation")

# Create mapper with target schema
mapper = ColumnMapper(profile.column_synonyms)

# Your source data
df = pd.DataFrame({
    "School Name": ["ABC Flight School"],
    "Contact Email Address": ["info@abc.com"],
    "Phone": ["+27123456789"],
})

# Map columns automatically
mapping_result = mapper.map_columns(list(df.columns), confidence_threshold=0.7)

print("Mapped columns:", mapping_result["mapped"])
# Output: {'School Name': 'organization_name', 'Contact Email Address': 'contact_email', ...}

# Apply the mapping
df_mapped = mapper.apply_mapping(df, mapping_result["mapped"])
print(df_mapped.columns)
# Output: Index(['organization_name', 'contact_email', 'contact_phone'], dtype='object')
```

### Column Type Inference

Automatically infer semantic types of columns:

```python
from hotpass.column_mapping import infer_column_types

df = pd.DataFrame({
    "email": ["user@example.com", "admin@site.org"],
    "phone": ["+1234567890", "+9876543210"],
    "website": ["https://example.com", "www.site.org"],
})

types = infer_column_types(df)
print(types)
# Output: {'email': 'email', 'phone': 'phone', 'website': 'url'}
```

### Data Profiling

Get comprehensive statistics about your data:

```python
from hotpass.column_mapping import profile_dataframe

df = pd.DataFrame({
    "name": ["Alice", "Bob", None],
    "email": ["alice@test.com", "bob@test.com", "charlie@test.com"],
    "score": [1, 2, 3],
})

profile = profile_dataframe(df)
print(f"Rows: {profile['row_count']}")
print(f"Columns: {profile['column_count']}")
print(f"Duplicates: {profile['duplicate_rows']}")
print(f"Memory: {profile['memory_usage_mb']:.2f} MB")

# Column-level statistics
for col, stats in profile["columns"].items():
    print(f"{col}: {stats['missing_percentage']:.1f}% missing")
```

## Enhanced Error Handling

Structured error handling with categorization and recovery suggestions.

### Using the Error Handler

```python
from hotpass.error_handling import (
    ErrorHandler,
    ErrorContext,
    ErrorCategory,
    ErrorSeverity,
    ValidationError,
)

# Create error handler (fail_fast=False accumulates errors)
handler = ErrorHandler(fail_fast=False)

# Report validation errors
try:
    # Your validation logic
    email = "invalid-email"
    if "@" not in email:
        error = ValidationError.create(
            field="email",
            value=email,
            expected="valid email with @ symbol",
            row=5,
            source_file="contacts.xlsx",
        )
        handler.handle_error(error.context)
except Exception as e:
    # Handle unexpected errors
    context = ErrorContext(
        category=ErrorCategory.PROCESSING_ERROR,
        severity=ErrorSeverity.ERROR,
        message=str(e),
        recoverable=True,
    )
    handler.handle_error(context)

# Get accumulated error report
report = handler.get_report()
print(f"Total errors: {report.get_summary()['total_errors']}")

# Export as markdown
with open("error_report.md", "w") as f:
    f.write(report.to_markdown())
```

### Error Categories

Available error categories:

- `FILE_NOT_FOUND`: Missing input files
- `SCHEMA_MISMATCH`: Column structure doesn't match expected
- `VALIDATION_FAILURE`: Data doesn't meet validation rules
- `DATA_QUALITY`: Poor data quality issues
- `INVALID_FORMAT`: Wrong data format
- `DUPLICATE_RECORD`: Duplicate entries
- `CONFIGURATION_ERROR`: Invalid configuration

### Error Severities

- `INFO`: Informational messages
- `WARNING`: Issues that don't prevent processing
- `ERROR`: Serious issues that may affect results
- `CRITICAL`: Fatal issues that prevent processing

## Advanced Contact Management

Handle multiple contacts per organization with intelligent preference scoring.

### Managing Organization Contacts

```python
from hotpass.contacts import Contact, OrganizationContacts

# Create organization contact manager
org = OrganizationContacts("Acme Flight School")

# Add contacts
ceo = Contact(
    name="John Doe",
    email="john@acme.com",
    phone="+27123456789",
    role="CEO",
    department="Executive",
)

manager = Contact(
    name="Jane Smith",
    email="jane@acme.com",
    phone="+27987654321",
    role="Operations Manager",
    department="Operations",
)

org.add_contact(ceo)
org.add_contact(manager)

# Calculate preference scores
org.calculate_preference_scores(
    source_priority={"SACAA": 3, "Contact DB": 1},
    role_weight=0.5,
    completeness_weight=0.3,
    recency_weight=0.2,
)

# Get primary contact (highest preference)
primary = org.get_primary_contact()
print(f"Primary contact: {primary.name} ({primary.role})")

# Get all emails
all_emails = org.get_all_emails()
print(f"All emails: {', '.join(all_emails)}")

# Convert to flat format for SSOT output
flat_dict = org.to_flat_dict()
print(flat_dict["contact_primary_email"])
print(flat_dict["contact_secondary_emails"])
```

### Consolidating from DataFrame

```python
from hotpass.contacts import consolidate_contacts_from_rows
import pandas as pd

# DataFrame with multiple contacts per organization
df = pd.DataFrame({
    "source_dataset": ["SACAA", "Contact DB"],
    "contact_names": [["John Doe"], ["Jane Smith"]],
    "contact_emails": [["john@acme.com"], ["jane@acme.com"]],
    "contact_phones": [["+27123456789"], ["+27987654321"]],
    "contact_roles": [["CEO"], ["Manager"]],
})

org_contacts = consolidate_contacts_from_rows(
    "Acme Flight School",
    df,
    source_priority={"SACAA": 3, "Contact DB": 1},
)

print(f"Total contacts: {len(org_contacts.contacts)}")
```

## Data Profiling

Profile your data before processing to understand its structure and quality.

### Quick Profile

```python
from hotpass.column_mapping import profile_dataframe
import pandas as pd

df = pd.read_excel("data/input.xlsx")
profile = profile_dataframe(df)

# Overall statistics
print(f"Dataset has {profile['row_count']} rows and {profile['column_count']} columns")
print(f"Memory usage: {profile['memory_usage_mb']:.2f} MB")
print(f"Duplicate rows: {profile['duplicate_rows']} ({profile['duplicate_percentage']:.1f}%)")

# Column analysis
for col, stats in profile["columns"].items():
    print(f"\n{col}:")
    print(f"  Type: {stats['dtype']}")
    print(f"  Inferred semantic type: {profile['inferred_types'].get(col, 'unknown')}")
    print(f"  Missing: {stats['missing_count']} ({stats['missing_percentage']:.1f}%)")
    print(f"  Unique values: {stats['unique_count']} ({stats['unique_percentage']:.1f}%)")
    print(f"  Sample values: {', '.join(stats['sample_values'][:3])}")
```

## Enhanced Output Formatting

Create professional-looking Excel outputs with formatting and summaries.

### Basic Excel Formatting

```python
from hotpass.formatting import OutputFormat, apply_excel_formatting, export_to_multiple_formats
import pandas as pd

df = pd.DataFrame({
    "organization_name": ["Acme Inc", "XYZ Corp"],
    "data_quality_score": [0.85, 0.45],
    "email": ["info@acme.com", "contact@xyz.com"],
})

# Export with default formatting
with pd.ExcelWriter("output.xlsx", engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="Data", index=False)
    apply_excel_formatting(writer, "Data", df)
```

### Custom Formatting

```python
# Create custom format configuration
custom_format = OutputFormat(
    header_bg_color="4472C4",  # Blue header
    header_font_color="FFFFFF",  # White text
    quality_excellent_bg="70AD47",  # Green for excellent
    quality_good_bg="FFC000",  # Orange for good
    quality_fair_bg="ED7D31",  # Light red for fair
    quality_poor_bg="C00000",  # Dark red for poor
    font_name="Arial",
    font_size=10,
    auto_size_columns=True,
    freeze_header_row=True,
    add_filters=True,
    zebra_striping=True,
)

with pd.ExcelWriter("formatted_output.xlsx", engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="Data", index=False)
    apply_excel_formatting(writer, "Data", df, custom_format)
```

### Multi-Format Export

```python
from pathlib import Path

# Export to multiple formats at once
output_paths = export_to_multiple_formats(
    df=df,
    base_path=Path("output/refined_data"),
    formats=["excel", "csv", "parquet", "json"],
    format_config=custom_format,
    quality_report={"total_records": 100, "invalid_records": 5},
)

for fmt, path in output_paths.items():
    print(f"{fmt}: {path}")
```

## Integration Example

Here's a complete example integrating multiple features:

```python
from pathlib import Path
import pandas as pd

from hotpass.config import load_industry_profile
from hotpass.column_mapping import ColumnMapper, profile_dataframe
from hotpass.error_handling import ErrorHandler
from hotpass.contacts import consolidate_contacts_from_rows
from hotpass.formatting import export_to_multiple_formats

# 1. Load industry profile
profile = load_industry_profile("aviation")
print(f"Using profile: {profile.display_name}")

# 2. Load and profile source data
df = pd.read_excel("data/source.xlsx")
data_profile = profile_dataframe(df)
print(f"Loaded {data_profile['row_count']} rows")

# 3. Map columns intelligently
mapper = ColumnMapper(profile.column_synonyms)
mapping_result = mapper.map_columns(list(df.columns))
df_mapped = mapper.apply_mapping(df, mapping_result["mapped"])

# 4. Initialize error handler
error_handler = ErrorHandler(fail_fast=False)

# 5. Process data with error handling
# (Your processing logic here)

# 6. Export with formatting
export_to_multiple_formats(
    df=df_mapped,
    base_path=Path("output/final"),
    formats=["excel", "csv"],
    quality_report={"total_records": len(df_mapped)},
)

# 7. Generate error report
if error_handler.get_report().has_errors():
    with open("errors.md", "w") as f:
        f.write(error_handler.get_report().to_markdown())

print("Processing complete!")
```

## Best Practices

1. **Always use industry profiles** to ensure consistent terminology and validation rules
2. **Profile your data first** to understand its structure and quality before processing
3. **Use column mapping** to handle schema variations across data sources
4. **Implement error handling** throughout your pipeline for robustness
5. **Calculate contact preference scores** before selecting primary contacts
6. **Apply formatting** to make outputs more user-friendly
7. **Export to multiple formats** to support different downstream consumers

## Next Steps

- Review the gap analysis document: `docs/gap-analysis.md`
- Explore the architecture overview: `docs/architecture-overview.md`
- Check the test files for more usage examples
- Customize industry profiles for your specific use case
