# Marquez docker-compose stack

Run `make marquez-up` from the repository root (or `docker compose up` from this
directory) to start a local Marquez instance backed by PostgreSQL. Stop the
stack with `make marquez-down` when finished. If ports `5000` or `3000` are
occupied, override them with `MARQUEZ_API_PORT` and `MARQUEZ_UI_PORT`:

```bash
make MARQUEZ_API_PORT=5500 MARQUEZ_UI_PORT=3500 marquez-up
```

The [Marquez lineage UI quickstart](../../docs/observability/marquez.md) documents
usage and configuration details.
