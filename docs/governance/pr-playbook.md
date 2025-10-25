---
title: Pull request playbook
summary: Expectations, quality gates, and waiver process for Hotpass pull requests.
last_updated: 2025-10-25
---

# Pull request playbook

## Checklist

1. Reference roadmap item or issue.
2. Update documentation (Diátaxis) and `Next_Steps.md`.
3. Run QA suite locally (tests, lint, type, security, secrets, build, accessibility, mutation, fitness functions).
4. Attach artefacts (SBOM, provenance, accessibility report) as PR uploads if relevant.
5. Tag code owners (`@platform-eng`, `@security`, `@docs`) per affected areas.

## Quality gate waivers

| Gate | Owner | Waiver conditions | Max duration |
| --- | --- | --- | --- |
| Tests | Engineering | Only for flaky tests with mitigation issue filed. | 5 days |
| Accessibility | Platform | Allowed for feature flagged UI with remediation scheduled. | 7 days |
| Mutation | QA | Permitted if coverage tool unstable; rerun within next sprint. | 7 days |
| Supply-chain | Security | Only if upstream CycloneDX outage; require manual SBOM in PR. | 3 days |

Waivers require documented approval comment and entry in `Next_Steps.md` Quality Gates with expiry date.

## Review workflow

- **Author** ensures PR template completed, attaches test evidence.
- **Reviewers** inspect code, docs, and artefacts; confirm automation success.
- **Security reviewer** validates supply-chain outputs and policy evaluations.
- **Docs reviewer** ensures TechDocs/Diátaxis updates align with style guide.

## Rollback procedure

- Revert commit via GitHub UI or CLI (`git revert <sha>`).
- Restore previous release artefacts (dist, SBOM, provenance) from GitHub Releases.
- Update `Next_Steps.md` with rollback summary and follow-up tasks.
- Notify stakeholders in `#hotpass` Slack channel with remediation ETA.
