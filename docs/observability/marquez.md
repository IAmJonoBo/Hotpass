---
title: Marquez lineage UI quickstart
summary: Run Marquez locally to inspect the OpenLineage events emitted by Hotpass.
last_updated: 2025-12-02
---

The Hotpass pipeline now emits OpenLineage events from the CLI and Prefect
execution paths. Marquez provides a lightweight UI for browsing those events and
verifying dataset relationships end-to-end. This guide walks through running the
stack locally with Docker Compose.

## Prerequisites

- Docker and Docker Compose installed locally.
- Ports `3000` (UI) and `5000` (OpenLineage API) available on your machine.

## Start Marquez

1. Navigate to the bundled infrastructure assets:

   ```bash
   cd infra/marquez
   docker compose up
   ```

   The compose file provisions a PostgreSQL backing database and the Marquez
   application container. Logs will stream to the terminal until you stop the
   stack with `Ctrl+C` or `docker compose down`.

2. Open the UI at [http://localhost:3000](http://localhost:3000) once the
   containers report `healthy`.

## Configure Hotpass to emit to Marquez

Hotpass will automatically emit lineage whenever the `openlineage` client is
available. Point the emitter at your local Marquez instance by exporting these
variables before running the CLI or Prefect flows:

```bash
export OPENLINEAGE_URL="http://localhost:5000"
export HOTPASS_LINEAGE_NAMESPACE="hotpass.local"
```

The namespace defaults to `hotpass.local` if unset. Set
`HOTPASS_LINEAGE_PRODUCER` to override the producer URI advertised in events.

Run a pipeline execution (for example `uv run hotpass run --log-format json ...`)
and refresh the Marquez UI to explore the captured datasets, jobs, and runs. The
UI surfaces the same events validated by the automated lineage integration
tests.

## Troubleshooting

- **No events appear:** confirm `OPENLINEAGE_URL` points to the running Marquez
  instance and that `HOTPASS_DISABLE_LINEAGE` is not set to `1`.
- **Port conflict:** update the exposed ports in
  [`infra/marquez/docker-compose.yaml`](../../infra/marquez/docker-compose.yaml)
  and restart the stack.
- **Resetting state:** run `docker compose down -v` from `infra/marquez/` to
  remove the PostgreSQL volume before starting fresh.
