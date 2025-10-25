---
title: Compliance — evidence catalog
summary: Inventory of audit evidence sources, locations, and retention guidance supporting compliance controls.
last_updated: 2025-10-25
---

# Compliance — evidence catalog

| Evidence source | Location | Owner | Retention | Notes |
| --- | --- | --- | --- | --- |
| QA command history | `Next_Steps.md` and GitHub Actions `process-data.yml` logs | Engineering | 1 year | Capture command outputs in release notes per run; export workflow logs quarterly. |
| Prefect flow run logs | Prefect Orion API (`refinement_pipeline_flow`) | Engineering | 1 year rolling | Configure automated export to object storage; include consent validation events once POPIA-001 lands. |
| Threat model | [`docs/security/threat-model.md`](../security/threat-model.md) | Security | Update on change | Serves as input to ISO27001-002 asset register and SOC2-002 risk register. |
| Architecture diagrams | [`docs/architecture/hotpass-architecture.dsl`](../architecture/hotpass-architecture.dsl) | Architecture | Update on change | Provide trust boundaries for POPIA transfer analysis and SOC 2 confidentiality controls. |
| Metrics dashboards | Four Keys / SPACE exports (planned) | Observability | TBD | TODO: Define export pipeline once metrics automation is enabled. |
| DSAR runbook & logs | _Pending implementation_ | Support & Engineering | TBD | TODO: Create storage location after POPIA-003 deliverable; link runbook and Prefect automation outputs. |
| Supplier risk register | _Pending implementation_ | Procurement & Security | TBD | TODO: Store register under `docs/governance/` once ISO27001-004 completes. |
| Incident response playbook | [`docs/security/threat-model.md`](../security/threat-model.md) & future incident guide | Security | Update on change | Update with POPIA escalation steps per POPIA-004; archive historical versions. |
| Data export access logs | _Pending implementation_ | Platform | 1 year | TODO: Configure storage-level logging and archive snapshots; reference in SOC2-005 evidence. |

Review evidence completeness during each verification cycle and update retention guidance as storage or regulatory requirements evolve.
