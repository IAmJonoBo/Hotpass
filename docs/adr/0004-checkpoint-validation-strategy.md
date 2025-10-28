# ADR-0004: Checkpoint-Based Validation with Data Docs

**Status:** Accepted

**Date:** 2025-10-28

**Context:**

The Hotpass pipeline previously used direct Great Expectations suite validation without a structured checkpoint framework. This approach had several limitations:

1. Validation results were ephemeral and not persistently stored
2. No automated Data Docs generation for visual inspection of results
3. Suite configurations were scattered across subdirectories (`contact/`, `reachout/`, `sacaa/`)
4. No standardized integration point for Prefect flows and CLI commands
5. Difficult to add validation actions (e.g., Slack notifications, metrics publishing)

The pipeline needed a more robust validation infrastructure that could:

- Generate human-readable validation reports (Data Docs)
- Provide a consistent interface for checkpoint execution
- Support future enhancements like validation result storage and alerting
- Maintain backward compatibility with existing validation code

**Decision:**

We restructured the Great Expectations validation infrastructure around checkpoints:

1. **Canonical Suite Layout:**
   - Move all expectation suites to `data_expectations/suites/`
   - Use canonical dataset identifiers as suite names (e.g., `reachout_organisation.json`)
   - Add `canonical_dataset` metadata to each suite

2. **Checkpoint Configurations:**
   - Create `data_expectations/checkpoints/` for checkpoint definitions
   - Each checkpoint references its suite and defines action lists
   - Standard actions: `StoreValidationResultAction` and `UpdateDataDocsAction`

3. **New Validation API:**
   - Implement `run_checkpoint()` function for checkpoint-based validation
   - Support optional Data Docs directory parameter
   - Configure filesystem Data Docs site dynamically
   - Maintain `validate_with_expectations()` for backward compatibility

4. **CLI Integration:**
   - Exit with code 2 on `DataContractError` (distinct from general errors)
   - Display detailed validation failure context in CLI output
   - Add structured logging for validation artifacts

5. **Prefect Integration:**
   - Validation failures automatically propagate as task failures
   - No special handling needed (exception propagation works correctly)

6. **Automation:**
   - Provide `scripts/validation/refresh_data_docs.py` for CI validation
   - Script runs all checkpoints against sample workbooks
   - Generates Data Docs for inspection

**Consequences:**

### Positive

- **Better observability:** Data Docs provide rich, visual validation reports
- **Standardized structure:** Canonical suite/checkpoint layout is easier to navigate
- **Extensibility:** Checkpoint actions can be extended (e.g., Slack alerts, metrics)
- **CI-friendly:** Automated script can verify suite integrity in CI
- **Backward compatible:** Existing `validate_with_expectations()` calls work unchanged
- **Clear failures:** Exit code 2 distinguishes validation failures from other errors

### Neutral

- **Migration path:** Both old and new paths work during transition
- **Directory structure:** New `suites/` and `checkpoints/` directories added
- **Configuration:** Each dataset now has two files (suite + checkpoint)

### Negative

- **Learning curve:** Teams need to understand checkpoint vs. suite concepts
- **Disk usage:** Data Docs generation adds HTML artifacts
- **Performance:** Building Data Docs adds ~100-200ms per checkpoint

**Alternatives Considered:**

1. **Keep flat directory structure:** Rejected due to maintainability concerns
2. **Use native Great Expectations project:** Rejected as too heavyweight
3. **Custom validation framework:** Rejected to leverage GE ecosystem
4. **Separate validation step:** Rejected to keep validation inline with data loading

**References:**

- [Great Expectations Checkpoints](https://docs.greatexpectations.io/docs/terms/checkpoint/)
- [Data Docs](https://docs.greatexpectations.io/docs/terms/data_docs/)
- Implementation: PR copilot/restructure-great-expectations-assets

**Notes:**

Future enhancements could include:

- Persistent validation result stores (e.g., PostgreSQL)
- Validation result metrics exported to observability platform
- Automated Slack/email notifications on validation failures
- Historical trend analysis in Data Docs
