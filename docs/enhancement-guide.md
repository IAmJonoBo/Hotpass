# Enhancement Guide

## Overview

This document describes the recent enhancements to the Hotpass data refinement pipeline, including improved spreadsheet formatting, configurable validation, comprehensive logging, data quality recommendations, and configuration diagnostics.

## New Features

### 1. Enhanced Spreadsheet Formatting

The pipeline now supports customizable spreadsheet formatting with professional styling options.

#### Configuration

```python
from hotpass import PipelineConfig, OutputFormat, run_pipeline
from pathlib import Path

# Configure custom formatting
output_format = OutputFormat(
    header_bg_color="366092",
    header_font_color="FFFFFF",
    zebra_striping=True,
    auto_size_columns=True,
    freeze_header_row=True,
    add_filters=True,
)

config = PipelineConfig(
    input_dir=Path("data"),
    output_path=Path("output/refined.xlsx"),
    enable_formatting=True,
    output_format=output_format,
)

result = run_pipeline(config)
```

#### Features

- **Conditional formatting**: Automatically applies color-coding based on data quality scores
- **Auto-sized columns**: Columns are automatically resized for optimal readability
- **Zebra striping**: Alternating row colors for easier scanning
- **Frozen headers**: Top row frozen for easy navigation
- **Auto-filters**: Filters enabled on all columns
- **Summary sheet**: Automatically generated summary with key metrics

### 2. Configurable Validation Thresholds

Validation rules now use industry profile settings for flexible quality control.

#### Configuration

```python
from hotpass import IndustryProfile, PipelineConfig, run_pipeline
from pathlib import Path

# Create custom profile with specific thresholds
profile = IndustryProfile(
    name="healthcare",
    display_name="Healthcare Industry",
    email_validation_threshold=0.90,  # 90% of emails must be valid
    phone_validation_threshold=0.85,  # 85% of phones must be valid
    website_validation_threshold=0.75,  # 75% of websites must be valid
)

config = PipelineConfig(
    input_dir=Path("data"),
    output_path=Path("output/refined.xlsx"),
    industry_profile=profile,
)

result = run_pipeline(config)
```

#### Threshold Guidelines

- **0.95+**: Very strict, use when data quality is critical
- **0.85-0.90**: Recommended for most use cases
- **0.70-0.85**: Lenient, use for exploratory data
- **Below 0.70**: Very lenient, use only for low-quality sources

### 3. Comprehensive Audit Trail

Track every step of the pipeline execution with detailed audit logs.

#### Configuration

```python
from hotpass import PipelineConfig, run_pipeline
from pathlib import Path

config = PipelineConfig(
    input_dir=Path("data"),
    output_path=Path("output/refined.xlsx"),
    enable_audit_trail=True,  # Enable audit logging
)

result = run_pipeline(config)

# Access audit trail
for entry in result.quality_report.audit_trail:
    print(f"{entry['event']}: {entry['details']}")
```

#### Audit Events

- `pipeline_start`: Pipeline execution begins
- `sources_loaded`: Data sources successfully loaded
- `aggregation_complete`: Data aggregation finished
- `schema_validation_errors`: Schema validation issues detected
- `pipeline_complete`: Pipeline execution completed

### 4. Data Quality Recommendations

Automatic analysis and actionable recommendations for improving data quality.

#### Configuration

```python
from hotpass import PipelineConfig, run_pipeline
from pathlib import Path

config = PipelineConfig(
    input_dir=Path("data"),
    output_path=Path("output/refined.xlsx"),
    enable_recommendations=True,  # Enable recommendations
)

result = run_pipeline(config)

# View recommendations
for rec in result.quality_report.recommendations:
    print(f"- {rec}")
```

#### Types of Recommendations

- **Critical**: Average quality below 50%, urgent action needed
- **Warning**: Quality below 70% or high missing data rates
- **Informational**: Validation failures or quality flags
- **Suggestions**: Tips for improving specific records

### 5. Conflict Resolution Tracking

Track how conflicts between data sources are resolved.

```python
from hotpass import PipelineConfig, run_pipeline
from pathlib import Path

config = PipelineConfig(
    input_dir=Path("data"),
    output_path=Path("output/refined.xlsx"),
)

result = run_pipeline(config)

# View conflict resolutions
for conflict in result.quality_report.conflict_resolutions:
    print(f"Field: {conflict['field']}")
    print(f"Chosen: {conflict['value']} from {conflict['chosen_source']}")
    print(f"Alternatives: {len(conflict['alternatives'])} other values")
```

### 6. Configuration Doctor

Diagnostic tool for validating and fixing configuration issues.

#### Usage

```python
from hotpass import ConfigDoctor, get_default_profile

# Load profile
profile = get_default_profile("aviation")

# Create doctor
doctor = ConfigDoctor(profile=profile)

# Run diagnostics
results = doctor.diagnose()

# Print report
doctor.print_report()

# Auto-fix common issues
if doctor.autofix():
    print("Fixed configuration issues")
    doctor.print_report()
```

#### Command-Line Interface

```bash
# Run diagnostics on a profile
python -c "from hotpass.config_doctor import doctor_command; doctor_command('aviation')"

# Run with auto-fix
python -c "from hotpass.config_doctor import doctor_command; doctor_command('aviation', autofix=True)"
```

## Complete Example

```python
from hotpass import (
    PipelineConfig,
    OutputFormat,
    IndustryProfile,
    run_pipeline,
    ConfigDoctor,
)
from pathlib import Path

# 1. Create custom industry profile
profile = IndustryProfile(
    name="aviation",
    display_name="Aviation Industry",
    email_validation_threshold=0.85,
    phone_validation_threshold=0.85,
    website_validation_threshold=0.75,
    source_priorities={
        "SACAA Cleaned": 3,
        "Reachout Database": 2,
        "Contact Database": 1,
    },
)

# 2. Validate configuration
doctor = ConfigDoctor(profile=profile)
summary = doctor.get_summary()
if summary["health_score"] < 80:
    print("⚠️  Configuration issues detected!")
    doctor.print_report()
    if doctor.autofix():
        print("✓ Auto-fixed issues")

# 3. Configure output formatting
output_format = OutputFormat(
    header_bg_color="366092",
    zebra_striping=True,
    auto_size_columns=True,
)

# 4. Create pipeline configuration
config = PipelineConfig(
    input_dir=Path("data"),
    output_path=Path("output/refined.xlsx"),
    industry_profile=profile,
    output_format=output_format,
    enable_formatting=True,
    enable_audit_trail=True,
    enable_recommendations=True,
)

# 5. Run pipeline
result = run_pipeline(config)

# 6. Review results
print(f"✓ Processed {result.quality_report.total_records} records")
print(f"✓ Quality score: {result.quality_report.data_quality_distribution['mean']:.2f}")

# 7. View recommendations
if result.quality_report.recommendations:
    print("\nRecommendations:")
    for rec in result.quality_report.recommendations:
        print(f"  - {rec}")

# 8. Export quality report
report_path = Path("output/quality_report.md")
report_path.write_text(result.quality_report.to_markdown())
print(f"✓ Quality report saved to {report_path}")
```

## Migration Guide

### From Previous Versions

If you're using the basic pipeline configuration:

**Before:**

```python
from hotpass import PipelineConfig, run_pipeline
from pathlib import Path

config = PipelineConfig(
    input_dir=Path("data"),
    output_path=Path("output/refined.xlsx"),
)

result = run_pipeline(config)
```

**After (with new features):**

```python
from hotpass import PipelineConfig, OutputFormat, run_pipeline
from pathlib import Path

config = PipelineConfig(
    input_dir=Path("data"),
    output_path=Path("output/refined.xlsx"),
    enable_formatting=True,  # NEW: Enable enhanced formatting
    enable_audit_trail=True,  # NEW: Enable audit logging
    enable_recommendations=True,  # NEW: Enable quality recommendations
)

result = run_pipeline(config)

# NEW: Access enhanced quality report
print(result.quality_report.recommendations)
print(result.quality_report.audit_trail)
print(result.quality_report.conflict_resolutions)
```

### Backward Compatibility

All new features are **opt-in** and **backward compatible**:

- Existing code continues to work without changes
- New parameters have sensible defaults
- New quality report fields are always present (as empty lists if disabled)

## Best Practices

### 1. Use Industry Profiles

Always create industry-specific profiles for better data quality:

```python
profile = IndustryProfile(
    name="retail",
    display_name="Retail Stores",
    email_validation_threshold=0.80,
    source_priorities={"POS System": 3, "CRM": 2, "Manual Entry": 1},
)
```

### 2. Enable All Features for Production

```python
config = PipelineConfig(
    input_dir=Path("data"),
    output_path=Path("output/refined.xlsx"),
    industry_profile=profile,
    enable_formatting=True,
    enable_audit_trail=True,
    enable_recommendations=True,
)
```

### 3. Review Recommendations Regularly

```python
result = run_pipeline(config)
critical_recs = [r for r in result.quality_report.recommendations if "CRITICAL" in r]
if critical_recs:
    # Take action on critical recommendations
    send_alert(critical_recs)
```

### 4. Monitor Conflict Resolutions

```python
if len(result.quality_report.conflict_resolutions) > 100:
    print("⚠️  High number of conflicts detected")
    # Review source data quality
```

### 5. Use Configuration Doctor

```python
# Before running pipeline
doctor = ConfigDoctor(profile=profile)
if doctor.get_summary()["health_score"] < 80:
    doctor.autofix()
```

## Troubleshooting

### Low Health Score

If configuration doctor reports low health score:

1. Run with `autofix=True`
2. Review failed checks manually
3. Adjust thresholds based on your data

### No Recommendations

If no recommendations are generated:

1. Check `enable_recommendations=True`
2. Verify data quality is actually good
3. Review expectation thresholds

### Missing Audit Events

If audit trail is incomplete:

1. Check `enable_audit_trail=True`
2. Ensure pipeline completes successfully
3. Check for early exits

## API Reference

See module docstrings for detailed API documentation:

- `hotpass.pipeline.PipelineConfig`
- `hotpass.pipeline.QualityReport`
- `hotpass.formatting.OutputFormat`
- `hotpass.config.IndustryProfile`
- `hotpass.config_doctor.ConfigDoctor`
