# Marquez docker-compose stack

Run `make marquez-up` from the repository root (or `docker compose up` from this
directory) to start a local Marquez instance backed by PostgreSQL. Stop the
stack with `make marquez-down` when finished. Override the default ports (API
`5000`, UI `3000`) by exporting `MARQUEZ_API_PORT` and `MARQUEZ_UI_PORT` when a
conflict occurs:

```bash
MARQUEZ_API_PORT=5500 MARQUEZ_UI_PORT=3500 make marquez-up
```

The [Marquez lineage UI quickstart](../../docs/observability/marquez.md)
documents usage and configuration details.
