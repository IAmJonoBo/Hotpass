# Hotpass UPGRADE.md Implementation Plan

**Version:** 1.0
**Date:** 2025-10-30
**Status:** In Progress
**Owner:** Development Team

## Executive Summary

This document details the implementation plan for upgrading Hotpass to support full CLI/MCP parity, enrichment pipelines, unified profiles, and comprehensive quality gates as specified in `UPGRADE.md`. The plan follows frontier-spec quality standards with explicit Technical Acceptance (TA) criteria and quality gates (QG) for each sprint.

## Goals

1. **CLI & MCP Parity**: Expose all Hotpass operations through both `uv run hotpass ...` CLI and equivalent MCP tools
2. **Enrichment Pipeline**: Implement deterministic-first, network-optional enrichment with provenance tracking
3. **Profile Unification**: Ensure all profiles declare complete `ingest`, `refine`, `enrich`, and `compliance` blocks
4. **Quality Gates**: Wire automated QG-1 through QG-5 checks into CI/CD
5. **Documentation Parity**: Update all docs to reflect new architecture without regressions

## Architecture Alignment

### Current State
- ✅ CLI surface now aligned with UPGRADE.md (`overview`, `refine`, `enrich`, `qa`, `contracts`) with legacy commands maintained where needed.
- ✅ MCP stdio server (`src/hotpass/mcp/server.py`) exposes the required toolset, including `hotpass.crawl` backed by the adaptive orchestrator.
- ✅ Enrichment + research orchestration deliver deterministic-first enrichment, provenance, and throttled crawl artefacts.
- ✅ Quality gates QG‑1 → QG‑5 run locally and in CI via `scripts/quality/run_qg*.py` and the `quality-gates` workflow.
- ⚠️ Advanced profile/linkage coverage and TA integration analytics remain in progress (integration tests + QG surfacing still required).
- ⚠️ Docs/navigation uplift and research-first positioning still pending sign-off.

### Target State
- ✅ CLI commands: `overview`, `refine`, `enrich`, `qa`, `contracts` (aliased to existing)
- ✅ MCP server at `src/hotpass/mcp/server.py` with 5 core tools
- ✅ Enrichment with deterministic/research split and network guards
- ✅ Complete profile schema with all 4 blocks
- ✅ Quality gates QG-1 through QG-5 automated in CI
- ✅ Documentation complete and aligned

---

## Sprint Breakdown

### Sprint 1: CLI & MCP Parity

**Objective:** Enable full Hotpass operation through CLI and MCP tools

#### Implementation Tasks

1. **Create new CLI commands** (`src/hotpass/cli/commands/`)
   - `overview.py` - Display available commands and system status
   - `refine.py` - Wrapper/alias for existing `run.py`
   - `enrich.py` - New enrichment command
   - `qa.py` - Quality assurance and validation
   - `contracts.py` - Contract emission command

2. **Create MCP server** (`src/hotpass/mcp/`)
   - `server.py` - MCP stdio server implementation
   - `tools.py` - Tool definitions and handlers
   - `__init__.py` - Module exports

3. **MCP Tools Implementation**
   - `hotpass.refine` - Runs refinement pipeline
   - `hotpass.enrich` - Runs enrichment with network control
   - `hotpass.qa` - Executes quality checks
   - `hotpass.crawl` - Optional, guarded crawler access
   - `hotpass.explain_provenance` - Provenance lookup

4. **Update Documentation**
   - Add MCP tools section to `.github/copilot-instructions.md`
   - Add MCP discovery instructions to `AGENTS.md`
   - Create `docs/reference/mcp-tools.md`

#### Quality Gate: QG-1 (CLI Integrity)

**Test:** `uv run hotpass overview`
**Pass Criteria:**
- Exit code 0
- Output lists: `refine`, `enrich`, `qa`, `contracts`, `overview`
- Each command has `--help` that works

**Implementation:**
```python
# tests/cli/test_quality_gates.py
def test_qg1_cli_integrity(tmp_path):
    """QG-1: CLI exposes all required verbs."""
    result = subprocess.run(
        ["uv", "run", "hotpass", "overview"],
        capture_output=True,
        text=True
    )
    expect(result.returncode == 0, "overview command should exit successfully")

    required_verbs = ["refine", "enrich", "qa", "contracts", "overview"]
    for verb in required_verbs:
        expect(verb in result.stdout, f"overview must list {verb}")
```

#### Technical Acceptance (TA) Criteria

- ✅ All CLI verbs callable via `uv run hotpass <verb> --help`
- ✅ MCP server starts with `python -m hotpass.mcp.server`
- ✅ MCP tools discoverable via stdio protocol
- ✅ Documentation mentions all verbs and tools
- ✅ QG-1 test passes in CI

**Dependencies:** None
**Blockers:** None
**Estimated Effort:** 2-3 days

---

### Sprint 2: Enrichment Translation

**Objective:** Implement offline-first, network-optional enrichment with provenance

#### Implementation Tasks

1. **Create enrichment structure** (`src/hotpass/enrichment/`)
   - `fetchers/__init__.py` - Fetcher registry
   - `fetchers/deterministic.py` - Local/offline enrichment
   - `fetchers/research.py` - Network-based enrichment
   - `pipeline.py` - Enrichment orchestration
   - `provenance.py` - Provenance tracking and reporting

2. **Deterministic Fetchers** (`fetchers/deterministic.py`)
   - Lookup table enrichment
   - Historical data backfill
   - Derived field calculation
   - Local registry queries

3. **Research Fetchers** (`fetchers/research.py`)
   - Network guard decorator (`@requires_network`)
   - Hotpass research service integration
   - Domain-specific crawlers
   - Rate limiting and retry logic

4. **Environment Controls**
   - `FEATURE_ENABLE_REMOTE_RESEARCH` - Master toggle
   - `ALLOW_NETWORK_RESEARCH` - Runtime toggle
   - Default: network disabled (safe by default)

5. **Provenance Tracking**
   - Source attribution
   - Timestamp and confidence
   - Strategy metadata (deterministic/research/backfill)
   - Audit trail for compliance

6. **CLI Integration**
   - Add `enrich` command to CLI
   - `--allow-network` flag (defaults to env var)
   - `--profile` support
   - Progress reporting

#### Quality Gate: QG-3 (Enrichment Chain)

**Test:**
```bash
uv run hotpass enrich \
  --input ./tests/data/minimal.xlsx \
  --output /tmp/enriched.xlsx \
  --profile test \
  --allow-network=false
```

**Pass Criteria:**
1. Output file exists at `/tmp/enriched.xlsx`
2. Provenance columns present in output
3. No network calls made (verify via network mock)
4. Exit code 0

**Implementation:**
```python
# tests/enrichment/test_quality_gates.py
def test_qg3_enrichment_chain_gate(tmp_path, minimal_xlsx, monkeypatch):
    """QG-3: Enrichment chain works offline with provenance."""
    # Mock network to fail if called
    monkeypatch.setenv("ALLOW_NETWORK_RESEARCH", "false")

    output = tmp_path / "enriched.xlsx"
    result = subprocess.run([
        "uv", "run", "hotpass", "enrich",
        "--input", str(minimal_xlsx),
        "--output", str(output),
        "--profile", "test",
        "--allow-network=false"
    ], capture_output=True)

    expect(result.returncode == 0, "enrich should succeed offline")
    expect(output.exists(), "output file must exist")

    # Verify provenance
    df = pd.read_excel(output)
    expect("provenance_source" in df.columns, "must have provenance columns")
    expect("provenance_timestamp" in df.columns, "must track timestamps")
```

#### Technical Acceptance (TA) Criteria

- ✅ `hotpass enrich` command works with `--allow-network=false`
- ✅ Deterministic enrichment produces valid output
- ✅ Network calls blocked when env vars disable them
- ✅ Provenance metadata written to all enriched rows
- ✅ QG-3 test passes in CI

**Dependencies:** Sprint 1 (CLI foundation)
**Blockers:** None
**Estimated Effort:** 3-4 days

---

### Sprint 3: Profiles & Compliance Unification

**Objective:** Complete profile schema with all required blocks

#### Implementation Tasks

1. **Update Profile Schema**
   - Define complete YAML structure with 4 blocks
   - Add validation for required sections
   - Create migration guide for existing profiles

2. **Profile Blocks**

   **a) `ingest` block:**
   ```yaml
   ingest:
     sources:
       - name: SACAA Cleaned
         format: xlsx
         priority: 3
     chunk_size: 5000
     staging_enabled: true
   ```

   **b) `refine` block:**
   ```yaml
   refine:
     mappings:
       organization_name: [school_name, company_name]
     deduplication:
       strategy: entity_resolution
       threshold: 0.85
     expectations:
       - expect_column_values_to_not_be_null: [organization_name]
   ```

   **c) `enrich` block:**
   ```yaml
   enrich:
     allow_network: false
     fetcher_chain:
       - deterministic
       - lookup_tables
       - research  # only if network enabled
     backfillable_fields:
       - contact_email
       - website
   ```

   **d) `compliance` block:**
   ```yaml
   compliance:
     policy: POPIA
     consent_required: true
     pii_fields:
       - contact_email
       - contact_phone
     retention_days: 365
   ```

3. **Profile Linter** (`tools/profile_lint.py`)
   - Validate YAML syntax
   - Check all 4 blocks present
   - Verify field references
   - Type checking for configurations
   - CLI integration: `hotpass qa profiles`

4. **Update Existing Profiles**
   - Migrate `aviation.yaml` to new schema
   - Migrate `generic.yaml` to new schema
   - Add `test.yaml` profile for QA

5. **Great Expectations Integration**
   - Wire profile expectations into GE suite
   - Generate data docs on failure
   - Link to QG-2 quality gate

#### Quality Gate: QG-2 (Data Quality)

**Test:** Run Great Expectations suite against sample data

**Pass Criteria:**
- All expectations defined in profile pass
- GE data docs generated on failure
- Pipeline stops on validation failure

**Implementation:**
```python
# tests/profiles/test_quality_gates.py
def test_qg2_data_quality_gate(tmp_path, sample_data):
    """QG-2: Great Expectations catches quality issues."""
    profile = load_industry_profile("test")

    # Run GE validation
    context = ge.get_context()
    suite = context.create_expectation_suite("test_suite")

    # Add expectations from profile
    for expectation in profile.refine.expectations:
        suite.add_expectation(expectation)

    validator = context.get_validator(
        batch_request=...,
        expectation_suite_name="test_suite"
    )

    results = validator.validate()
    expect(results.success, "all expectations should pass for valid data")
```

#### Technical Acceptance (TA) Criteria

- ✅ All profiles contain 4 blocks: ingest, refine, enrich, compliance
- ✅ `tools/profile_lint.py` validates profile completeness
- ✅ `hotpass qa profiles` runs linter
- ✅ GE expectations from profiles execute in pipeline
- ✅ QG-2 test passes in CI

**Dependencies:** Sprint 2 (enrich block needs enrichment pipeline)
**Blockers:** None
**Estimated Effort:** 3-4 days

---

### Sprint 4: Docs & Agent UX

**Objective:** First-class agent instructions and E2E flow documentation

#### Implementation Tasks

1. **Create Agent Instructions** (`docs/agent-instructions.md`)
   - Flow 1: "Refine the spreadsheet"
   - Flow 2: "Double-check this entry"
   - Flow 3: "Run quality gates"
   - Tool discovery guide
   - Common patterns and examples

2. **Update Copilot Instructions** (`.github/copilot-instructions.md`)
   - Add "Profile-first" guidance
   - Add "Deterministic-first" preference
   - Add "Provenance tracking" requirements
   - Link to agent-instructions.md

3. **Update AGENTS.md**
   - Add MCP tool descriptions
   - Add example invocations
   - Add troubleshooting section

4. **Create Reference Docs**
   - `docs/reference/cli-commands.md` - All CLI verbs
   - `docs/reference/mcp-tools.md` - All MCP tools
   - `docs/reference/quality-gates.md` - QG-1 through QG-5
   - `docs/reference/profiles.md` - Complete schema

5. **Update Existing Docs**
   - Review all how-to guides for accuracy
   - Update architecture docs with new components
   - Add migration guides where needed

#### Quality Gate: QG-5 (Docs/Instruction Gate)

**Test:** Verify required docs exist with required content

**Pass Criteria:**
- `.github/copilot-instructions.md` exists
- `AGENTS.md` exists
- Both mention: "profile-first", "deterministic-first", "provenance"
- Both are non-empty (>100 bytes)

**Implementation:**
```python
# tests/docs/test_quality_gates.py
def test_qg5_docs_instruction_gate():
    """QG-5: Agent instruction files present and complete."""
    copilot_instructions = Path(".github/copilot-instructions.md")
    agents_md = Path("AGENTS.md")

    expect(copilot_instructions.exists(), "copilot-instructions.md must exist")
    expect(agents_md.exists(), "AGENTS.md must exist")

    copilot_text = copilot_instructions.read_text()
    agents_text = agents_md.read_text()

    required_terms = ["profile-first", "deterministic-first", "provenance"]
    for term in required_terms:
        expect(term in copilot_text.lower(),
               f"copilot-instructions must mention {term}")
        expect(term in agents_text.lower(),
               f"AGENTS.md must mention {term}")

    expect(len(copilot_text) > 100, "copilot-instructions not empty")
    expect(len(agents_text) > 100, "AGENTS.md not empty")
```

#### Technical Acceptance (TA) Criteria

- ✅ `docs/agent-instructions.md` contains E2E flows
- ✅ `.github/copilot-instructions.md` updated with new guidance
- ✅ `AGENTS.md` references MCP tools
- ✅ All reference docs created and accurate
- ✅ QG-5 test passes in CI

**Dependencies:** Sprint 1, 2, 3 (documents their outputs)
**Blockers:** None
**Estimated Effort:** 2-3 days

---

### Sprint 5: TA Closure

**Objective:** Wire all quality gates into CI and create TA checking tool

#### Implementation Tasks

1. **CI Automation** (`.github/workflows/quality-gates.yml`)
   - Job 1: QG-1 (CLI integrity)
   - Job 2: QG-2 (Data quality)
   - Job 3: QG-3 (Enrichment chain)
   - Job 4: QG-4 (MCP discoverability)
   - Job 5: QG-5 (Docs/instructions)
   - Matrix testing across profiles

2. **Meta-MCP Tool** (`src/hotpass/mcp/tools/ta_check.py`)
   - `hotpass.ta.check` - Runs all QG checks
   - Returns structured results
   - CLI integration: `hotpass qa ta`

3. **Quality Gate Scripts** (`scripts/quality/`)
   - `run_qg1.py` - CLI integrity check
   - `run_qg2.py` - GE validation
   - `run_qg3.py` - Enrichment test
   - `run_qg4.py` - MCP discovery
   - `run_qg5.py` - Docs verification
   - `run_all_gates.py` - Master runner

4. **MCP Discoverability Test**
   ```python
   # tests/mcp/test_quality_gates.py
   def test_qg4_mcp_discoverability():
       """QG-4: MCP tools are discoverable."""
       # Start MCP server
       server = subprocess.Popen([...])

       # Query tool list
       tools = query_mcp_tools()

       required_tools = [
           "hotpass.refine",
           "hotpass.enrich",
           "hotpass.qa"
       ]

       for tool in required_tools:
           expect(tool in tools, f"MCP must expose {tool}")
   ```

5. **TA Summary Report**
   - Persist JSON summary to `dist/quality-gates/latest-ta.json`
   - Append NDJSON history entries for longitudinal tracking
   - Expose artefact paths via CLI/MCP output for downstream analytics (markdown export remains optional)
   - Provide `scripts/quality/ta_history_report.py` to surface pass-rate analytics (covered by `tests/cli/test_ta_history_report.py`)

#### Quality Gate: QG-4 (MCP Discoverability)

**Test:** MCP tools are discoverable via protocol

**Pass Criteria:**
- MCP server starts successfully
- Tool list includes: `hotpass.refine`, `hotpass.enrich`, `hotpass.qa`
- Tools respond to invocation

**Implementation:** See QG-4 test above

#### Technical Acceptance (TA) Criteria

- ✅ CI runs QG-1 through QG-5 automatically
- ✅ `hotpass.ta.check` MCP tool works
- ✅ `hotpass qa ta` CLI command works
- ✅ All QG scripts in `scripts/quality/`
- ✅ TA summary report generated
- ✅ QG-4 test passes in CI

**Dependencies:** Sprints 1-4 (integrates all prior work)
**Blockers:** None
**Estimated Effort:** 2-3 days

---

## Technical Acceptance Summary

### TA-1: Single-Tool Rule
All operations accessible via `uv run hotpass ...` or equivalent MCP tools.

**Verification:**
- [ ] Every MCP tool has CLI equivalent
- [ ] No operations require secondary repos/tools

### TA-2: Profile Completeness
Every profile declares all 4 blocks (ingest, refine, enrich, compliance).

**Verification:**
- [ ] `tools/profile_lint.py` validates schemas
- [ ] All existing profiles migrated
- [ ] Test profile covers edge cases

### TA-3: Offline-First
Enrichment succeeds with `--allow-network=false` and valid provenance.

**Verification:**
- [ ] QG-3 passes
- [ ] No network calls when disabled
- [ ] Provenance tracks "offline" strategy

### TA-4: Network-Safe
Network disabled by env vars prevents remote calls with provenance note.

**Verification:**
- [ ] Tests mock network and verify no calls
- [ ] Provenance shows "skipped: network disabled"

### TA-5: MCP Parity
Every CLI verb exposed as MCP tool, discoverable via `/mcp list`.

**Verification:**
- [ ] QG-4 passes
- [ ] All tools respond correctly
- [ ] Tool schemas match CLI signatures

### TA-6: Quality Gates Wired
QG-1 through QG-5 exist as runnable scripts/tests.

**Verification:**
- [ ] All QG tests in CI
- [ ] Scripts in `scripts/quality/`
- [ ] `hotpass qa ta` runs all gates

### TA-7: Docs Present
Agent instructions complete with required terminology.

**Verification:**
- [ ] QG-5 passes
- [ ] E2E flows documented
- [ ] Migration guides provided

---

## Risk Assessment

### High Risk
- **MCP Protocol Stability**: MCP spec may evolve; isolate protocol handling
- **Network Guard Bypass**: Critical for security; extensive testing required
- **Profile Migration**: Breaking changes for users; provide migration tool

**Mitigation:**
- Version-pin MCP dependencies
- Use network mocking in all enrichment tests
- Create automated profile migration script
- Document breaking changes prominently

### Medium Risk
- **GE Integration**: Complex validation logic may have edge cases
- **CLI Backwards Compat**: Existing scripts may break
- **CI Pipeline Load**: More gates = longer CI times

**Mitigation:**
- Extensive GE test coverage
- Maintain aliases for old CLI commands
- Parallelize CI jobs, cache dependencies

### Low Risk
- **Documentation Drift**: Docs may fall out of sync
- **TA Check Performance**: Running all gates may be slow

**Mitigation:**
- Make docs updates part of PR checklist
- Optimize TA check, allow selective runs

---

## Success Metrics

### Functional Metrics
- [ ] 100% of CLI verbs have MCP equivalents
- [ ] 100% of profiles pass linter
- [ ] 100% of quality gates pass in CI
- [ ] 0 network calls when network disabled

### Quality Metrics
- [ ] Test coverage ≥ 90% for new code
- [ ] All fitness functions pass
- [ ] 0 Bandit/Ruff/mypy violations
- [ ] Documentation completeness score ≥ 95%

### Operational Metrics
- [ ] CI pipeline time < 15 minutes
- [ ] TA check runtime < 5 minutes
- [ ] Profile linter runtime < 10 seconds

---

## Implementation Phases

### Phase 1: Foundation (Sprints 1-2)
**Duration:** 1 week
**Deliverables:** CLI verbs, MCP server, enrichment pipeline, QG-1, QG-3

### Phase 2: Standardization (Sprint 3)
**Duration:** 4 days
**Deliverables:** Complete profiles, linter, QG-2

### Phase 3: Documentation (Sprint 4)
**Duration:** 3 days
**Deliverables:** Agent instructions, updated docs, QG-5

### Phase 4: Integration (Sprint 5)
**Duration:** 3 days
**Deliverables:** CI automation, TA tooling, QG-4

### Phase 5: Validation & Handoff
**Duration:** 2 days
**Deliverables:** Full TA verification, migration guides, team training

**Total Duration:** ~3 weeks

---

## Dependencies

### External Dependencies
- MCP protocol library (Python SDK)
- Great Expectations ≥ 1.8.0
- Existing test infrastructure

### Internal Dependencies
- Existing enrichment providers
- Profile system
- CLI framework
- Observability infrastructure

---

## Testing Strategy

### Unit Tests
- All new modules have ≥90% coverage
- Mock network calls in enrichment tests
- Parametrize tests across profiles

### Integration Tests
- E2E CLI flows (refine → enrich → qa)
- MCP server lifecycle tests
- Profile migration tests

### Quality Gate Tests
- Dedicated test module per gate
- Runnable standalone (CI + local)
- Clear pass/fail criteria

### Regression Tests
- Existing tests must continue passing
- Backwards compatibility for CLI
- Profile schema backwards compatibility

---

## Rollback Plan

### If MCP Integration Fails
- MCP is additive; CLI remains functional
- Feature flag: `FEATURE_ENABLE_MCP`
- Disable in CI, continue with CLI-only

### If Profile Migration Fails
- Keep old schema support as fallback
- Warn on deprecated schema usage
- Provide 2-version migration window

### If Quality Gates Block CI
- Make gates advisory initially (warnings)
- Promote to blocking after 1 week
- Allow override with approval

---

## Handoff Checklist

### For Development Team
- [ ] All code merged to main branch
- [ ] CI passing with all quality gates
- [ ] Migration scripts tested
- [ ] Rollback procedures documented

### For Documentation Team
- [ ] All docs reviewed for accuracy
- [ ] Agent instructions validated with Copilot
- [ ] Migration guides published
- [ ] Changelog updated

### For Operations Team
- [ ] CI workflows documented
- [ ] Quality gate runbooks created
- [ ] Incident response procedures updated
- [ ] Monitoring alerts configured

### For Product Team
- [ ] TA criteria verified
- [ ] User-facing changes documented
- [ ] Breaking changes communicated
- [ ] Upgrade timeline published

---

## Appendices

### Appendix A: CLI Command Mapping

| Old Command | New Command | Alias | Notes |
|-------------|-------------|-------|-------|
| `run` | `refine` | Yes | Primary refinement |
| N/A | `enrich` | No | New functionality |
| N/A | `qa` | No | New, wraps existing checks |
| N/A | `contracts` | No | New, schema emission |
| N/A | `overview` | No | New, discovery |

### Appendix B: MCP Tool Signatures

```typescript
// hotpass.refine
{
  name: "hotpass.refine",
  description: "Run the Hotpass refinement pipeline",
  inputSchema: {
    type: "object",
    properties: {
      input_path: { type: "string" },
      output_path: { type: "string" },
      profile: { type: "string" },
      archive: { type: "boolean", default: false }
    },
    required: ["input_path", "output_path", "profile"]
  }
}

// hotpass.enrich
{
  name: "hotpass.enrich",
  description: "Enrich data with deterministic and optional network sources",
  inputSchema: {
    type: "object",
    properties: {
      input_path: { type: "string" },
      output_path: { type: "string" },
      profile: { type: "string" },
      allow_network: { type: "boolean", default: false }
    },
    required: ["input_path", "output_path", "profile"]
  }
}

// hotpass.qa
{
  name: "hotpass.qa",
  description: "Run quality assurance checks",
  inputSchema: {
    type: "object",
    properties: {
      target: {
        type: "string",
        enum: ["all", "contracts", "docs", "profiles", "ta"],
        default: "all"
      }
    }
  }
}

// hotpass.explain_provenance
{
  name: "hotpass.explain_provenance",
  description: "Explain data provenance for a specific row",
  inputSchema: {
    type: "object",
    properties: {
      row_id: { type: "string" },
      dataset_path: { type: "string" }
    },
    required: ["row_id", "dataset_path"]
  }
}

// hotpass.crawl (optional, guarded)
{
  name: "hotpass.crawl",
  description: "Execute research crawler (requires network permission)",
  inputSchema: {
    type: "object",
    properties: {
      query_or_url: { type: "string" },
      profile: { type: "string" },
      backend: {
        type: "string",
        enum: ["deterministic", "research"],
        default: "deterministic"
      }
    },
    required: ["query_or_url", "profile"]
  }
}
```

### Appendix C: Profile Schema Example

```yaml
# Complete profile schema (all 4 blocks)
name: aviation
display_name: Aviation & Flight Training

# Block 1: Ingest
ingest:
  sources:
    - name: SACAA Cleaned
      format: xlsx
      path_pattern: "data/*sacaa*.xlsx"
      priority: 3
    - name: Reachout Database
      format: xlsx
      path_pattern: "data/*reachout*.xlsx"
      priority: 2
  chunk_size: 5000
  staging_enabled: true
  staging_format: parquet

# Block 2: Refine
refine:
  mappings:
    organization_name:
      - school_name
      - institution_name
      - provider_name
    contact_email:
      - email
      - email_address
      - primary_email
  deduplication:
    strategy: entity_resolution
    threshold: 0.85
    blocking_keys:
      - organization_name_normalized
  normalization:
    phone_format: E164
    country_code: ZA
  expectations:
    - expect_column_values_to_not_be_null:
        column: organization_name
    - expect_column_values_to_match_regex:
        column: contact_email
        regex: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
  quality_thresholds:
    email: 0.85
    phone: 0.85
    website: 0.75

# Block 3: Enrich
enrich:
  allow_network: false  # Default, can be overridden by env/CLI
  fetcher_chain:
    - deterministic  # Always run
    - lookup_tables  # Always run
    - research       # Only if network enabled
  backfillable_fields:
    - contact_email
    - contact_phone
    - website
    - province
  confidence_threshold: 0.7
  provenance_required: true

# Block 4: Compliance
compliance:
  policy: POPIA
  jurisdiction: ZA
  consent_required: true
  pii_fields:
    - contact_email
    - contact_phone
    - contact_name
  retention_days: 365
  anonymization_on_request: true
  audit_trail_required: true
```

### Appendix D: Fitness Function Updates

Add to `scripts/quality/fitness_functions.py`:

```python
# New checks for UPGRADE.md compliance
def check_mcp_server_exists() -> None:
    mcp_server = SRC_ROOT / "mcp" / "server.py"
    if not mcp_server.exists():
        raise FitnessFailure("MCP server missing at src/hotpass/mcp/server.py")

def check_profile_completeness(profile_name: str) -> None:
    profile_path = SRC_ROOT / "profiles" / f"{profile_name}.yaml"
    content = yaml.safe_load(profile_path.read_text())

    required_blocks = ["ingest", "refine", "enrich", "compliance"]
    missing = [block for block in required_blocks if block not in content]

    if missing:
        raise FitnessFailure(
            f"Profile {profile_name} missing blocks: {missing}"
        )

# Add to main():
checks.extend([
    lambda: check_mcp_server_exists(),
    lambda: check_profile_completeness("aviation"),
    lambda: check_profile_completeness("generic"),
])
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-30 | Dev Team | Initial implementation plan |

---

## Sign-off

**Technical Lead:** _______________ Date: ___________

**Product Owner:** _______________ Date: ___________

**QA Lead:** _______________ Date: ___________

---

*This document is version-controlled and maintained in the Hotpass repository.*
