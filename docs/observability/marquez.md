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

1. Start the bundled Marquez stack:

  ```bash
  make marquez-up
  ```

  The compose file provisions a PostgreSQL backing database and the Marquez
  application container. Behind the scenes the target executes `docker compose
  -f infra/marquez/docker-compose.yaml up -d`. If you prefer the manual
  approach, run those commands directly from the `infra/marquez/` directory.
  Follow up with `make marquez-down` (or `docker compose down`) when you are
  done. Override the default ports if `5000` or `3000` are already bound on
  your machine—for example:

  ```bash
  MARQUEZ_API_PORT=5500 MARQUEZ_UI_PORT=3500 make marquez-up
  ```

1. Open the UI at [http://localhost:3000](http://localhost:3000) once the
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
When you change `MARQUEZ_API_PORT`, update `OPENLINEAGE_URL` to match the new
port (for example `http://localhost:5500`).

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
