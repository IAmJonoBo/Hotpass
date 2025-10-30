# Agent Instructions for Hotpass

**Version:** 1.0
**Audience:** GitHub Copilot, Codex, and other AI coding assistants
**Last Updated:** 2025-10-30

## Overview

Hotpass is a data refinement platform that transforms messy spreadsheets into a governed single source of truth. This document provides AI agents with comprehensive instructions for operating Hotpass through CLI and MCP interfaces.

## Core Principles

1. **Profile-First**: Always specify a profile (`aviation`, `generic`, or custom) to ensure correct data semantics
2. **Deterministic-First**: Prefer offline/deterministic enrichment before network-based lookups
3. **Provenance Tracking**: Maintain full audit trails of data sources and transformations
4. **Safe by Default**: Network operations disabled by default; require explicit enablement

## Available Interfaces

### CLI Interface

All operations are accessible via `uv run hotpass <command>`. Primary commands:

- `overview` - Display available commands and quick start
- `refine` - Run refinement pipeline (clean, normalize, deduplicate)
- `enrich` - Add additional data (deterministic and optional network)
- `qa` - Run quality assurance checks
- `contracts` - Generate data contracts and schemas

### MCP Interface

Hotpass exposes an MCP (Model Context Protocol) server that provides the same operations as callable tools:

- `hotpass.refine`
- `hotpass.enrich`
- `hotpass.qa`
- `hotpass.explain_provenance`
- `hotpass.crawl` (guarded)

Start the MCP server: `python -m hotpass.mcp.server`

## End-to-End Workflows

### Workflow 1: Refine a Spreadsheet

**Goal**: Convert messy input data into a clean, validated, single source of truth.

**Steps**:

1. **Discover input data**:
   ```bash
   ls ./data/*.xlsx
   ```

2. **Choose appropriate profile**:
   - Aviation industry: `--profile aviation`
   - Generic business: `--profile generic`
   - Custom profile: `--profile <your-profile> --profile-search-path ./profiles`

3. **Run refinement**:
   ```bash
   uv run hotpass refine \
     --input-dir ./data \
     --output-path ./dist/refined.xlsx \
     --profile aviation \
     --archive
   ```

4. **Verify output**:
   - Check `./dist/refined.xlsx` exists
   - Review quality report (JSON/HTML) in `./dist/`
   - Check archived inputs if `--archive` was used

**MCP Equivalent**:
```javascript
hotpass.refine({
  input_path: "./data",
  output_path: "./dist/refined.xlsx",
  profile: "aviation",
  archive: true
})
```

**Expected Outputs**:
- Refined Excel file with normalized columns
- Quality report with validation results
- Provenance metadata for each row
- Optional archive of original inputs

### Workflow 2: Enrich Refined Data

**Goal**: Add missing information using deterministic (offline) sources first, then optionally network sources.

**Steps**:

1. **Ensure refined data exists** (run Workflow 1 first if needed)

2. **Run deterministic enrichment** (safe, always works offline):
   ```bash
   uv run hotpass enrich \
     --input ./dist/refined.xlsx \
     --output ./dist/enriched.xlsx \
     --profile aviation \
     --allow-network=false
   ```

3. **Review enrichment results**:
   - Check confidence scores in provenance columns
   - Identify rows with low confidence
   - Review which fields were enriched

4. **If needed, enable network enrichment** (requires env vars):
   ```bash
   export FEATURE_ENABLE_REMOTE_RESEARCH=1
   export ALLOW_NETWORK_RESEARCH=1

   uv run hotpass enrich \
     --input ./dist/refined.xlsx \
     --output ./dist/enriched-network.xlsx \
     --profile aviation \
     --allow-network=true
   ```

**MCP Equivalent**:
```javascript
// Deterministic only (default)
hotpass.enrich({
  input_path: "./dist/refined.xlsx",
  output_path: "./dist/enriched.xlsx",
  profile: "aviation",
  allow_network: false
})

// With network (if env permits)
hotpass.enrich({
  input_path: "./dist/refined.xlsx",
  output_path: "./dist/enriched-network.xlsx",
  profile: "aviation",
  allow_network: true
})
```

**Expected Outputs**:
- Enriched Excel file with additional columns filled
- Provenance columns showing data sources:
  - `provenance_source` - Which fetcher provided the data
  - `provenance_timestamp` - When data was fetched
  - `provenance_confidence` - Confidence score (0.0-1.0)
  - `provenance_strategy` - Strategy used (deterministic/research/backfill)
  - `provenance_network_status` - Whether network was used

### Workflow 3: Run Quality Checks

**Goal**: Verify data quality, profile compliance, and system health.

**Steps**:

1. **Run all checks**:
   ```bash
   uv run hotpass qa all
   ```

2. **Run specific check types**:
   ```bash
   # Just fitness functions
   uv run hotpass qa fitness

   # Just profile validation
   uv run hotpass qa profiles

   # Just documentation checks
   uv run hotpass qa docs

   # Technical acceptance criteria
   uv run hotpass qa ta
   ```

**MCP Equivalent**:
```javascript
hotpass.qa({
  target: "all"  // or "fitness", "profiles", "docs", "ta"
})
```

**Expected Outputs**:
- Pass/fail status for each check
- Detailed error messages for failures
- Suggestions for remediation

### Workflow 4: Generate Data Contracts

**Goal**: Export schemas and contracts for API consumers and data quality tools.

**Steps**:

1. **Emit contract for a profile**:
   ```bash
   uv run hotpass contracts emit \
     --profile aviation \
     --format yaml \
     --output ./contracts/aviation.yaml
   ```

2. **Include examples** (optional):
   ```bash
   uv run hotpass contracts emit \
     --profile aviation \
     --format json \
     --include-examples \
     --output ./contracts/aviation.json
   ```

**Expected Outputs**:
- Schema definitions for all fields
- Validation thresholds
- Column mappings/synonyms
- Example records (if requested)

### Workflow 5: Explain Provenance

**Goal**: Understand where a specific data point came from.

**MCP Tool** (not yet CLI command):
```javascript
hotpass.explain_provenance({
  row_id: "org-12345",
  dataset_path: "./dist/enriched.xlsx"
})
```

**Expected Output**:
- Source of each field in the row
- Timestamps of data fetch
- Confidence scores
- Strategy used (deterministic/research/manual)

## Environment Configuration

### Required Environment Variables

**For Network Enrichment**:
```bash
# Enable network-based enrichment feature
export FEATURE_ENABLE_REMOTE_RESEARCH=1

# Allow network calls at runtime
export ALLOW_NETWORK_RESEARCH=1
```

**For API Keys** (if using external enrichment services):
```bash
export HOTPASS_GEOCODE_API_KEY=<your-key>
export HOTPASS_ENRICH_API_KEY=<your-key>
```

### Network Behavior Matrix

| `FEATURE_ENABLE_REMOTE_RESEARCH` | `ALLOW_NETWORK_RESEARCH` | `--allow-network` | Result |
|----------------------------------|--------------------------|-------------------|--------|
| 0 or unset | * | * | Deterministic only |
| 1 | 0 or unset | * | Deterministic only |
| 1 | 1 | false | Deterministic only |
| 1 | 1 | true | Network enabled |

**Key Insight**: Network enrichment requires ALL THREE to be enabled for safety.

## Profile Selection Guide

### When to Use `aviation` Profile
- Flight schools
- Aviation training providers
- Airport services
- Aircraft maintenance companies

**Key Features**:
- Province/region normalization (South African focus)
- SACAA (regulator) source prioritization
- Training category mappings
- Flight-specific synonyms

### When to Use `generic` Profile
- General businesses
- Any organization type
- Unknown/mixed industries
- Quick testing

**Key Features**:
- Universal column mappings
- Standard validation thresholds
- No industry-specific logic

### Creating Custom Profiles

If you need a custom profile:

1. Create YAML file in `src/hotpass/profiles/<your-profile>.yaml`
2. Include all 4 required blocks (see Profile Schema below)
3. Use via `--profile <your-profile>`

## Profile Schema (Complete)

As of Sprint 3, all profiles must declare these 4 blocks:

```yaml
name: example
display_name: Example Industry

# Block 1: Ingest
ingest:
  sources:
    - name: Source Name
      format: xlsx
      priority: 3
  chunk_size: 5000
  staging_enabled: true

# Block 2: Refine
refine:
  mappings:
    organization_name:
      - company_name
      - business_name
  deduplication:
    strategy: entity_resolution
    threshold: 0.85
  normalization:
    phone_format: E164
    country_code: ZA
  expectations:
    - expect_column_values_to_not_be_null: [organization_name]

# Block 3: Enrich
enrich:
  allow_network: false  # default
  fetcher_chain:
    - deterministic
    - lookup_tables
    - research  # only if network enabled
  backfillable_fields:
    - contact_email
    - website
  confidence_threshold: 0.7

# Block 4: Compliance
compliance:
  policy: POPIA
  consent_required: true
  pii_fields:
    - contact_email
    - contact_phone
  retention_days: 365
```

## Troubleshooting

### Issue: "Profile not found"
**Solution**: Check profile name spelling, or use `--profile-search-path` to add custom directory.

### Issue: "Network calls blocked"
**Solution**: Check environment variables (`FEATURE_ENABLE_REMOTE_RESEARCH`, `ALLOW_NETWORK_RESEARCH`) and `--allow-network` flag.

### Issue: "Enrichment failed"
**Solution**:
1. Try deterministic only first: `--allow-network=false`
2. Check input file format (must be XLSX)
3. Verify profile is complete with all 4 blocks

### Issue: "Quality gate failed"
**Solution**:
1. Run `uv run hotpass qa all` to see specific failures
2. Check fitness functions: `uv run python scripts/quality/fitness_functions.py`
3. Verify documentation exists (`.github/copilot-instructions.md`, `AGENTS.md`)

## Quality Gates Reference

### QG-1: CLI Integrity
**Test**: `uv run hotpass overview`
**Passes if**: Lists all required verbs (refine, enrich, qa, contracts, overview)

### QG-2: Data Quality
**Test**: Great Expectations suite
**Passes if**: All profile expectations pass

### QG-3: Enrichment Chain
**Test**: `uv run hotpass enrich --input <file> --output <out> --allow-network=false`
**Passes if**: Output exists, provenance written, network skipped

### QG-4: MCP Discoverability
**Test**: MCP tools/list request
**Passes if**: All 5 tools appear (refine, enrich, qa, explain_provenance, crawl)

### QG-5: Docs/Instructions
**Test**: File existence and content checks
**Passes if**: `.github/copilot-instructions.md` and `AGENTS.md` exist with required terms

## Security Considerations

1. **Never commit API keys**: Use environment variables
2. **Network guard**: Always verify network permissions before enrichment
3. **PII handling**: Follow POPIA compliance in profile
4. **Provenance audit**: Log all data sources for compliance
5. **MCP safety**: MCP server requires explicit user approval for file/network operations (per Copilot CLI defaults)

## Best Practices

1. **Always specify `--profile`**: Don't rely on defaults
2. **Run `qa` before production**: Catch issues early
3. **Archive inputs**: Use `--archive` flag for audit trail
4. **Check provenance**: Review confidence scores before trusting enriched data
5. **Deterministic first**: Only enable network when offline sources insufficient
6. **Document custom profiles**: Add comments explaining business logic

## Examples

### Complete Refinement Pipeline
```bash
# 1. Refine raw data
uv run hotpass refine \
  --input-dir ./data \
  --output-path ./dist/refined.xlsx \
  --profile aviation \
  --archive

# 2. Enrich with deterministic sources
uv run hotpass enrich \
  --input ./dist/refined.xlsx \
  --output ./dist/enriched.xlsx \
  --profile aviation \
  --allow-network=false

# 3. Run quality checks
uv run hotpass qa all

# 4. Generate contract
uv run hotpass contracts emit \
  --profile aviation \
  --output ./contracts/aviation.yaml
```

### MCP-Driven Pipeline
```javascript
// Step 1: Refine
const refineResult = await callTool("hotpass.refine", {
  input_path: "./data",
  output_path: "./dist/refined.xlsx",
  profile: "aviation",
  archive: true
});

// Step 2: Enrich (deterministic only)
const enrichResult = await callTool("hotpass.enrich", {
  input_path: "./dist/refined.xlsx",
  output_path: "./dist/enriched.xlsx",
  profile: "aviation",
  allow_network: false
});

// Step 3: QA
const qaResult = await callTool("hotpass.qa", {
  target: "all"
});

// Step 4: Explain a specific row
const provenance = await callTool("hotpass.explain_provenance", {
  row_id: "org-12345",
  dataset_path: "./dist/enriched.xlsx"
});
```

## Integration with GitHub Agent HQ

When working in GitHub Agent HQ or Copilot CLI:

1. **Discovery**: Run `hotpass overview` first to see available operations
2. **Context**: Always mention the profile you're using
3. **Safety**: Confirm network operations with user before enabling
4. **Feedback**: Show quality check results to user
5. **Provenance**: Explain data sources when presenting results

## References

- **UPGRADE.md**: Full specification of CLI/MCP parity requirements
- **IMPLEMENTATION_PLAN.md**: Detailed implementation plan with quality gates
- **README.md**: Project overview and installation
- **docs/how-to-guides/configure-pipeline.md**: Profile customization guide
- **docs/how-to-guides/agentic-orchestration.md**: Prefect orchestration guide

## Support

For issues or questions:
1. Run `uv run hotpass doctor` for diagnostics
2. Check `docs/` directory for detailed guides
3. Review quality gate tests in `tests/cli/test_quality_gates.py`
4. Consult fitness functions in `scripts/quality/fitness_functions.py`

---

*This document is maintained as part of the Hotpass UPGRADE.md implementation.*
