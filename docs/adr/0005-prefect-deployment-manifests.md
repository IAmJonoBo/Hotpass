# ADR-0005: Prefect deployment manifests and CLI workflow

**Status:** Accepted

**Date:** 2025-10-29

## Context

Hotpass previously registered Prefect deployments by calling `flow.to_deployment()` imperatively from the CLI. The approach had
several shortcomings:

1. Deployment metadata (schedules, tags, work pools, parameters) lived in code rather than version-controlled manifests.
2. The CLI could only deploy a single flow at a time and did not support idempotent re-registration when metadata changed.
3. Incremental and backfill parameters were not encoded consistently, making resumable runs brittle.
4. Documentation could not point to canonical deployment definitions, complicating reviews and audits.

## Decision

We introduced manifest-driven deployments and a revamped `hotpass deploy` command:

1. **Manifest directory** — Each flow has a dedicated YAML file under `prefect/` describing the `RunnerDeployment`. Refinement
   deployments set `incremental: true` and expose `since` for resumable runs; backfill manifests enable `backfill: true` and
   default to a paused schedule (`active: false`).
2. **Deployment loader** — `hotpass.prefect.deployments` reads the manifests, validates their structure, and renders
   `RunnerDeployment` models using Prefect's runner API. The loader guards against missing parameters and enforces that schedules
   carry explicit timezone and activation flags.
3. **Idempotent CLI** — `hotpass deploy` now accepts `--flow`, `--manifest-dir`, `--build-image`, and `--push-image` flags. It
   applies one or more manifests in a single invocation and returns the Prefect deployment IDs.
4. **Test coverage** — New tests validate manifest presence, parameter defaults (including resumable options), and Prefect model
   construction. Deployments are skipped when Prefect is unavailable.
5. **Documentation updates** — How-to guides, CLI reference material, and a dedicated deployment management guide document the
   workflow.

## Consequences

### Positive

- Deployments are declarative, reviewable, and auditable via Git history.
- Incremental and backfill parameters are encoded consistently, enabling resumable runs without ad-hoc overrides.
- Teams can re-register deployments safely; re-running the CLI updates existing deployments without duplication.
- Documentation now points to canonical manifests, improving onboarding and operations hand-offs.

### Neutral

- Contributors must update YAML manifests when changing deployment metadata.
- The CLI exposes additional flags, which slightly increases the help surface.

### Negative

- The manifest loader depends on Prefect's runner API; breaking changes in Prefect may require adjustments.
- Local environments without Prefect installed cannot validate manifests end-to-end, though tests guard against regressions.

## Alternatives considered

1. **Keep imperative deployment code** — Rejected because it hides changes in Python diffs and complicates reviews.
2. **Generate manifests from code** — Rejected to keep deployment metadata readable and editable by operations teams.
3. **Adopt Prefect's `prefect.yaml` exclusively** — Rejected to allow multiple environment overlays and finer-grained manifests.

## References

- `src/hotpass/prefect/deployments.py`
- `prefect/refinement.yaml`
- `prefect/backfill.yaml`
- `docs/how-to-guides/manage-prefect-deployments.md`
