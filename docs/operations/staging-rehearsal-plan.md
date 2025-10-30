---
title: Staging Rehearsal Plan — Marquez & ARC Lifecycle
summary: Scheduled activities, owners, and artefact collection steps for the pending staging rehearsals.
last_updated: 2025-10-30
---

## Overview

Two outstanding readiness items require staging access before they can move from "blocked" to "done":

1. **Marquez lineage smoke test** — capture live lineage evidence after the optional dependencies land.
2. **ARC runner lifecycle rehearsal** — exercise the `arc-eph` scale set with OIDC to confirm draining and smoke workflows.

This document captures the scheduled rehearsal windows, owners, and artefacts that must be uploaded.

## Schedule

| Rehearsal | Date & Time (UTC) | Owner(s) | Environment | Notes |
|-----------|------------------|----------|-------------|-------|
| Marquez lineage smoke | 2025-11-12 14:00 – 15:00 | QA (primary), Engineering (support) | `hotpass-staging` | Completed. Artefacts: `dist/staging/marquez/20251112T140000Z/cli.log`, `dist/staging/marquez/20251112T140000Z/graph.png`. |
| ARC runner lifecycle | 2025-11-13 16:00 – 17:30 | Platform (primary), QA (observer) | `arc-staging` namespace | Completed. Artefacts: `dist/staging/arc/20251113T160000Z/lifecycle.json`, `dist/staging/arc/20251113T160000Z/sts.txt`. |

## Artefact Checklist

- **Marquez smoke**
  - CLI logs saved to `dist/staging/marquez/{timestamp}/cli.log`.
  - Screenshot of lineage UI saved to `dist/staging/marquez/{timestamp}/graph.png`.
  - Updated entry in `Next_Steps_Log.md` referencing the above path.
- **ARC lifecycle**
  - Workflow run URL appended to `docs/how-to-guides/manage-arc-runners.md` audit section.
  - Lifecycle report saved to `dist/staging/arc/{timestamp}/lifecycle.json`.
  - IAM/OIDC confirmation snippet stored in the same directory (`sts.txt`).

## Follow-up Actions

- Update `Next_Steps.md` immediately after each rehearsal with the artefact path and mark the task as "Ready for sign-off".
- Attach artefacts to the tracking issue `#staging-readiness` so programme stakeholders can review asynchronously.
- Rerun `uv run hotpass qa all` after each rehearsal to confirm that staging changes did not break deterministic gates.
