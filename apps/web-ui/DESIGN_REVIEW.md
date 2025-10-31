# Hotpass Web UI – Remaining Action Items (2025-10-31)

_Objective: keep only actionable follow-ups for the final UI push. Everything listed below requires a new task, Jira ticket, or PR before release._

## 1. Experience Gaps

- [ ] Add lineage graph visualization (react-flow) on the Lineage page for visual traceability.
- [ ] Implement real-time or periodic auto-refresh on the dashboard once new runs complete (WebSocket or polling toggle).
- [ ] Replace “Loading…” placeholders with skeleton loaders for tables, cards, and detail panes.
- [ ] Surface API failure banners outside the Admin page when the app falls back to mock/offline data.
- [ ] Promote toast or inline error messaging instead of console-only logging for user-visible failures.
- [ ] Extend connection status indicator so it is visible from the dashboard header, not just the Admin page.

## 2. Accessibility & Responsiveness

- [ ] Run a full WCAG 2.1 AA audit (ARIA roles, focus order, keyboard traps, screen reader labels) and capture findings.
- [ ] Strengthen focus outlines and contrast tokens for both light and dark themes.
- [ ] Validate zoom/viewport scaling up to 200% and document fixes.
- [ ] Produce a responsive-table strategy for sub-1024px viewports (horizontal scroll hints or stacked cards).

## 3. Human-in-the-Loop Workflow

- [ ] Introduce approval/hold/reject controls on the Run Details page with audit logging.
- [ ] Add comment/annotation threads for QA findings and lineage anomalies.
- [ ] Provide a data review workspace that lets operators adjust/refine single records and push changes back to Hotpass.
- [ ] Design conflict-resolution UI for competing enrichment results.
- [ ] Wire notification/alert surface (email, webhook, or in-app banner) for pending approvals.

## 4. Collaboration & Communication (Backlog)

- [ ] Spike a lightweight “notes/chat” sidebar linked to runs to satisfy the original chat-box requirement.
- [ ] Define keyboard shortcut map (⌘K palette, navigation keys) and ship at least the global command palette.

## 5. Security & Compliance

- [ ] Add authentication + role-based authorization in front of the UI (Okta/Cognito/SSO TBD).
- [ ] Apply rate limiting or circuit breakers to API calls initiated from the UI.
- [ ] Sanitize/encode all user-supplied inputs before rendering or forwarding to APIs.
- [ ] Set CSP headers, explicit HTTPS redirects, and integrate with the platform’s TLS posture.

## 6. Performance & Observability

- [ ] Optimize and document image/static asset delivery (SVG sprites, lazy loading if we add charts).
- [ ] Publish performance budgets (bundle size, Largest Contentful Paint target) and add CI guardrails.
- [ ] Ship telemetry hooks (analytics + error tracking) that respect Hotpass data policies.

## 7. Documentation & QA

- [ ] Update README/Storybook to cover new interaction patterns (skeletons, toasts, approvals).
- [ ] Add E2E tests (Playwright or Cypress) for the dashboard, lineage graph, and approval workflow.
- [ ] Capture accessibility test scripts and results in `docs/how-to-guides/agentic-orchestration.md` once the audit completes.

---

## Staged Copilot Implementation Prompt

You are enhancing the Hotpass web UI delivered in PR #150. The stack is React 18 + Vite + TypeScript + Tailwind + shadcn/ui with pages under apps/web-ui/src/pages and shared components in apps/web-ui/src/components. Preserve Layout.tsx and Sidebar.tsx structure, existing design tokens, rounded-2xl styling, and dark-mode support. Work inside apps/web-ui unless the stage calls out additional paths. Maintain lint/test standards, update Storybook, and document each new capability. After each stage, show the refreshed folder tree and diffs for the files you touched.

### Stage 0 – Prep

1. Run lint/tests/Storybook baselines to capture current state.
2. Confirm Prefect and Marquez clients exist in src/api/prefect.ts and src/api/marquez.ts.
3. Review src/components/ui/table.tsx for table primitives and Storybook setup.

### Stage 1 – Agent assistant console

1. Add a /assistant route rendering a chat console anchored to the bottom of the page with message bubbles, timestamps, and a telemetry footer (“last poll from Prefect…”, “lineage source: Marquez”, “current environment: …”).
2. Provide a right-hand drawer accessible from any page that opens the assistant; integrate with Layout.tsx and Sidebar.tsx.
3. Create src/agent/tools.ts exporting:
   - listFlows → wraps Prefect client.
   - listLineage(namespace) → wraps Marquez client.
   - openRun(runId) → navigates to /runs/:id.
4. Allow chat messages to trigger these tools and show a “what just happened” note under the input describing the most recent tool call.
5. Stub reasoning with an in-memory array/state—no backend extension.
6. Keep styling aligned with the existing UI.
7. Add Storybook coverage for the chat/assistant component (light/dark modes).

### Stage 2 – Human-in-the-loop approvals

1. In Dashboard.tsx, add a “HIL status” column with badges (none, waiting, approved, rejected).
2. In RunDetails.tsx, add a slide-over panel showing run metadata, lineage link, QA results, and actions: “Approve and continue downstream tasks” and “Reject and open chat with agent”.
3. Implement approveRun(runId: string) in src/api/prefect.ts (mock resolve) and call it on approve.
4. On reject, launch the Stage 1 chat drawer prefilled with “Explain why run {id} failed QA and propose remediation.”
5. Track approvals/rejections in a hilAudit store (React Query or Zustand) and surface operator history.

### Stage 3 – Dockerized hub

1. Create deploy/docker/docker-compose.yml running hotpass-web (build from apps/web-ui/), marquez (official image), and prefect (lightweight server/worker).
2. Network containers so the UI hits <http://marquez:5000/api/v1> and <http://prefect:4200/api>.
3. Update apps/web-ui/README.md with:
   docker compose -f deploy/docker/docker-compose.yml up --build
    then browse [http://localhost:3001](http://localhost:3001)
4. Add an environment banner in the UI header sourced from VITE_ENVIRONMENT indicating Docker vs remote.
5. Integrate new commands into the Makefile from PR #150 (mirror make web-ui-dev, make marquez-up flows).

### Stage 4 – Live refinement panel

1. On Dashboard.tsx, insert a live refinement table between KPI cards and the assistant console.
2. Table lists the last 50 refined rows (mock data): source, entity, status, refined_at, notes.
3. Include a feedback icon per row that expands a mini textarea under the chat box (“Operator feedback on row {id}: …”).
4. Mock POSTs to /telemetry/operator-feedback in the browser.
5. Add caption “Telemetry: {pending backfills} pending backfills · last sync {n}s ago · source: Marquez namespace=hotpass”, refreshing every 10–15 seconds via src/api/marquez.ts polling.
6. Ensure responsive behaviour (≥1024px optimized, mobile tolerant).
7. Document this feature here as “live view refinement”.

### Stage 5 – Telemetry strip

1. Build src/components/TelemetryStrip.tsx and render it on Dashboard, Lineage, RunDetails, and Admin.
2. Strip displays current environment (Admin settings), whether the agent is executing a tool (/assistant state), timestamp of last Prefect poll, and number of failed runs in the last 30 minutes.
3. Use React Query with existing clients; keep visuals compact (≤2 lines).
4. Provide an Admin toggle to enable/disable the strip.
5. Update Storybook for the strip.

### Stage 6 – Power tools launcher

1. Add a “Power Tools” panel (sidebar or top-right button).
2. Buttons surface:
   - Start Marquez locally → show `make marquez-up`.
   - Run demo pipeline → show `uv run hotpass refine --input-dir ./data --output-path ./dist/refined.xlsx`.
   - Open lineage page → navigate to `/lineage`.
   - Open agent/chat console → open `/assistant`.
3. Display the underlying CLI command with each action.
4. Grey out items when running inside Docker (use environment banner logic).

### Stage 7 – UX transparency red-team

1. Add explanatory loading text (“Fetching flow runs from Prefect… (over VPN/bastion this may be slow).”).
2. Warn on /admin when the configured endpoint is a private VPC URL; recommend the bastion tunnel.
3. Add “last updated” timestamps to all data tables.
4. Create an “Agent activity” side panel listing the last 10 agent actions (tool calls, approvals, etc.).
5. Update apps/web-ui/TEST_PLAN.md with tests covering the transparency features.

### Stage 8 – Finalization

1. Re-run lint/tests/Storybook build; capture results.
2. Show updated folder structure and diffs for every touched file.
3. Summarize the new capabilities, outstanding TODOs, and testing performed.
