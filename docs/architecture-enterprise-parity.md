# Hotpass Architecture: Enterprise Parity

Hotpass pairs open tooling with production guardrails so that operators coming from commercial data stacks recognise the orchestration, lineage, CI/CD, and agent layers immediately. The table below maps each pillar to its OSS analogue and links to the canonical configuration inside this repository.

| Capability        | Hotpass Implementation | Enterprise Analogue | References |
| ----------------- | ---------------------- | ------------------- | ---------- |
| Orchestration     | Prefect 3 Runner Deployments (generated via `ops/prefect/build_deployments.py`) | Airflow / Step Functions | `prefect/deployments/`, `.github/workflows/prefect-deployments.yml` |
| Lineage           | OpenLineage + Marquez (with Hotpass facets) | Collibra, Datakin | `apps/data-platform/hotpass/lineage.py`, `apps/web-ui/src/pages/Lineage.tsx`, `deploy/docker/docker-compose.yml` |
| CI/CD             | GitHub ARC with isolated namespaces + security suite | GitHub AE, Harness, CircleCI | `infra/arc/`, `.github/workflows/security-scan.yml`, `ops/arc/verify_runner_lifecycle.py` |
| Agent Layer       | Tool contract (`tools.json`) + MCP bridge | OpenAI Assistants, GitHub Copilot Service | `tools.json`, `apps/web-ui/src/agent`, `AGENTS.md`, `mcp_server.yaml` |

## Highlights

- **One source of truth for endpoints** – the web UI now reads `PREFECT_API_URL` and `OPENLINEAGE_URL` directly, matching the CLI and MCP environments.
- **Health probes & lifecycle evidence** – `/health` surfaces Prefect, Marquez, and ARC status with VPN/bastion hints; ARC lifecycle output can be exported to `dist/arc/status.json` for the UI.
- **Lineage facets** – every OpenLineage event carries `hotpass_version`, `profile`, `source_spreadsheet`, and `research_enabled` metadata so operators can filter for Hotpass-specific context inside Marquez.
- **Supply-chain gate** – pull requests run Gitleaks, pip-audit, pytest, and Playwright via the `Security & Supply Chain` workflow before merging.

Use this page as the executive summary when positioning Hotpass against managed data platforms. Each section links to the concrete manifests, workflows, or code paths that implement the capability.
