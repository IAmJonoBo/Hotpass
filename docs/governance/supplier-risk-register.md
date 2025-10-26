---
title: Supplier risk register
summary: Inventory and review cadence for key suppliers supporting the Hotpass platform.
last_updated: 2025-10-26
---

# Supplier risk register

| Supplier | Service scope | Classification | Last review | Next review | Notes |
| -------- | ------------- | -------------- | ----------- | ----------- | ----- |
| Prefect  | Orchestration platform for scheduled runs | High | 2024-12-10 | 2025-03-10 | Tokens rotated monthly; ensure worker nodes restrict egress. |
| Slack    | Incident communication and stakeholder updates | Medium | 2024-11-30 | 2025-02-28 | Confirm workspace retention matches POPIA requirements. |
| Vault    | Secrets management for CI and Prefect workers | High | 2024-12-01 | 2025-03-01 | Audit logs reviewed quarterly; ensure namespace policies remain least privilege. |
| GitHub   | Source control and CI/CD | High | 2024-12-05 | 2025-03-05 | Actions runners restricted to pinned images; monitor security advisories weekly. |

Document findings from each quarterly verification run by appending rows with review dates
and remediation actions. Link deeper assessments or supplier questionnaires in the notes
column when available.
