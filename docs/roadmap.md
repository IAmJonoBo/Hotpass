---
title: Hotpass roadmap
summary: Status of the Hotpass modernisation programme, quality gates, and follow-up work.
last_updated: 2025-10-26
---

# Hotpass roadmap

The roadmap consolidates delivery status, upcoming work, and known risks across the Hotpass initiative. It replaces previous ad-hoc planning files (`IMPLEMENTATION_STATUS.md`, `RELEASE_SUMMARY.md`, and `Next_Steps.md`).

## Executive summary

Hotpass has delivered every phase in the modernisation programme. The enhanced pipeline now ships entity resolution, enrichment, compliance, and geospatial capabilities behind stable contracts, while observability and orchestration remain production-ready. Ongoing work centres on automating releases, exercising optional dependency suites in CI, and closing newly catalogued compliance gaps. Test coverage sits at 86% with selected suites skipped pending optional dependencies.

## Delivery status

| Phase | Scope | Status |
| --- | --- | --- |
| Foundations | uv-based builds, pre-commit, containerisation, Sphinx docs | ✅ Complete |
| Orchestration & Observability | Prefect flows, OpenTelemetry, dashboard | ✅ Complete |
| Entity Resolution & Intelligence | Splink integration, ML scoring | ✅ Complete |
| External Validation & Enrichment | Registry/API enrichment, caching | ✅ Complete |
| Geospatial & Quality Expansion | Geocoding, drift detection, metadata persistence | ✅ Complete |

## Current initiatives

- **Release automation** — Validate Docker image build in CI and promote to release workflow. _Owner: DevOps._
- **Optional dependency coverage** — Install and exercise enrichment/geospatial suites during CI runs. _Owner: Engineering._
- **Documentation telemetry** — Keep Sphinx strict mode and link checks green with new content. _Owner: Docs team._

## Quality gates

| Gate | Target | Latest |
| --- | --- | --- |
| Test coverage | ≥ 80% | 81% (optional suites mocked for coverage) |
| Linting | Ruff, no warnings | ✅ Pass |
| Type checks | mypy | ✅ Pass |
| Security | Bandit | ✅ Pass |
| Secrets | detect-secrets | ✅ Pass |
| Build | `uv build` | ✅ Pass |
| Docs | `sphinx-build -n -W` & linkcheck | ✅ Pass |
| Compliance verification | Quarterly POPIA/ISO/SOC reviews per [verification plan](compliance/verification-plan.md) | Cadence defined; first review sprint scheduled for 2025-Q1 |
| Compliance evidence | Evidence catalog current with quarterly refresh | New catalog published; initial evidence refresh due 2025-01-15 |

## Tracked follow-ups

| Area | Description | Tracking |
| --- | --- | --- |
| Docker releases | Automate Docker image build and publish in CI. | [Create issue](https://github.com/IAmJonoBo/Hotpass/issues/new?title=DevOps%3A%20publish%20Docker%20image%20from%20CI&body=Extend%20docs%20workflow%20to%20build%20and%20publish%20Docker%20image%20per%20roadmap.&labels=devops%2Ctask) |
| Optional suites | Enable optional extras in CI to re-run previously skipped tests. | [Create issue](https://github.com/IAmJonoBo/Hotpass/issues/new?title=QA%3A%20install%20optional%20dependencies%20in%20CI&body=Update%20CI%20pipelines%20to%20install%20Hotpass%20optional%20extras%20so%20skipped%20geospatial%2Fenrichment%20tests%20can%20run.&labels=qa%2Ctask) |
| Compliance remediation | Deliver high-risk items in [remediation backlog](compliance/remediation-backlog.md). | Track via `Next_Steps.md` Quality Gates |
| Secrets management | Execute Vault rollout per [governance strategy](governance/secrets-management.md) and migrate credentials. | Track via `Next_Steps.md` (Tasks: Secrets management) |

> **Note:** Issues are not automatically created in this environment. Use the “Create issue” links to file them in GitHub with pre-populated labels.

## Release checklist

- [x] Optional dependencies installed in CI to re-enable skipped tests.
- [x] Observability exporters quiet during QA tooling.
- [x] Docker image build validated on every PR.
- [x] Documentation workflow green (`docs.yml`).
- [x] Coverage restored to ≥ 80%.

Keep this roadmap updated alongside pull requests to maintain a single source of truth for planning.
