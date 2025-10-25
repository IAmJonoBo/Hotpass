---
title: Security — threat model
summary: Multi-surface threat model covering CLI, Prefect flows, and the Streamlit dashboard with STRIDE and MITRE mappings.
last_updated: 2025-10-25
---

# Security threat model

## Executive summary

Hotpass exposes three operator-facing entry points: the command-line interface (CLI), Prefect flow deployments, and the Streamlit dashboard. Each surface touches the same sensitive assets—raw customer spreadsheets, refined exports, and audit metadata—so tampering or leakage on one surface can cascade. The CLI enforces strict option validation and structured logging, while the Prefect flow enables retries and archiving hooks. The dashboard embeds pipeline execution directly in the UI and persists run history on disk, making it the least isolated surface.

Key safeguards already in place include configuration validation in the CLI, Prefect task retries, and regression tests that exercise deployment error paths. Gaps centre on authentication (dashboard), parameter validation (Prefect flow), and supply-chain integrity (curl-based installer, unpinned Actions). The tables below map threats to STRIDE categories and MITRE ATT&CK techniques, with detection/prevention evidence.

## Entry point inventory and STRIDE mapping

| Entry point | Critical assets | STRIDE threats | Existing controls | MITRE techniques | Detection & evidence |
| --- | --- | --- | --- | --- | --- |
| CLI (`hotpass.cli`) | Raw spreadsheets (`data/`), refined workbooks (`dist/`), quality reports (`logs/`) | **Spoofing**: malicious config path injection; **Tampering**: modified config toggling archive/logging; **Repudiation**: operators denying actions; **Information disclosure**: verbose logs leaking PII; **Denial of service**: malformed chunk size/empty input dir; **Elevation of privilege**: staged parquet overwriting system paths | Parser restricts formats (`.json`, `.toml`), validates chunk size > 0, restricts log/report formats, and blocks execution when input dir missing or empty | `T1565` Data Manipulation, `T1499` Endpoint DoS, `T1059.006` Command-Line | Parser enforces constraints and raises errors for unsupported config/log formats; tests assert JSON logging emits archive events and rejects invalid config values【F:src/hotpass/cli.py†L50-L213】【F:tests/test_cli.py†L81-L195】 |
| Prefect flow (`hotpass.orchestration`) | Prefect deployment credentials, pipeline outputs, archive artifacts | **Spoofing**: attacker registering fake Prefect deployment; **Tampering**: unvalidated parameters altering filesystem targets; **Repudiation**: lack of run provenance if Prefect unavailable; **Information disclosure**: Prefect logs/archives; **Denial of service**: repeated task retries on poisoned data; **Elevation of privilege**: Prefect deployment executing attacker code | Prefect decorators add retries, logging, and archiving with try/except; deployment helper errors when Prefect missing, preventing silent fallback | `T1078` Valid Accounts, `T1106` Native API, `T1490` Inhibit Recovery | Flow annotates retries and archives, but `validate_parameters=False` keeps trust boundary open; tests confirm deployment fails without Prefect and that serve helper is called when available, giving hooks to monitor deployments【F:src/hotpass/orchestration.py†L119-L200】【F:tests/test_orchestration.py†L35-L150】 |
| Streamlit dashboard (`hotpass.dashboard`) | Same filesystem assets plus run history (`logs/pipeline_history.json`) | **Spoofing**: unauthenticated UI in shared network; **Tampering**: user-supplied paths allow arbitrary file read/write; **Repudiation**: run history stored locally without signatures; **Information disclosure**: UI renders full dataset previews; **Denial of service**: repeated runs saturate resources; **Elevation of privilege**: pipeline executes with dashboard user's filesystem permissions | Saves history in JSON with append-only behaviour; leverages same pipeline validation; UI feedback for success/failure | `T1190` Exploit Public-Facing Application, `T1047` Windows Management Instrumentation analog (remote execution), `T1110` Brute Force (if auth added later) | Functions create directories securely and append history; tests verify history append behaviour and pipeline invocation but no auth or path restrictions—flag for mitigation【F:src/hotpass/dashboard.py†L19-L167】【F:tests/test_dashboard.py†L70-L141】 |

### Observed gaps

- **Dashboard authentication:** No session protection; exposure outside a trusted LAN invites spoofing and tampering.
- **Prefect parameter validation:** `validate_parameters=False` permits arbitrary string arguments, enabling tampering/EoP if deployment is exposed.
- **CLI log redaction:** Structured logger emits raw report content, risking accidental disclosure of PII in logs.

## MITRE ATT&CK cross-reference and control status

| Technique ID | Description | Surface | Status | Detection/Prevention evidence |
| --- | --- | --- | --- | --- |
| `T1059.006` | Command-line execution via scripts | CLI | **Mitigated** (option validation, required existing Excel files) | CLI raises errors on missing directories or empty inputs, halting execution; tests assert archive and report events only emit after successful runs【F:src/hotpass/cli.py†L387-L400】【F:tests/test_cli.py†L91-L181】 |
| `T1565` | Data manipulation through config alteration | CLI, Dashboard | **Partially mitigated** (format restrictions, but config files not signed) | `_load_config` restricts accepted formats, and tests raise `ValueError` for invalid log formats, but no integrity checking or signing exists【F:src/hotpass/cli.py†L234-L241】【F:tests/test_cli.py†L184-L195】 |
| `T1499` | Local resource DoS | CLI, Prefect | **Partially mitigated** (chunk size validation, Prefect retries) | Chunk size must be >0 and Prefect tasks cap retries; tests confirm chunk staging path invoked when set, implying control coverage but not guarding huge files【F:src/hotpass/cli.py†L194-L229】【F:tests/test_cli.py†L144-L182】【F:src/hotpass/orchestration.py†L119-L151】 |
| `T1078` | Abuse of valid accounts (Prefect) | Prefect | **Unmitigated** (depends on Prefect work pool auth) | `deploy_pipeline` warns when Prefect absent but trusts Prefect identity; tests only cover availability, not credential scoping—requires external control【F:src/hotpass/orchestration.py†L190-L216】【F:tests/test_orchestration.py†L113-L150】 |
| `T1190` | Exploit public-facing app | Dashboard | **Unmitigated** (no auth, unvalidated paths) | Dashboard accepts arbitrary `input_dir` and `output_path` from UI and runs pipeline with them; tests show pipeline executes on button press without safeguards【F:src/hotpass/dashboard.py†L64-L167】【F:tests/test_dashboard.py†L92-L141】 |
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
| Dashboard lacks authentication and path validation | Remote operators could execute pipeline against arbitrary paths, exfiltrating or corrupting data | Dashboard accepts arbitrary `input_dir`/`output_path` and executes pipeline; tests confirm run without safeguards【F:src/hotpass/dashboard.py†L64-L167】【F:tests/test_dashboard.py†L92-L141】 | Add authentication (e.g., SSO or token header), restrict paths to approved roots, and enforce allowlists via `Path.resolve().is_relative_to()` checks. Reference OWASP ASVS 4.0.3 V2 controls. |
| Prefect flow skips parameter validation (`validate_parameters=False`) | Malicious deployment updates can supply crafted paths, leading to tampering or lateral movement | Flow decorator disables validation, relying on downstream code; tests show deployment wiring but no parameter guards【F:src/hotpass/orchestration.py†L154-L200】【F:tests/test_orchestration.py†L67-L111】 | Enable `validate_parameters=True`, define Pydantic parameter models, and add Prefect block policies to restrict schedule updates. Align with NIST SP 800-53 CM-7. |
| CLI structured logger emits full report payloads | Potential PII disclosure in logs shipped to SIEM or stdout | Logger prints report metrics and details without redaction; tests assert presence of detailed metrics in outputs【F:src/hotpass/cli.py†L253-L345】【F:tests/test_cli.py†L60-L140】 | Introduce redaction filters for sensitive columns (PII), provide `--sensitive-fields` mask, and document sanitisation. Map to GDPR Art. 32 data minimisation. |
| Dockerfile installs tooling via unsigned curl script | Supply-chain compromise risk; attacker-controlled install script can run arbitrary code | `RUN curl -LsSf https://astral.sh/uv/install.sh | sh` executes remote script during build【F:Dockerfile†L9-L18】 | Replace with pinned release tarball + checksum verification (e.g., `curl .../uv.tar.gz` + `sha256sum`), or vendor `uv` via Micromamba/Conda package. Reference SLSA Level 1 requirements. |
| GitHub Actions workflows use floating action tags and force-push artifacts | Attacker controlling action tag or PAT could modify pipeline/artifacts | Workflows rely on version tags and push archives with PAT; no checksum recorded【F:.github/workflows/process-data.yml†L13-L118】 | Pin actions to commit SHAs, scope PAT to artifact branch, and publish checksums for archives (supply chain best practices per OWASP CICD-SEC). |

## Proof-of-value logs and artefacts

- Baseline QA suite: `uv run pytest --cov=src --cov=tests --cov-report=term-missing` (pass)【150a53†L1-L74】
- Lint/type/security scans: `uv run ruff check`, `uv run mypy src tests scripts`, `uv run bandit -r src scripts`, `uv run detect-secrets scan src tests scripts` (all clean)【6b0e7e†L1-L3】【3f68f9†L1-L24】【f75107†L1-L18】【f75013†L1-L67】
- Build reproducibility: `uv run uv build` succeeded, producing wheel/tarball for comparison in future reviews【28ec86†L1-L119】

## Next steps

1. Harden dashboard authentication and filesystem allowlists.
2. Enforce Prefect parameter validation and document required deployment policies.
3. Implement log redaction and document handling of sensitive metrics.
4. Refactor Dockerfile to eliminate curl-pipe shell and introduce checksum verification.
5. Pin GitHub Actions and add checksum verification for released artifacts.

Update `Next_Steps.md` with owners and due dates aligned to platform and DevOps teams.
