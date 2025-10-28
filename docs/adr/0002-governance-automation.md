---
title: Automate Conventional Commits governance workflows
summary: Introduce commit message linting, PR labelling, Renovate policies, and Release Drafter templates aligned to Conventional Commits.
last_updated: 2025-12-01
status: Accepted
---

Hotpass relies on Conventional Commits for release hygiene, but checks were manual. Reviewers could only spot malformed commit
messages during review, labels varied between contributors, and release notes were assembled by hand. Renovate also opened
ungrouped dependency PRs for the `uv` CLI and Prefect extras, which complicated orchestrator rollouts that require the extras
to move together.

## Decision

We introduced GitHub workflows that enforce these governance steps automatically:

- `commitlint` validates every pull request commit against Conventional Commits and blocks merges on violations.
- `pr-labeler` applies Conventional Commit-aligned `type:*`, `scope:*`, `prefect`, and `uv` labels based on branches and touched
  files so Release Drafter has consistent metadata.
- `release-drafter` compiles release notes from the labelled PRs using Conventional Commit categories.
- `renovate.json` now groups uv/Prefect extra upgrades, applies dependency labels, and restricts automerge to a weekend window
  once updates have stabilised for at least a day.

## Consequences

- Contributors must fix lint failures locally before requesting review, but they receive feedback immediately rather than during
  review.
- Label automation reduces manual toil yet still allows manual overrides when edge cases arise.
- Release notes stay aligned with Conventional Commit semantics, improving downstream changelog and governance artefacts.
- Coordinated uv/Prefect upgrades reduce Prefect deployment risk and allow safe weekend automerges.
- CODEOWNERS includes the new workflows and config files so platform maintainers review governance automation changes.
