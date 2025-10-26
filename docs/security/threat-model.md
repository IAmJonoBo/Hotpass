---
title: Security — threat model
summary: Multi-surface threat model covering CLI, Prefect flows, and the Streamlit dashboard with STRIDE and MITRE mappings.
last_updated: 2025-10-26
---

# Security threat model

## Executive summary

Hotpass exposes three operator-facing entry points: the command-line interface (CLI), Prefect flow deployments, and the Streamlit dashboard. Each surface touches the same sensitive assets—raw customer spreadsheets, refined exports, and audit metadata—so tampering or leakage on one surface can cascade. The CLI enforces strict option validation and structured logging, the Prefect flow validates deployment parameters with Pydantic models, and the dashboard now ships with password-gated access plus filesystem allowlists to contain data movement.

Key safeguards already in place include configuration validation in the CLI, Prefect task retries, regression tests that exercise deployment error paths, and dashboard authentication backed by environment-configured shared secrets. Remaining gaps centre on moving from shared-secret auth to SSO, supply-chain integrity (curl-based installer, unpinned Actions), and secrets platform alignment. The tables below map threats to STRIDE categories and MITRE ATT&CK techniques, with detection/prevention evidence.

## Entry point inventory and STRIDE mapping

| Entry point | Critical assets | STRIDE threats | Existing controls | MITRE techniques | Detection & evidence |
| --- | --- | --- | --- | --- | --- |
| CLI (`hotpass.cli`) | Raw spreadsheets (`data/`), refined workbooks (`dist/`), quality reports (`logs/`) | **Spoofing**: malicious config path injection; **Tampering**: modified config toggling archive/logging; **Repudiation**: operators denying actions; **Information disclosure**: verbose logs leaking PII; **Denial of service**: malformed chunk size/empty input dir; **Elevation of privilege**: staged parquet overwriting system paths | Parser restricts formats (`.json`, `.toml`), validates chunk size > 0, restricts log/report formats, and blocks execution when input dir missing or empty | `T1565` Data Manipulation, `T1499` Endpoint DoS, `T1059.006` Command-Line | Parser enforces constraints and raises errors for unsupported config/log formats; tests assert JSON logging emits archive events and rejects invalid config values【F:src/hotpass/cli.py†L50-L213】【F:tests/test_cli.py†L81-L195】 |
| Prefect flow (`hotpass.orchestration`) | Prefect deployment credentials, pipeline outputs, archive artifacts | **Spoofing**: attacker registering fake Prefect deployment; **Tampering**: unvalidated parameters altering filesystem targets; **Repudiation**: lack of run provenance if Prefect unavailable; **Information disclosure**: Prefect logs/archives; **Denial of service**: repeated task retries on poisoned data; **Elevation of privilege**: Prefect deployment executing attacker code | Prefect decorators add retries, logging, and archiving with try/except; deployment helper errors when Prefect missing, preventing silent fallback | `T1078` Valid Accounts, `T1106` Native API, `T1490` Inhibit Recovery | Flow annotates retries and archives, but `validate_parameters=False` keeps trust boundary open; tests confirm deployment fails without Prefect and that serve helper is called when available, giving hooks to monitor deployments【F:src/hotpass/orchestration.py†L119-L200】【F:tests/test_orchestration.py†L35-L150】 |
| Streamlit dashboard (`hotpass.dashboard`) | Same filesystem assets plus run history (`logs/pipeline_history.json`) | **Spoofing**: unauthenticated UI in shared network (mitigated by password gate); **Tampering**: user-supplied paths allow arbitrary file read/write (mitigated via allowlists); **Repudiation**: run history stored locally without signatures; **Information disclosure**: UI renders full dataset previews; **Denial of service**: repeated runs saturate resources; **Elevation of privilege**: pipeline executes with dashboard user's filesystem permissions | Shared-secret authentication enforced via environment variable; filesystem allowlists restrict read/write roots; saves history in JSON with append-only behaviour; leverages same pipeline validation; UI feedback for success/failure | `T1190` Exploit Public-Facing Application, `T1047` Windows Management Instrumentation analog (remote execution), `T1110` Brute Force | Functions require authentication before pipeline execution, validate paths against allowlists, and append history with sanitised paths; regression tests assert authentication, access denial, and allowlist enforcement.【F:src/hotpass/dashboard.py†L1-L220】【F:tests/test_dashboard.py†L1-L216】 |

### Observed gaps

- **Dashboard authentication:** Shared-secret password protects access today; migrate to SSO-backed auth and session auditing for multi-tenant deployments.
- **Prefect parameter validation:** `validate_parameters=False` permits arbitrary string arguments, enabling tampering/EoP if deployment is exposed.
- **CLI log redaction:** Structured logger emits raw report content, risking accidental disclosure of PII in logs.
- **Secrets platform rollout:** Vault selected for centralised secrets; wire CI, Prefect, and dashboard workloads into Vault and verify audit log coverage.

## MITRE ATT&CK cross-reference and control status

| Technique ID | Description | Surface | Status | Detection/Prevention evidence |
| --- | --- | --- | --- | --- |
| `T1059.006` | Command-line execution via scripts | CLI | **Mitigated** (option validation, required existing Excel files) | CLI raises errors on missing directories or empty inputs, halting execution; tests assert archive and report events only emit after successful runs【F:src/hotpass/cli.py†L387-L400】【F:tests/test_cli.py†L91-L181】 |
| `T1565` | Data manipulation through config alteration | CLI, Dashboard | **Partially mitigated** (format restrictions, but config files not signed) | `_load_config` restricts accepted formats, and tests raise `ValueError` for invalid log formats, but no integrity checking or signing exists【F:src/hotpass/cli.py†L234-L241】【F:tests/test_cli.py†L184-L195】 |
| `T1499` | Local resource DoS | CLI, Prefect | **Partially mitigated** (chunk size validation, Prefect retries) | Chunk size must be >0 and Prefect tasks cap retries; tests confirm chunk staging path invoked when set, implying control coverage but not guarding huge files【F:src/hotpass/cli.py†L194-L229】【F:tests/test_cli.py†L144-L182】【F:src/hotpass/orchestration.py†L119-L151】 |
| `T1078` | Abuse of valid accounts (Prefect) | Prefect | **Unmitigated** (depends on Prefect work pool auth) | `deploy_pipeline` warns when Prefect absent but trusts Prefect identity; tests only cover availability, not credential scoping—requires external control【F:src/hotpass/orchestration.py†L190-L216】【F:tests/test_orchestration.py†L113-L150】 |
| `T1190` | Exploit public-facing app | Dashboard | **Mitigated** (password gate + filesystem allowlists) | Dashboard enforces shared-secret authentication and validates both input and output paths against an allowlist before executing the pipeline, preventing untrusted operators from running arbitrary file operations.【F:src/hotpass/dashboard.py†L44-L220】【F:tests/test_dashboard.py†L120-L216】 |
| `T1530` | Data from local system | CLI, Dashboard | **Partially mitigated** (structured logging, manual review) | Structured logger prints full report data; tests verify JSON logs include report payloads, demonstrating potential leak—needs sanitisation or filtering【F:src/hotpass/cli.py†L253-L345】【F:tests/test_cli.py†L60-L140】 |

## Infrastructure and IaC assessment

- **Dockerfile**: Uses Micromamba base, installs Python via Conda, then executes a curl-piped shell script to install `uv`. This script execution is unsigned and unauthenticated, introducing supply-chain risk. Recommend pinning the installer checksum and swapping to a release tarball fetched with verification, plus running `uv sync --frozen --no-editable` under non-root user (currently switches after dependency sync)【F:Dockerfile†L1-L33】.
- **Filesystem permissions**: Image copies source and docs before switching to `appuser`. Consider tightening permissions on `/app/data`, `/app/logs`, and `/app/dist` via `RUN install -d -m 750 --owner appuser --group appuser ...` to reduce exposure.
- **Healthcheck**: Probes `http://localhost:8000/health`, but container entrypoint runs CLI, not a server, so healthcheck will fail and may mask runtime regressions. Either add a lightweight HTTP status endpoint or remove the healthcheck.
- **IaC gaps**: No Kubernetes manifests or Terraform present. Propose authoring baseline templates (e.g., Kubernetes Deployment + Secret + ConfigMap) with securityContext hardening once deployment target is defined.

## CI/CD supply-chain evaluation

- **Workflow pinning**: `actions/checkout@v5` and other reusable actions rely on tags; pin to specific commit SHAs to prevent tag hijacking【F:.github/workflows/process-data.yml†L13-L118】.
- **Dependency integrity**: `uv sync --extra dev --frozen` honours `uv.lock`, but there is no checksum verification of downloaded archives in CI. Consider adding `uv pip hash --locked` or enabling Sigstore provenance checks once supported.
- **Artifact handling**: Workflow pushes archives to `data-artifacts` using a PAT fallback. Ensure `DATA_ARTIFACT_PAT` is scoped to artifact branch only and audit logs for forced pushes. Add verification command (e.g., `sha256sum dist/*.zip > dist/ARCHIVE.sha256`) prior to upload.
- **Proposed reproducible verification**:
  - `uv run pytest --cov=src --cov=tests --cov-report=term-missing` (baseline now passing)【150a53†L1-L74】
  - `uv run ruff check` for lint coverage【6b0e7e†L1-L3】
  - `uv run mypy src tests scripts` for type regressions【3f68f9†L1-L24】
  - `uv run bandit -r src scripts` and `uv run detect-secrets scan src tests scripts` for security/secrets drift【f75107†L1-L18】【f75013†L1-L67】
  - `uv run uv build` to ensure release artifacts reproducible【28ec86†L1-L119】
  - Add `sha256sum dist/*.zip` and compare with previous manifest in `data-artifacts` branch to detect tampering.

## Findings, evidence, and mitigations

| Finding | Impact | Evidence | Recommended mitigation |
| --- | --- | --- | --- |
| Dashboard lacks authentication and path validation | Remote operators could execute pipeline against arbitrary paths, exfiltrating or corrupting data | Mitigated: dashboard enforces shared-secret authentication and validates filesystem selections against environment-configured allowlists before executing pipelines; regression tests cover lockout, unlock, and validation behaviour.【F:src/hotpass/dashboard.py†L44-L220】【F:tests/test_dashboard.py†L120-L216】 | Maintain shared-secret rotation policy, add access logging, and plan SSO integration for multi-tenant deployments. |
| Prefect flow skips parameter validation (`validate_parameters=False`) | Malicious deployment updates can supply crafted paths, leading to tampering or lateral movement | Mitigated: the flow now validates parameters with Pydantic models, rejects non-existent directories and invalid chunk sizes, and raises clear errors under test coverage.【F:src/hotpass/orchestration.py†L136-L227】【F:tests/test_orchestration.py†L1-L129】 | Document Prefect block policies that complement the runtime validation and align them with NIST SP 800-53 CM-7. |
| CLI structured logger emits full report payloads | Potential PII disclosure in logs shipped to SIEM or stdout | Mitigated: structured logging redacts configurable sensitive fields by default, and regression tests assert `[REDACTED]` output for email and phone conflicts.【F:src/hotpass/cli.py†L33-L356】【F:tests/test_cli.py†L1-L158】 | Extend runbooks with guidance on additional redaction masks required for regulated deployments and confirm SIEM ingestion honours the mask. |
| Dockerfile installs tooling via unsigned curl script | Supply-chain compromise risk; attacker-controlled install script can run arbitrary code | Mitigated: Dockerfile now downloads a pinned release tarball and verifies SHA-256 before installing `uv`, eliminating the curl-pipe risk.【F:Dockerfile†L12-L20】 | Monitor upstream `uv` releases and rotate pinned version and checksum during regular dependency reviews; consider packaging via Micromamba/Conda channels for centralized governance. |
| GitHub Actions workflows use floating action tags and force-push artifacts | Attacker controlling action tag or PAT could modify pipeline/artifacts | Workflows rely on version tags and push archives with PAT; no checksum recorded【F:.github/workflows/process-data.yml†L13-L118】 | Pin actions to commit SHAs, scope PAT to artifact branch, and publish checksums for archives (supply chain best practices per OWASP CICD-SEC). |

## Proof-of-value logs and artefacts

- Baseline QA suite: `uv run pytest --cov=src --cov=tests --cov-report=term-missing` (pass)【150a53†L1-L74】
- Lint/type/security scans: `uv run ruff check`, `uv run mypy src tests scripts`, `uv run bandit -r src scripts`, `uv run detect-secrets scan src tests scripts` (all clean)【6b0e7e†L1-L3】【3f68f9†L1-L24】【f75107†L1-L18】【f75013†L1-L67】
- Build reproducibility: `uv run uv build` succeeded, producing wheel/tarball for comparison in future reviews【28ec86†L1-L119】

## Next steps

1. ✅ Harden dashboard authentication and filesystem allowlists.【F:src/hotpass/dashboard.py†L44-L220】【F:tests/test_dashboard.py†L120-L216】
2. ✅ Enforce Prefect parameter validation and document required deployment policies.【F:src/hotpass/orchestration.py†L136-L227】【F:tests/test_orchestration.py†L1-L129】
3. ✅ Implement log redaction and document handling of sensitive metrics.【F:src/hotpass/cli.py†L33-L356】【F:tests/test_cli.py†L1-L158】
4. ✅ Refactor Dockerfile to eliminate curl-pipe shell and introduce checksum verification (pinned `uv` tarball + SHA-256 validation in Dockerfile).【F:Dockerfile†L12-L20】
5. Pin GitHub Actions and add checksum verification for released artifacts.

Update `Next_Steps.md` with owners and due dates aligned to platform and DevOps teams.
