---
title: How-to — format outputs and enforce validation rules
summary: Apply professional Excel styling and tune validation thresholds for your sector.
last_updated: 2025-10-25
---

# How-to — format outputs and enforce validation rules

Follow this guide when stakeholders expect polished deliverables and tailored quality gates.

## Enable premium formatting

```python
from pathlib import Path
from hotpass import PipelineConfig, OutputFormat, run_pipeline

formatting = OutputFormat(
    header_bg_color="366092",
    header_font_color="FFFFFF",
    zebra_striping=True,
    auto_size_columns=True,
    freeze_header_row=True,
    add_filters=True,
)

config = PipelineConfig(
    input_dir=Path("data"),
    output_path=Path("dist/refined.xlsx"),
    enable_formatting=True,
    output_format=formatting,
)
run_pipeline(config)
```

Key options:

- `header_bg_color` and `header_font_color` use hex RGB strings.
- `zebra_striping` alternates row colours for better readability.
- `add_filters` adds Excel auto-filters to every column.

## Customise validation thresholds

Profiles define default validation requirements. Override them for specific deployments:

```yaml
validation:
  email_validity: 0.9
  phone_validity: 0.85
  website_validity: 0.75
  duplicate_threshold: 0.1
```

Lower thresholds make the pipeline more permissive for exploratory analysis. Higher thresholds (≥0.95) are recommended for production datasets.

## Monitor validation feedback

After each run, inspect the generated quality report:

```python
from hotpass.quality import load_quality_report

report = load_quality_report(Path("dist/quality-report.json"))
print(report.summary())
```

Combine the structured report with the Markdown export to share remediation tasks with stakeholders.

## Troubleshooting

- **Excel formatting not applied**: Ensure `enable_formatting=True` and install the `dashboards` extra for the required libraries.
- **Unexpected validation failures**: Check whether the incoming workbook uses the latest field mapping and review the field dictionary in the [data model reference](../reference/data-model.md).
- **Large Excel files**: Disable conditional formatting for columns with more than 50,000 rows to speed up exports.
