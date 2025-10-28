---
title: Governance — project charter
summary: Mission, personas, guardrails, and governance rhythms for the Hotpass modernisation programme.
last_updated: 2025-10-25
---

Hotpass refines messy spreadsheets into a governed single source of truth. This charter links the programme mission to the personas we serve, the constraints we must respect, and the boundaries we will not cross.

## Mission

- Deliver a governed, industry-ready data refinement pipeline that keeps stakeholders confident in data quality, compliance, and operational readiness.
- Shorten the time from ingesting messy source files to publishing a trustworthy single source of truth.
- Embed observability, documentation, and quality gates so changes ship safely and remain auditable.

## Strategic context

- **Problem statement**: Organisations rely on ad-hoc spreadsheets that duplicate entities, miss compliance rules, and lack observability. Manual cleanup is error-prone and slow.
- **Opportunity**: Hotpass provides configurable validation profiles, enrichment, and orchestration with traceable outputs, enabling faster, repeatable refinement.
- **Value hypothesis**: Teams that standardise on Hotpass will reduce refinement cycle time by 60%, surface compliance issues before downstream systems ingest data, and unlock shared dashboards for operational visibility.

## Personas and needs

| Persona              | Needs                                                                           | Success signals                                                                                     |
| -------------------- | ------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| Data operations lead | Reliable, repeatable pipeline runs with transparent quality reporting.          | Flow runtimes stable, dashboards highlight fewer untriaged failures per release.                    |
| Compliance officer   | Evidence of POPIA adherence, audit-friendly provenance, and redaction controls. | Quality reports flag zero high-severity unresolved compliance issues per run.                       |
| Data engineer        | Extendable pipeline with clear contracts, tests, and observability hooks.       | Onboarding new profiles or connectors requires ≤ 2 PRs and passes automated gates on first attempt. |
| Product analyst      | Self-service access to refined datasets and dashboards.                         | Streamlit dashboard uptime ≥ 99% during business hours, with fresh exports after each pipeline run. |

## Constraints and operating assumptions

- Preserve CLI and Prefect interfaces; downstream teams now use the unified `hotpass` command while the deprecated `hotpass-enhanced` shim delegates for backwards compatibility.
- Optional extras (enrichment, geospatial, dashboards) may not install in restricted CI environments—tests and telemetry must tolerate feature flags.
- Datasets contain POPIA-sensitive information; artefacts must avoid exposing raw PII and respect retention policies.
- Sandbox environments lack outbound internet access; enrichment connectors require controlled fallbacks and cached fixtures.
- Docker image publication workflow remains under construction; deployment guidance assumes manual promotion until CI validation lands.

## “Do-not” boundaries

- Do not break backward compatibility for exported schemas or CLI arguments without a documented migration plan and 2 release windows’ notice.
- Do not ingest or emit datasets without provenance metadata or quality scores.
- Do not enable external telemetry exporters that exfiltrate data outside approved observability endpoints.
- Do not merge changes that bypass automated QA gates (tests, lint, type checks, security scans, docs build) without formal risk acceptance.

## Governance cadence and artefacts

- **Roadmap stewardship**: Update [docs/roadmap.md](../roadmap.md) after major scope, risk, or milestone changes.
- **Metrics reviews**: Track DORA and SPACE targets per the [metrics plan](../metrics/metrics-plan.md); review monthly with engineering and product leads.
- **Quality gates**: Maintain ≥ 80% coverage, green lint/type/security/build checks, and document waivers in `Next_Steps.md` when temporary exceptions are approved.
- **Telemetry posture**: Validate instrumentation changes in staging before production rollout; log assumptions in the metrics plan and revisit quarterly.

## Decision logging

- Capture architectural or governance-impacting decisions as ADRs under `docs/explanations/` or new governance records when material changes occur.
- Record open risks, mitigation owners, and due dates in `Next_Steps.md` to preserve a single source of truth for follow-up work.

## Change management checklist

1. Confirm alignment with mission, personas, and constraints before accepting roadmap adjustments.
2. Document feature flags, rollout plans, and rollback procedures in the relevant pull request and governance notes.
3. Ensure support teams (Data Ops, Compliance, Observability) acknowledge changes affecting their runbooks prior to release.
