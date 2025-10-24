# Hotpass Enhanced Pipeline Usage Guide

## Overview

The Hotpass Enhanced Pipeline integrates multiple advanced features into a single, cohesive data refinement workflow. This guide demonstrates how to use each feature and combine them effectively.

## Installation

### Minimal Installation
```bash
uv sync --extra dev --extra docs
```

### Full Installation (All Features)
```bash
uv sync --extra dev --extra docs --extra orchestration --extra entity_resolution \
  --extra ml_scoring --extra enrichment --extra geospatial --extra compliance \
  --extra dashboards --extra caching
```

## Basic Usage

### Standard Pipeline
```bash
# Run the basic pipeline
hotpass --input-dir ./data --output-path ./output/refined.xlsx

# With archiving
hotpass --archive --dist-dir ./dist
```

### Enhanced Pipeline with All Features
```bash
# Enable all enhancements
hotpass-enhanced orchestrate --profile aviation --enable-all --archive

# Output:
# - Deduplicates records with entity resolution
# - Geocodes addresses
# - Enriches from external sources
# - Detects PII and adds compliance tracking
# - Collects observability metrics
```

## Feature-by-Feature Usage

### 1. Entity Resolution

Deduplicate records using probabilistic matching or rule-based fallback.

```bash
# Standalone entity resolution
hotpass-enhanced resolve \
  --input-file data/with-duplicates.xlsx \
  --output-file data/deduplicated.xlsx \
  --threshold 0.75 \
  --use-splink

# In integrated pipeline
hotpass-enhanced orchestrate \
  --profile aviation \
  --enable-entity-resolution \
  --archive
```

**What it does:**
- Identifies duplicate organizations across sources
- Uses probabilistic matching (Splink) or exact slug matching
- Adds ML-driven priority scores based on completeness
- Preserves best record from each duplicate cluster

**Output columns added:**
- `completeness_score`: Measure of field completeness (0-1)
- `priority_score`: Combined completeness and quality score

### 2. Geospatial Enrichment

Add geographical context to your data.

```bash
# Enable geospatial features
hotpass-enhanced orchestrate \
  --profile aviation \
  --enable-geospatial \
  --archive
```

**What it does:**
- Normalizes address formatting
- Geocodes addresses to latitude/longitude coordinates
- Reverse geocodes coordinates to addresses
- Infers province/region from coordinates
- Calculates distance matrices
- Clusters locations by proximity

**Output columns added:**
- `latitude`: Geocoded latitude
- `longitude`: Geocoded longitude
- `formatted_address`: Standardized address from geocoding
- `geocoded`: Boolean indicating successful geocoding

### 3. External Data Enrichment

Enrich records with data from external sources.

```bash
# Enable enrichment features
hotpass-enhanced orchestrate \
  --profile aviation \
  --enable-enrichment \
  --archive
```

**What it does:**
- Extracts content from organization websites
- Queries external registries (CIPC, SACAA - stubs currently)
- Caches results to avoid repeated API calls
- Enriches with titles, descriptions, and metadata

**Output columns added:**
- `website_title`: Page title from website
- `website_description`: Meta description
- `website_text_length`: Length of extracted text
- `website_enriched`: Boolean indicating success
- `registry_type`: Registry queried
- `registry_status`: Status from registry
- `registry_number`: Registration number if found

**Cache location:** `data/.cache/enrichment.db` (SQLite)

### 4. Compliance & Data Protection

Add POPIA compliance tracking and PII detection.

```bash
# Enable compliance features
hotpass-enhanced orchestrate \
  --profile aviation \
  --enable-compliance \
  --archive
```

**What it does:**
- Adds provenance tracking columns
- Detects PII in contact fields
- Generates compliance reports
- Tracks consent and retention requirements
- Enables data anonymization workflows

**Output columns added:**
- `data_source`: Source system name
- `processed_at`: Processing timestamp
- `consent_status`: Consent tracking (pending/granted/denied)
- `consent_date`: Date consent was obtained
- `retention_until`: Data retention deadline
- `{field}_has_pii`: Boolean PII flag per field
- `{field}_pii_types`: Types of PII detected

**Compliance report includes:**
- Field classifications (PUBLIC, INTERNAL, PII, SENSITIVE_PII)
- PII field identification
- Consent requirements
- Retention policies
- Compliance issues

### 5. Observability & Monitoring

Enable OpenTelemetry instrumentation for metrics and tracing.

```bash
# Enable observability
hotpass-enhanced orchestrate \
  --profile aviation \
  --enable-observability \
  --archive

# Launch monitoring dashboard
hotpass-enhanced dashboard --port 8501
```

**What it collects:**
- **Counters:**
  - Records processed (by source)
  - Validation failures (by rule)
- **Histograms:**
  - Load duration
  - Aggregation duration
  - Validation duration
  - Write duration
- **Gauges:**
  - Current quality score

**Export options:**
- Console (default for testing)
- OTLP (configure for production)
- Prometheus
- Grafana/Loki

## Combining Features

### Recommended Combinations

**Production Data Pipeline:**
```bash
hotpass-enhanced orchestrate \
  --profile aviation \
  --enable-entity-resolution \
  --enable-compliance \
  --enable-observability \
  --archive
```

**Research/Analysis Pipeline:**
```bash
hotpass-enhanced orchestrate \
  --profile aviation \
  --enable-entity-resolution \
  --enable-geospatial \
  --enable-enrichment \
  --archive
```

**All Features (Maximum Enrichment):**
```bash
hotpass-enhanced orchestrate \
  --profile aviation \
  --enable-all \
  --archive
```

## Python API Usage

You can also use the enhanced pipeline programmatically:

```python
from pathlib import Path
from hotpass.config import get_default_profile
from hotpass.data_sources import ExcelReadOptions
from hotpass.pipeline import PipelineConfig
from hotpass.pipeline_enhanced import EnhancedPipelineConfig, run_enhanced_pipeline

# Configure base pipeline
profile = get_default_profile("aviation")
config = PipelineConfig(
    input_dir=Path("./data"),
    output_path=Path("./output/refined.xlsx"),
    industry_profile=profile,
    excel_options=ExcelReadOptions(),
)

# Configure enhanced features
enhanced_config = EnhancedPipelineConfig(
    enable_entity_resolution=True,
    enable_geospatial=True,
    enable_enrichment=True,
    enable_compliance=True,
    enable_observability=True,
    entity_resolution_threshold=0.75,
    use_splink=False,  # Use fallback matching
    geocode_addresses=True,
    enrich_websites=True,
    detect_pii=True,
    cache_path="data/.cache/enrichment.db",
)

# Run enhanced pipeline
result = run_enhanced_pipeline(config, enhanced_config)

# Access results
print(f"Processed {len(result.refined)} organizations")
print(f"Quality score: {result.quality_report.data_quality_distribution['mean']:.2%}")

# Save results
result.refined.to_excel(config.output_path, index=False)
```

## Performance Considerations

### Feature Impact on Runtime

| Feature | Overhead | Recommendation |
|---------|----------|----------------|
| Entity Resolution (fallback) | Low (~5%) | Always enable for production |
| Entity Resolution (Splink) | Medium (~20%) | Enable for datasets > 1000 records |
| Geospatial (geocoding) | High (~100-200%) | Enable selectively; use cache |
| Enrichment (web scraping) | Very High (~300-500%) | Enable for small batches; use cache |
| Compliance (PII detection) | Medium (~30%) | Enable for sensitive data |
| Observability | Low (~2-3%) | Always enable for monitoring |

### Optimization Tips

1. **Use Caching**: Enrichment and geospatial features cache results
2. **Batch Processing**: Process large datasets in chunks
3. **Selective Enrichment**: Only enable features you need
4. **Async Orchestration**: Use Prefect for scheduled/distributed runs

## Troubleshooting

### Missing Dependencies
```bash
# If you get import errors
uv sync --extra <feature_name>

# Examples:
uv sync --extra geospatial  # For geocoding
uv sync --extra enrichment  # For web scraping
uv sync --extra compliance  # For PII detection
```

### Geocoding Timeouts
Geocoding can be slow. Adjust timeout in code or skip failed addresses:
```python
from hotpass.geospatial import Geocoder

# Increase timeout
geocoder = Geocoder(timeout=30)  # Default is 10 seconds
```

### Cache Management
```python
from hotpass.enrichment import CacheManager

cache = CacheManager()

# View cache stats
stats = cache.stats()
print(f"Cache has {stats['total_entries']} entries")

# Clear expired entries
removed = cache.clear_expired()
print(f"Removed {removed} expired entries")
```

## Next Steps

- **Custom Profiles**: Create industry-specific profiles in `src/hotpass/profiles/`
- **Advanced Validation**: Add custom Great Expectations rules
- **Production Deployment**: Set up Prefect Cloud for orchestration
- **Monitoring**: Configure Grafana dashboards for observability metrics

## Support

- Documentation: `/docs/` directory
- Issues: GitHub Issues
- Questions: GitHub Discussions
