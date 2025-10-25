---
title: Compliance — POPIA maturity matrix
summary: Baseline POPIA control coverage, gaps, evidence links, and owners for Hotpass.
last_updated: 2025-10-25
---

# Compliance — POPIA maturity matrix

| Control | Current maturity | Target state | Gap & risk | Risk severity | Evidence | Control owner | Remediation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Lawful processing basis | Profiles capture consent status and processing purpose in YAML, but enforcement relies on manual review. | Automated consent validation before processing and explicit logging of lawful basis decisions. | Consent metadata not programmatically enforced, risking unlawful processing if operators skip manual checks. | High | [`docs/how-to-guides/configure-pipeline.md`](../../how-to-guides/configure-pipeline.md); [`src/hotpass/compliance.py`](../../../src/hotpass/compliance.py) consent checks; Prefect flow logs under `data/logs/prefect/`. | Product & Engineering | [Backlog: POPIA-001](../remediation-backlog.md#popia-001-automate-consent-validation) |
| Data minimisation | Column mapping trims unused attributes, yet enrichment adds optional PII without documented justification. | Enrichment gated by documented purpose and minimisation checklist per dataset. | Missing approval workflow for enrichment connectors may introduce unnecessary PII fields. | Medium | [`docs/explanations/data-quality-strategy.md`](../../explanations/data-quality-strategy.md); [`src/hotpass/enrichment.py`](../../../src/hotpass/enrichment.py). | Data Governance | [Backlog: POPIA-002](../remediation-backlog.md#popia-002-document-enrichment-minimisation-checklists) |
| Data subject rights | CLI exposes export/erasure helpers, but no documented SLA or verification that requests complete. | Formal DSAR runbook with SLA tracking and Prefect automation. | Without SLA tracking, DSAR handling may miss regulatory deadlines. | High | [`docs/reference/cli.md`](../../reference/cli.md); [`docs/roadmap.md`](../../roadmap.md); DSAR artefacts to be stored in `data/compliance/dsar/`. | Support & Engineering | [Backlog: POPIA-003](../remediation-backlog.md#popia-003-implement-dsar-tracking) |
| Breach notification | Threat model references incident process, yet runbook lacks POPIA-specific escalation steps. | Documented incident response playbook referencing POPIA notification windows. | Escalations could omit regulator notification within 72 hours. | Medium | [`docs/security/threat-model.md`](../../security/threat-model.md); Prefect run logs (`data/logs/`). | Security | [Backlog: POPIA-004](../remediation-backlog.md#popia-004-extend-incident-playbook) |
| Cross-border transfer safeguards | No automated check for transfer destinations when exporting archives. | Transfer decision matrix and technical controls (encryption, access logging) for exports. | Potential non-compliant transfer if archives sync to global storage without safeguards. | Medium | [`docs/explanations/architecture.md`](../../explanations/architecture.md); `dist/` export pipeline logs. | Platform | [Backlog: POPIA-005](../remediation-backlog.md#popia-005-define-transfer-controls) |

Unknowns:

- Confirm whether customer contracts require additional POPIA chapters (e.g., prior authorisation) beyond current scope.
- Validate retention periods for archived spreadsheets once DSAR automation lands.
