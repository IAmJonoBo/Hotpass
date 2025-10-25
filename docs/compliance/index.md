---
title: Compliance — framework baseline
summary: Overview of Hotpass compliance frameworks, maturity scoring, evidence mapping, and remediation approach.
last_updated: 2025-10-25
---

# Compliance — framework baseline

The Hotpass governance programme spans POPIA, ISO 27001, and SOC 2. This index tracks baseline maturity for each framework, links controls to evidence, and consolidates remediation and verification cadences.

## How maturity scoring works

1. **Evidence-first** — Every control references tangible artefacts such as pipeline configuration, QA outputs, or architecture documentation.
2. **Target alignment** — Each control compares the current state to the desired target and captures the gap narrative plus risk severity.
3. **Actionable backlog** — High-risk gaps feed the [remediation backlog](./remediation-backlog.md) with owners and due dates for audit traceability.
4. **Cadence discipline** — Verification checkpoints and metrics live in the [verification plan](./verification-plan.md) to ensure continuous assurance.

## Framework matrices

| Framework | Scope | Baseline maturity | Matrix |
| --- | --- | --- | --- |
| POPIA | Data privacy controls for South African personal information. | Core processing controls in place; evidence refresh cadence pending. | [POPIA maturity matrix](./popia/maturity-matrix.md) |
| ISO 27001 | Information security management system practices. | Policies drafted; risk treatment and supplier management gaps remain. | [ISO 27001 maturity matrix](./iso-27001/maturity-matrix.md) |
| SOC 2 | Trust Services Criteria for security, availability, and confidentiality. | Logging and change management strong; incident response still ad hoc. | [SOC 2 maturity matrix](./soc2/maturity-matrix.md) |

## Supporting artefacts

- [Remediation backlog](./remediation-backlog.md) — Prioritised work to close gaps.
- [Evidence catalog](./evidence-catalog.md) — Retrieval instructions and owners for audit artefacts.
- [Verification plan](./verification-plan.md) — Cadence, measurement approach, and tooling alignment per framework.

Update these pages whenever controls, evidence sources, or remediation statuses change. Keep `Next_Steps.md` and the [roadmap](../roadmap.md) aligned so compliance remains a first-class workstream.
