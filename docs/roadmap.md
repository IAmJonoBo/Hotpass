---
title: Hotpass roadmap
summary: Status of the Hotpass modernisation programme, quality gates, and follow-up work.
last_updated: 2025-10-25
---

## Hotpass roadmap

The roadmap consolidates delivery status, upcoming work, and known risks across the Hotpass initiative. It replaces previous ad-hoc planning files (`IMPLEMENTATION_STATUS.md`, `RELEASE_SUMMARY.md`, and `Next_Steps.md`).

## Executive summary

Hotpass is feature-complete for the enhanced pipeline and observability foundation. The remaining work focuses on enrichment coverage, external integrations, and operational resilience. Test coverage sits at 67% with several suites skipped pending optional dependencies.

## Delivery status

| Phase | Scope | Status |
| --- | --- | --- |
| Foundations | uv-based builds, pre-commit, containerisation, Sphinx docs | ✅ Complete |
| Orchestration & Observability | Prefect flows, OpenTelemetry, dashboard | 🟡 Mostly complete — exporters need hardening |
| Entity Resolution & Intelligence | Splink integration, ML scoring | 🟡 Partially complete — historical merge support outstanding |
| External Validation & Enrichment | Registry/API enrichment, caching | 🔴 In progress |
| Geospatial & Quality Expansion | Geocoding, drift detection, metadata persistence | 🔴 In progress |

## Current initiatives

- **Docs hardening** — Move to Diátaxis, enable strict Sphinx builds, and enforce style guidance. _Owner: Docs team._
- **Observability stability** — Resolve OTLP shutdown warnings and document console fallbacks. _Owner: Engineering._
- **Docker delivery** — Validate Docker image build in CI and promote to release workflow. _Owner: DevOps._

## Quality gates

| Gate | Target | Latest |
| --- | --- | --- |
| Test coverage | ≥ 80% | 67% (optional suites skipped) |
| Linting | Ruff, no warnings | ✅ Pass |
| Type checks | mypy | ✅ Pass |
| Security | Bandit | ✅ Pass |
| Secrets | detect-secrets | ✅ Pass |
| Build | `uv build` | ✅ Pass |
| Docs | `sphinx-build -n -W` & linkcheck | 🚧 Newly enforced |

## Tracked follow-ups

| Area | Description | Tracking |
| --- | --- | --- |
| Entity resolution | Load and merge historical data when consolidating entities. | [Create issue](https://github.com/IAmJonoBo/Hotpass/issues/new?title=Entity%20resolution%3A%20load%20historical%20records&body=Implement%20support%20for%20loading%20and%20merging%20historical%20entity%20records%20referenced%20in%20`src/hotpass/entity_resolution.py`%20TODO.&labels=enhancement%2Centity-resolution) |
| Telemetry resilience | Prevent OTLP exporter errors when stdout is closed. | [Create issue](https://github.com/IAmJonoBo/Hotpass/issues/new?title=Observability%3A%20harden%20OTLP%20exporter%20shutdown&body=Resolve%20ValueError%20raised%20when%20console%20handlers%20flush%20after%20process%20shutdown.%20Tracked%20in%20Next_Steps.md.&labels=bug%2Cobservability) |
| Docker releases | Automate Docker image build and publish in CI. | [Create issue](https://github.com/IAmJonoBo/Hotpass/issues/new?title=DevOps%3A%20publish%20Docker%20image%20from%20CI&body=Extend%20docs%20workflow%20to%20build%20and%20publish%20Docker%20image%20per%20roadmap.&labels=devops%2Ctask) |

> **Note:** Issues are not automatically created in this environment. Use the “Create issue” links to file them in GitHub with pre-populated labels.

## Release checklist

- [ ] Optional dependencies installed in CI to re-enable skipped tests.
- [ ] Observability exporters quiet during QA tooling.
- [ ] Docker image build validated on every PR.
- [ ] Documentation workflow green (`docs.yml`).
- [ ] Coverage restored to ≥ 80%.

Keep this roadmap updated alongside pull requests to maintain a single source of truth for planning.
