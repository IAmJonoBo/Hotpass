---
title: How-to — manage Prefect deployment manifests
summary: Version, review, and apply Prefect deployment manifests for Hotpass flows.
last_updated: 2025-10-29
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
