# DVC Integration Workflow Steps

This document describes CI/CD integration steps for DVC data versioning.

## CI Workflow Integration

### Step 1: Validate DVC Setup

Add a job to validate DVC configuration (without requiring a configured remote):

```yaml
dvc-validation:
  runs-on: ubuntu-latest
  needs: qa
  steps:
    - uses: actions/checkout@v4

    - name: Set up uv and Python
      uses: astral-sh/setup-uv@v7
      with:
        python-version: "3.13"

    - name: Install with versioning extra
      run: uv sync --extra versioning

    - name: Validate DVC initialization
      run: |
        uv run hotpass version --status || echo "DVC not yet initialized"

    - name: Test version commands
      run: |
        uv run hotpass version --get refined_data
        uv run hotpass version --bump patch --dataset test_dataset
        uv run hotpass version --get test_dataset
```

### Step 2: Version Bump on Successful Pipeline Runs

In the `process-data` job, after successful data refinement:

```yaml
- name: Bump dataset version
  if: success() && github.ref == 'refs/heads/main'
  run: |
    uv sync --extra versioning
    uv run hotpass version --bump patch --dataset refined_data --description "Automated pipeline run"

- name: Record version metadata
  if: success()
  run: |
    VERSION=$(uv run python -c "from hotpass.versioning import DVCManager; m=DVCManager('.'); v=m.get_version('refined_data'); print(v.semver)")
    echo "dataset_version=$VERSION" >> $GITHUB_OUTPUT
  id: version
```

### Step 3: Push DVC Metadata (when remote configured)

```yaml
- name: Push DVC data
  if: success() && github.ref == 'refs/heads/main' && env.DVC_REMOTE_CONFIGURED == 'true'
  env:
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
  run: |
    dvc push
```

### Step 4: Artifact Upload with Version

```yaml
- name: Upload refined data with version
  uses: actions/upload-artifact@v4
  with:
    name: refined-data-v${{ steps.version.outputs.dataset_version }}
    path: |
      data/refined_data.xlsx
      dist/refined_data.version.json
```

## Production Deployment Steps

### Configure DVC Remote

For production pipelines, configure DVC remote storage:

```bash
# Using S3
dvc remote add -d production s3://your-bucket/hotpass-data
dvc remote modify production region us-east-1

# Commit configuration
git add .dvc/config
git commit -m "Configure production DVC remote"
git push
```

### Set Secrets in GitHub

Configure the following secrets for DVC push operations:

- `AWS_ACCESS_KEY_ID` (for S3)
- `AWS_SECRET_ACCESS_KEY` (for S3)
- `AZURE_STORAGE_CONNECTION_STRING` (for Azure)
- `GCS_SERVICE_ACCOUNT_KEY` (for GCS)

### Enable DVC Push in Workflow

Set the `DVC_REMOTE_CONFIGURED` environment variable:

```yaml
env:
  DVC_REMOTE_CONFIGURED: "true"
```

## Recovery Workflow

To restore a specific dataset version:

1. **Trigger workflow with specific version**:

   ```yaml
   workflow_dispatch:
     inputs:
       restore_version:
         description: "Dataset version to restore (e.g., 1.2.3)"
         required: false
   ```

2. **Checkout and restore**:
   ```yaml
   - name: Restore specific version
     if: github.event.inputs.restore_version != ''
     run: |
       git fetch --tags
       git checkout refined_data-v${{ github.event.inputs.restore_version }}
       dvc pull
   ```

## Local Development Setup

For developers working locally:

```bash
# Initialize DVC (first time only)
hotpass version --init

# Configure local remote for development
dvc remote add -d local-dev /mnt/data/hotpass-dvc
dvc remote modify local-dev --local

# Track datasets
hotpass version --add data/
hotpass version --add dist/refined_data.xlsx

# After pipeline runs
hotpass version --bump patch
dvc push
```

## Monitoring and Alerts

Consider adding monitoring for:

- DVC push failures
- Version mismatch between Git tags and version metadata
- Missing version metadata files
- Remote storage quota warnings

## Testing

Include DVC operations in your test suite:

```python
def test_version_management():
    from hotpass.versioning import DVCManager, DatasetVersion

    manager = DVCManager(tmp_path)
    manager.initialize()

    version = DatasetVersion(1, 0, 0, timestamp="2025-01-01T00:00:00Z")
    assert manager.set_version(version)

    retrieved = manager.get_version()
    assert retrieved.semver == "1.0.0"
```

## See Also

- [Managing data versions](../docs/how-to-guides/manage-data-versions.md)
- [Process data workflow](.github/workflows/process-data.yml)
- [DVC Documentation](https://dvc.org/doc/start)
