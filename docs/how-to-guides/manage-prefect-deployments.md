---
title: How-to — manage Prefect deployment manifests
summary: Version, review, and apply Prefect deployment manifests for Hotpass flows.
last_updated: 2025-10-31
---

This guide explains how to work with the manifest-based Prefect deployment workflow introduced in October 2025.

## Understand the manifest layout

Hotpass stores Prefect deployment definitions as YAML files under `prefect/`. Each file contains a single
`RunnerDeployment` specification with the following canonical fields:

- `id`: Stable identifier used by the CLI (`--flow`).
- `flow`: Import path for the Prefect flow (for example, `hotpass.orchestration:refinement_pipeline_flow`).
- `schedule`: Cron, interval, or RRULE metadata encoded via the `kind` and `value` keys. `active: false` automatically pauses
  the deployment during registration.
- `parameters`: Default parameters passed to the flow. Refinement deployments set `incremental: true` and expose `since` so
  you can resume incremental runs. Backfill manifests toggle `backfill: true` and disable `incremental`.
- `work_pool`: Prefect work pool target. Use separate directories (for example, `prefect/prod/`) when environments require
  different pools.

## Apply a manifest

Register one or more deployments by pointing the CLI at the manifest directory. The command is idempotent—re-running it updates
existing deployments without duplicating them.

```bash
uv run hotpass deploy --flow refinement
```

To register multiple flows, repeat the `--flow` flag:

```bash
uv run hotpass deploy --flow refinement --flow backfill
```

### Override the manifest directory

When you maintain overlays for dev/staging/prod, pass `--manifest-dir`:

```bash
uv run hotpass deploy --manifest-dir prefect/prod --flow refinement
```

The CLI merges the directory contents, so keep only the manifests you want registered in each overlay.

### Build and push images on demand

By default Hotpass skips Prefect's image build pipeline because the flows run from the checked-out repository. If your
environment requires a container image, enable the toggles:

```bash
uv run hotpass deploy --flow refinement --build-image --push-image
```

## Update manifests safely

1. Edit the relevant YAML file under `prefect/` and run `uv run hotpass deploy --flow <id>` to apply the change.
2. Commit both the manifest and any documentation updates. Automated tests load the manifests and ensure they stay
   parseable, include incremental/backfill parameters, and build valid Prefect models.
3. Capture significant structural changes in an ADR so the deployment history remains auditable.

## Resume incremental runs

The refinement manifest exposes a `since` parameter. Override it when you need to resume from a checkpoint:

```bash
uv run prefect deployment run hotpass-refinement --params '{"since": "2024-11-01"}'
```

Prefect records the new parameter defaults, and subsequent scheduled runs continue from the supplied date unless the
manifest is re-applied.

## Scale workers and monitor health

- **Shared work pool** — Provision a single Prefect work pool (for example `hotpass-shared-workers`) and register multiple
  workers against it. Allocate at least one Linux worker for production flows and one macOS/Linux worker for parallel test
  execution. Co-locating workers in the same pool lets Prefect schedule refinement, enrichment, and QA flows concurrently.
- **Autoscaling** — Configure workers with Prefect's `prefect worker start --limit` flag or container orchestrator autoscaling
  so the pool can expand when you queue parallel backfill or test runs. Keep worker limits aligned with downstream rate-limit
  policies defined in Hotpass profiles.
- **Health checks** — Enable Prefect worker heartbeats (`PREFECT_WORKER_HEARTBEAT_SECONDS`) and monitor them via Prefect Cloud
  or the self-hosted UI. Treat worker offline events as a gating alert because orchestrated pipelines rely on parallel
  capacity to meet SLAs.
- **Environment parity** — Build workers from the same base image/environment as CI (`uv` + Hotpass extras) so test, staging,
  and production executions behave consistently. Run `make sync` within the worker bootstrap to align dependency extras.

## CI and local test cadence

- Run `make qa`, `uv run hotpass qa all`, and `uv run pytest -n auto` locally before pushing changes. These commands mirror
  production CI and exercise the Prefect manifests, orchestration flows, and assert migrations.
- In CI, ensure the quality-gates workflow executes the same trio to maintain parity. When Prefect workers are available in
  the shared pool, you can trigger orchestration QA (`uv run hotpass qa ta`) concurrently with the unit test matrix.

## Stage backfill guardrail rehearsals

The release preflight requires a staged backfill rehearsal. Once staging access is restored:

1. Apply the staging manifest overlay if needed (`uv run hotpass deploy --manifest-dir prefect/staging --flow backfill`).
2. Trigger the backfill deployment via Prefect (`uv run prefect deployment run hotpass-backfill --params '{"since": "<date>"}'`).
3. Export artefacts to `dist/staging/backfill/<timestamp>/`:
   - `prefect.log` — Prefect flow log export.
   - `summary.json` — key guardrail metrics (concurrency limits, QA outcomes, dataset counts).
   - `cli.sh` — commands executed during the rehearsal for audit parity.
4. Link the artefacts in `docs/operations/staging-rehearsal-plan.md` and `Next_Steps.md` to unblock programme sign-off.

Document any access blockers in `Next_Steps_Log.md` so the programme manager can reschedule the rehearsal window.
