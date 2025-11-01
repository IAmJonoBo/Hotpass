Hotpass vNext — Implementation Brief for Codex

Mission

Build a production-grade, OSS-first data/AI control plane that fuses:
• Prefect 3 event-driven orchestration and automations, including deployments and webhooks. ￼
• OpenLineage/Marquez lineage with custom, Hotpass-specific facets for dataset/version/column and research flags. ￼
• GitHub Actions Runner Controller (ARC) for secure, multi-tenant, K8s-backed CI, including multi-org patterns. ￼
• MCP as the universal agent/tool bus so Codex, Claude, Copilot Spark, etc. can drive Hotpass over one contract. ￼

Every surface (API, CLI, UI, MCP) must consume the same typed SDK and the same event bus (Redpanda default; NATS via feature flag).

⸻

Global tenets 1. Experience Parity: no UI-only or CLI-only paths; everything is an API call described in OpenAPI and exposed as MCP tools. 2. Contract-Driven: OpenAPI, JSON/Avro schemas, OpenLineage facets, and OPA bundles are authored first; code is generated from them. 3. Secure-by-Construction: OIDC → JWT → RBAC (Operator, Analyst, Auditor, Admin); OPA check on sensitive routes; full audit log. 4. Observability as a Feature: OpenTelemetry tracing from UI/CLI → FastAPI → Prefect → workers → Marquez; dashboards must ship. ￼ 5. Compliance First-Class: POPIA/GDPR retention and provenance ledger are regular features, not post-launch. 6. Automate the Golden Path: make bootstrap / uv run hotpass setup brings up the whole stack locally (API, UI, Prefect 3, Marquez, ARC, LLM router).

⸻

Target stack
• Experience: React 18 + Vite, shadcn-style components, React Query, React Flow for lineage, Playwright tests.
• Services: FastAPI (apps/service/api), gRPC/worker layer, Prefect 3 work pools, Celery/RQ.
• Data Plane: Lakehouse (Delta/Iceberg), contract registry, Marquez, provenance ledger.
• Platform: Docker/K8s, Terraform/IaC, Redpanda, OPA, Keycloak/Auth0, Prometheus/Grafana.

⸻

Phase 0 — Discovery & Foundations

Objectives
• Freeze domain model and contracts.
• Align security/compliance.
• Produce UX foundations so UI stays in lockstep.

Tasks 1. Architecture ADRs: API-first; Redpanda as default; NATS via feature flag; shared SDK layout. ￼ 2. Env blueprint: local, CI, staging, prod; each must be runnable via compose. 3. Security+Compliance: POPIA/GDPR control list; audit artefacts; threat model. 4. Product/UX charter: wireframes for:
• Control Center
• Lineage Explorer v2
• Run Details timeline
• Admin (LLM+Policy)
• Agent Console

Quality gates
• ADR bundle approved.
• Terraform/Helm skeleton plan succeeds.
• UX prototypes signed-off.
• Backlog created with acceptance criteria.

⸻

Phase 1 — Platform, SDK & Experience Shells

Objectives
• Ship the core API + generated SDK.
• Align auth/RBAC across API, CLI, MCP.
• Prove Prefect 3 integration.
• Render the first, thin UI.

Tasks 1. API & SDK
• FastAPI app with /health, /readiness, /metrics, /whoami.
• Generate dist/api/openapi.json and hotpass.sdk (Python/TS). 2. Auth & RBAC
• OIDC (Auth0/Azure AD/Keycloak) → JWT → roles: Operator, Analyst, Auditor, Admin.
• CLI and MCP use device-code / PAT with scopes. 3. Prefect 3 alignment
• Stand up Prefect 3 work pools; flows for refine/enrich/backfill/QA.
• API routes schedule flows, not run them inline. ￼ 4. Developer experience
• make bootstrap / uv run hotpass bootstrap → uv, npm, terraform init, docker compose up.
• Pre-commit, mypy/ruff, CI skeleton (GitHub Actions). 5. Experience shells (critical)
• React app with: top navigation, telemetry strip (Prefect/Marquez/ARC/LLM), Control Center skeleton reading /health+/whoami.
• CLI: hotpass status, hotpass whoami.
• MCP: expose /health and /whoami as MCP tools so Codex can call them. ￼

Quality gates
• CI runs API+SDK tests.
• SSO in UI and CLI, RBAC enforced.
• docker compose up runs API + Prefect 3 + Marquez.
• Shell UI shows VPN/bastion guidance if backends unreachable.

⸻

Phase 2 — Data & Lineage Core with UI Preview

Objectives
• Make lineage, contracts, and provenance real.
• Prove column-level + custom facets in Marquez.
• Feed UI while contracts are still warm. OpenLineage recommends facets for extension. ￼

Tasks 1. Data contracts & schema registry
• Define canonical JSON/Avro for inputs, refined outputs, enriched datasets.
• /contracts API + CLI hotpass contracts emit.
• CI rejects contract mismatches. 2. Lineage Facet v3
• Emit dataset version, column lineage facet, pipeline config hash, research flags. ￼
• Store in Marquez and on the event bus. ￼
• Websocket /lineage/events. 3. Provenance ledger
• Append-only (Delta/Iceberg) recording workbook hash, operator, pipeline version, POPIA/GDPR retention signals. 4. Data storage & retention
• data/lake/{bronze,silver,gold}/…
• GDPR delete → audit artefact. 5. Experience tie-ins
• Lineage Explorer preview: version-aware toggle, basic graph via React Flow, “Explain this gap” stubbed to agent.
• Show column names where available (Marquez column facet). ￼

Quality gates
• Lineage events validate against OpenLineage spec. ￼
• Marquez shows new facets.
• UI preview consumes /lineage via SDK, not ad-hoc fetch.
• Contract-fail in CI blocks merge.

⸻

Phase 3 — Orchestration, Agents, ARC Broker

Objectives
• Expose the orchestration surface.
• Make Hotpass agent-native (MCP-first).
• Solve ARC multi-tenant, per GitHub community gap. ￼

Tasks 1. Runs & Jobs API
• POST /runs/{refine|enrich|qa|contract}
• GET /runs/{id}, GET /runs?status=…
• Webhook callbacks + event bus notifications. ￼ 2. Research/crawl orchestrator
• Deterministic first; networked only when policy allows.
• /research/plans, /research/crawl. 3. Agent toolkit & MCP
• agents/tools.json listing all tools (prefect, lineage, runs, arc, contracts, telemetry).
• Adapter for LangGraph, CrewAI, SmolAgents, OpenAI Agents SDK, Claude MCP. ￼
• /agent/activity API writing tool traces to event bus (for replay and UI). 4. ARC broker service
• Service that holds multiple GitHub App creds and emits per-tenant ARC config.
• Expose /arc/tenants, /arc/runners, /arc/audit.
• Follow current multi-org ARC discussions. ￼ 5. Reliability
• Celery/RQ worker pools, retries, DLQs.
• Health dashboards.

Experience work (same phase)
• Agent Console page: chat, tool list, tool traces.
• CI/ARC page: tenant badges, runner health, last reconcile.

Quality gates
• Every tool in agents/tools.json callable via MCP.
• Agent Console shows tool, args, ts for each action (matches MCP spec 2025-03-26). ￼
• kubectl get runners shows ≥2 tenants in demo cluster.
• Chaos (kill worker) recovers >99%.

⸻

Phase 4 — Experience & Governance (4 weeks)

Objectives
• Deliver the “frontier” UX that makes everything legible.
• Add admin, policy, and audit surfaces.

Tasks 1. Control Center UI
• Tabs: Deployments, Events, Automations.
• Real-time updates (15s) from event bus.
• Offline state: VPN/bastion guidance ≤30 words. 2. Lineage Explorer v2
• React Flow graph
• Version-aware toggle
• Column-level diff
• Inline agent “Explain this gap”, shows tool trace.
(This compensates for Marquez’s current column-view limits.) ￼ 3. Run Details timeline
• HIL trail, artefact links, compliance badges, dataset preview. 4. Admin & Governance console
• LLM router manager (Groq → OpenRouter → HF → Local) with fallback log. ￼
• OPA bundle editor, secrets, audit viewer. 5. CLI enhancements
• hotpass status, hotpass telemetry, hotpass governance.

Quality gates
• Playwright/Cypress covers Control, Lineage v2, Run Details, Admin.
• WCAG AA passes.
• LLM fallback visible in UI when Groq 429s.
• Policy edits produce audit entries retrievable via UI and CLI.

⸻

Phase 5 — Operations, Compliance, Resilience

Objectives
• Make it supportable and defensible.

Tasks 1. Observability & SRE
• Prometheus/Grafana for API, worker queue depth, Prefect runs, ARC runners.
• End-to-end OpenTelemetry trace (UI → API → worker → Prefect → Marquez). ￼ 2. Security hardening
• Vault/SM, least-privilege IAM, Cosign, SBOM, Trivy, kube-bench. 3. Compliance automation
• POPIA/GDPR evidence binder, DSAR export/delete via API/CLI. 4. Cost & performance
• Benchmarks, autoscaling, LLM router quotas.

Quality gates
• DR drill documented.
• Security scans clean or ticketed.
• SLOs: >99.5% uptime, <400ms p95 API.
• Compliance artefacts in dist/compliance/….

⸻

Launch Gate

Exit criteria
• All surfaces (API, CLI, UI, MCP) call through hotpass.sdk.
• Dashboards green; on-call rehearsed.
• OPA enforced; audit streaming; POPIA/GDPR verified.
• Docs: developer handbook, operator guide, agent playbook, ADR index.
• Training delivered; knowledge base seeded.

⸻

Notes for Codex 1. Default infra: use Docker Compose with Redpanda, Prefect 3, Marquez, API, UI, ARC broker, LLM router; K8s/TF is generated but optional for local runs. 2. Reuse first: if existing Hotpass React components or lineage emitters match the new contracts, wrap them; only rebuild when contracts diverge. 3. MCP everywhere: every new API must add an MCP tool description so Codex/agents can call it. This mirrors current OpenAI MCP guidance. ￼ 4. UI telemetry: never add a page without the bottom strip; that’s how operators see VPN/LLM/ARC state instantly.
