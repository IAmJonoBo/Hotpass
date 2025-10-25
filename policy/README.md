# Policy-as-code

This directory captures organisation-wide guardrails enforced via automation.

- `sbom.rego` — Validates CycloneDX SBOMs include the Hotpass component metadata.
- `branch-protection.yaml` — Documents required GitHub branch protection rules for `main`.

These policies are evaluated during CI (see `.github/workflows/process-data.yml`). Extend the directory with additional `rego` and YAML policies as coverage expands.
