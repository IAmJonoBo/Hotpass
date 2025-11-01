# Hotpass vNext Upgrade Blueprint

**Version:** 2.0  
**Date:** 2025-11-01  
**Audience:** Platform Engineering · Data Quality · Compliance · Agent Enablement · Product  
**Goal:** Rebuild Hotpass into an API-first, contract-driven data refinery with unified CLI/MCP/UI experiences, production-grade governance, and end-to-end observability.  
**Supersedes:** All prior upgrade runbooks (`UPGRADE.md` ≤ v1.1, `UPGRADE_B.md`, `GAP_ANALYSIS_30_10_25.md`).

---

## Executive Summary
- We will deliver Hotpass vNext through six sequential phases plus a launch gate, each gated by contracts, automated tests, and operational readiness.
- Core tenets: API-first with shared SDK, contract-driven data plane, secure-by-construction (OPA, audit, RBAC), observable-by-default, and automation of the golden operator path.
- The current codebase already provides rich CLI tooling (`apps/data-platform/hotpass/cli`), MCP integrations (`apps/data-platform/hotpass/mcp/server.py`), Prefect flows, and a lineage emitter. These become targets for refactoring to use the new service fabric rather than being rewritten from scratch.
- Major lifts include: building the FastAPI service layer and SDK, migrating orchestration to Prefect 3, implementing a lineage-aware lakehouse with data contracts, modernising the React operator console, introducing an LLM router, and codifying security/compliance controls with observable infrastructure.

---

## 0. Gap Analysis (Nov 2025)

| Domain | Existing Assets | Reuse Potential | Critical Gaps / Actions |
| --- | --- | --- | --- |
| **Service/API Layer** | No dedicated HTTP service; logic lives in CLI modules and `apps/data-platform/hotpass/*.py`. | Pipeline, lineage, research code can be wrapped via new SDK. | Build FastAPI app (`apps/service/api`), shared Pydantic models, authentication middleware, rate limiting, tracing. |
| **SDK & Contracts** | CLI utilities, helper modules, but no central typed SDK. | CLI command implementations inform SDK ergonomics. | Generate OpenAPI + TypeScript/Python clients, enforce schema registry, embed retry/backoff & tracing. |
| **CLI & MCP** | Mature command set in `apps/data-platform/hotpass/cli/commands` and MCP server in `apps/data-platform/hotpass/mcp/server.py`. | High – commands can call new SDK once refactored. | Decouple direct imports, add telemetry, standardise error handling, expand tool catalogue. |
| **Prefect & Workers** | Prefect 2 deployments (`prefect/deployments/*.yaml`), flows in `apps/data-platform/hotpass/orchestration.py`. | Flows reusable with minimal refactor. | Migrate to Prefect 3 work pools, update docker-compose (`deploy/docker/docker-compose.yml`) to Prefect 3 images, add async workers. |
| **Data Pipeline & Contracts** | Configurable pipeline modules (`pipeline`, `pipeline_enhanced`), but limited contract enforcement. | Logic reusable with contract hooks. | Introduce schema registry, `/contracts` API, automated validation, GDPR-compliant retention. |
| **Lineage & Provenance** | OpenLineage wrapper in `apps/data-platform/hotpass/lineage.py`, tests in `tests/test_lineage.py`. | Facet builder can be extended. | Add dataset version, column fingerprints, provenance ledger, Marquez event stream APIs. |
| **Research & Automation** | Adaptive orchestrator in `apps/data-platform/hotpass/research/orchestrator.py`, CLI & MCP tooling. | High reuse after API abstraction. | Add policy gates, audit streams, deterministic/network split in service layer. |
| **UI/UX** | React app in `apps/web-ui` (Dashboard, Lineage, Health, Admin prototypes). | Components & styling can seed new Control Center. | Build Control Center, Lineage Explorer v2, Run timeline, Admin policy/LLM consoles, agent activity pane. |
| **Observability & Telemetry** | Basic telemetry hooks (`apps/data-platform/hotpass/telemetry.py`), limited dashboards. | Logging patterns exist. | Implement full metrics/logging/tracing stack (Prometheus/Grafana/OTEL), SLO dashboards, alerting. |
| **Security & Compliance** | Docs (`docs/compliance/*`, `maturity-matrix.md`), gitleaks/pip-audit workflows. | Policies inform future controls. | OIDC RBAC integration, OPA policy enforcement, secrets management, compliance evidence automation. |
| **Infrastructure & DevEx** | Docker Compose stack, Make targets, docs; no Terraform/Helm. | Compose stack seeds local env. | Author Terraform modules, Helm charts, GitOps pipeline, reproducible bootstrap (`make bootstrap`). |
| **Documentation & Training** | Extensive markdown docs, runbooks, agent instructions. | Large reuse; reorganise to match phases. | Update architecture docs, create operator handbook, ADR catalogue for new decisions. |

Risks & external dependencies identified during the analysis are tracked in §4.

---

## 1. Delivery Roadmap

### Phase 0 – Discovery & Foundations (2 weeks)
- **Objectives:** Finalise architecture, IaC baseline, compliance requirements, UX guardrails.
- **Key Deliverables:** ADR set (API-first, event bus, SDK layering, data versioning); updated threat model; environment matrix; UX prototypes.
- **Quality Gates:** ADR approvals; Terraform/Helm skeletons execute `plan`; UX flows signed off; backlog with owners and acceptance criteria.
- **Artefacts:** `docs/architecture/adr/00x-*`, `docs/security/threat-model-vnext.md`, `infra/terraform/modules/*`, UX assets in `docs/product/ux/`.

### Phase 1 – Platform & SDK Backbone (4 weeks)
- **Objectives:** Ship FastAPI service (`apps/service/api`), shared SDK (`hotpass/sdk`), SSO/RBAC, Prefect 3 foundation, developer bootstrap.
- **Key Deliverables:** `/health`, `/readiness`, `/metrics`, `/whoami` endpoints; generated OpenAPI/SDK; OIDC integration with CLI device flow; Prefect 3 work pools; `make bootstrap`.
- **Quality Gates:** API & SDK tests green in CI; CLI/MCP authenticate via SDK; Prefect flows triggered through API in Docker compose; bootstrap completes in <15 minutes.
- **Artefacts:** `dist/api/openapi.json`, `hotpass/sdk`, updated `deploy/docker/docker-compose.yml`.

### Phase 2 – Data & Lineage Core (4 weeks)
- **Objectives:** Implement schema registry, data contracts, lineage facet v3, provenance ledger, GDPR-ready lakehouse.
- **Key Deliverables:** `/contracts` API, contract registry, output validation hooks, enhanced lineage facets (dataset version, column hash, profile metadata), `/lineage` & `/lineage/events` APIs, provenance ledger (Delta/Iceberg).
- **Quality Gates:** Pipelines fail on contract violations; lineage events validate against OpenLineage; provenance queries accessible via API; automated PII scanning integrated.
- **Artefacts:** `docs/reference/data-contracts.md`, lineage dashboards, `docs/compliance/provenance-ledger.md`.

### Phase 3 – Orchestration Services & Automation (4 weeks)
- **Objectives:** Build runs/research APIs, refactor CLI/MCP to SDK, expand agent toolkit, harden async workers.
- **Key Deliverables:** `POST /runs/*`, `GET /runs`, webhook/event bus integrations; `/research/plans`, `/research/crawl`; agent adapter supporting LangGraph, CrewAI, SmolAgents, LlamaIndex; distributed task queue with retries and DLQs.
- **Quality Gates:** Contract tests enforce API usage from CLI/MCP; research runs emit audit traces; agent panel/API show tool-call histories; resiliency tests survive worker/network failures.
- **Artefacts:** `docs/agent-integration.md`, event schema catalogue, load/resilience test reports.

### Phase 4 – Experience & Governance (4 weeks)
- **Objectives:** Deliver Control Center, Lineage Explorer v2, Run timeline, Admin governance console, CLI status tooling.
- **Key Deliverables:** Real-time deployments/events UI with automation actions, version-aware lineage graph, HIL timeline with exports, LLM router management, policy editor, CLI `hotpass status|telemetry|governance`.
- **Quality Gates:** Playwright/Cypress UX suite passes; accessibility (WCAG AA) validated; LLM fallback chain observable; policy edits audited via API/CLI and require approvals.
- **Artefacts:** Updated operator guide, recorded training walkthrough, MCP/CLI documentation refresh.

### Phase 5 – Operations, Compliance & Resilience (3 weeks)
- **Objectives:** Complete observability stack, security hardening, compliance automation, cost/performance optimisation.
- **Key Deliverables:** Prometheus/Grafana dashboards, OTEL tracing, incident runbooks, secrets rotation plan, signed container attestations, POPIA/GDPR evidence binder, data subject request automation, scaling policies.
- **Quality Gates:** Chaos/DR drills documented; security scans clean; compliance checklist signed; SLOs met (>99.5% availability, <400 ms p95 latency).
- **Artefacts:** `docs/operations/runbooks/*`, compliance binder (`dist/compliance`), incident playbooks.

### Launch Gate (2 weeks)
- **Exit Criteria:** All surfaces operate via shared SDK; observability and alerting live; security/compliance approvals complete; documentation and training finished; go-live checklist signed.
- **Launch Artefacts:** Release notes, go-live checklist, 30/60/90 day monitoring plan, adoption metrics baseline.

---

## 2. Cross-Cutting Programmes

1. **Architecture Governance** – Bi-weekly council, ADR backlog, automated architecture docs build.  
2. **Quality Engineering** – Test pyramid (unit, contract, integration, resilience, performance) with test data management service and nightly regression.  
3. **Developer Experience** – Remote dev containers, `make bootstrap`, Taskfile, contribution playbook refresh, Codespaces config.  
4. **Change Management** – Feature flags (Unleash/LaunchDarkly), rollout/rollback playbooks, communication plan.  
5. **Security & Compliance Ops** – OPA policy lifecycle, secrets governance (Vault/SM), audit log review cadence, retention automation.  
6. **Community & Support** – Champions programme, office hours, feedback intake feeding backlog, knowledge base (#support-hotpass).

---

## 3. Risks & Dependencies

| Risk / Dependency | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| **Prefect 3 migration & licensing** | Medium | High | Stage migration in Phase 1 pilot environment; maintain Prefect 2 fallback until Phase 3 hardening. |
| **OIDC / Auth provider procurement** | Medium | High | Engage Security early; prototype with Keycloak locally; confirm production IdP contract during Phase 0. |
| **Event bus selection & ops** | Medium | Medium | Evaluate NATS vs. Redpanda during Phase 0; include cost/perf benchmarks; ensure ops playbooks ready by Phase 3. |
| **Marquez & lineage volume** | Low | Medium | Stress-test lineage facets Phase 2; scale Postgres; archive old events to lakehouse. |
| **LLM provider quotas** | Medium | Medium | Implement router fallback (Groq → OpenRouter → HF → Local); monitor via telemetry; negotiate enterprise quotas. |
| **Team bandwidth & skill ramp** | Medium | Medium | Secure dedicated squads per phase; schedule training on FastAPI, Prefect 3, OPA, OTEL. |
| **Compliance sign-off (POPIA/GDPR)** | Medium | High | Engage compliance liaisons Phase 0; maintain evidence binder; plan audits in Phase 5. |

---

## 4. Immediate Next Steps
1. Circulate this blueprint to leadership, Platform/Ops, Compliance, Data Quality, and Agent stakeholders for sign-off.
2. Create Phase 0 epic with decomposed tasks (ADRs, threat model update, IaC skeleton, UX prototypes) and assign owners/dates.
3. Stand up programme tooling: roadmap board, architecture hub, release calendar, documentation workspace.
4. Launch procurement/approval threads for OIDC provider, event bus, observability stack, and any managed services.
5. Schedule cross-team kickoff to align on roles, communication cadence, and success metrics before Phase 0 sprint start.

Once Phase 0 artefacts are approved, delivery proceeds sequentially through phases 1–5, culminating in the launch gate and post-launch monitoring plan. No downstream work should begin without passing earlier phase gates.
