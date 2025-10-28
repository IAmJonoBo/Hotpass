# Policy-as-code

This directory captures organisation-wide guardrails enforced via automation.

- `sbom.rego` — Validates CycloneDX SBOMs include the Hotpass component metadata.
- `branch-protection.yaml` — Documents required GitHub branch protection rules for `main`.
- `semgrep/hotpass.yml` — Offline static analysis rules used by CI and local scans.
- `licensing/allowlist.yml` — Approved third-party license expressions enforced by ScanCode audits.
- `acquisition/providers.json` — Allowlisted acquisition providers with collection basis and compliance notes.
- `reuse/dep5` — REUSE policy metadata ensuring consistent copyright headers.

These policies are evaluated during CI (see `.github/workflows/process-data.yml`). Extend the directory with additional `rego` and YAML policies as coverage expands.
