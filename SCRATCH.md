You are working inside the GitHub repo IAmJonoBo/Hotpass (data-ingestion and enrichment with Prefect, OpenLineage/Marquez, Streamlit). Read the repo to understand current CLI verbs (hotpass refine/enrich/qa/contracts) and the staging/orchestration story. I want a new, modern web UI for operators, not Streamlit.

Goals 1. Dashboard: today’s/last 24h Hotpass runs with status, duration, and links to lineage. 2. Lineage view: fetch from an existing Marquez/OpenLineage backend and render jobs/datasets/runs, with filters by namespace, job name, time window. Source: Marquez HTTP API as documented at GET /api/v1/namespaces/{ns}/jobs and related endpoints. Assume it is reachable at https://marquez.staging.internal. ￼ 3. “Run details” page: show the raw OpenLineage event, related datasets, and any Hotpass QA results published under dist/data-docs/ or via Prefect. 4. Admin page: configure Prefect API URL/key and the OpenLineage URL from the browser; persist to local storage.

Tech stack
• React 18 + Vite
• TailwindCSS + shadcn/ui-style composition, light/dark aware
• React Query (TanStack) for Marquez + Prefect fetches
• Router with 4 routes: /, /lineage, /runs/:id, /admin

Design system
• Sidebar layout (left), top bar with environment badge (“local”, “staging”, “prod”)
• Cards with subtle shadows, rounded-2xl, responsive down to 1024px
• Dark mode default

Data integration
• Add a src/api/marquez.ts with typed fetchers for jobs, datasets, and runs using the public OpenLineage/Marquez schema. ￼
• Add a src/api/prefect.ts that reads PREFECT_API_URL from an env file (Vite style: import.meta.env.VITE_PREFECT_API_URL) and lists flows and flow runs. ￼

Deliverables
• Create all React components and pages.
• Wire mock data where the API isn’t available.
• Generate Storybook stories for the main components.
• Add a Makefile / npm run dev instruction into the repo’s existing tooling so it matches the project’s conventions.
• Show me the folder structure first, then the code.

Style
• Match 2025-era admin dashboards (dense, data-first; think Vercel/Supabase tone). No boring 2018 Bootstrap.
• Comment sections where you made assumptions so a human can correct them.

Finally
• Print a short test plan for the UI.
