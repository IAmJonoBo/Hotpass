---
title: Contributing to the documentation
summary: Workflow and expectations for updating the Hotpass documentation set.
last_updated: 2025-12-01
---

# Contributing to the documentation

Thank you for improving Hotpass docs. Follow this lightweight workflow to keep contributions consistent.

> 💡 Working on application code instead? Run `make qa` from the repository root to execute Ruff lint/format, pytest with coverage, mypy (strict for pipeline configuration and QA tooling), Bandit, detect-secrets, and pre-commit hooks before submitting your pull request.

## 1. Set up your environment

```bash
uv sync --extra docs
uv run pre-commit install
```

## 2. Make focused changes

- Use the Diátaxis structure: tutorials, how-to guides, reference, explanations.
- Update or create pages under `docs/` with YAML front matter (`title`, `summary`, `last_updated`).
- Keep README changes minimal—link out to full documentation when possible.
- Apply the Conventional Commit label taxonomy when opening PRs: automation attaches `type:*` (feature/fix/docs/ci/chore) and `scope:*` (dependencies/governance) labels plus `prefect`/`uv` for orchestrator extras. Double-check the labeler output so Release Drafter summarises your work accurately.

## 3. Run quality checks

```bash
uv run sphinx-build -n -W -b html docs docs/_build/html
uv run sphinx-build -b linkcheck docs docs/_build/linkcheck
```

Fix all warnings before opening a pull request. The docs CI workflow enforces the same commands.

## 4. Submit your pull request

- Use Conventional Commits (for example, `docs: update quickstart tutorial`).
- Update `Next_Steps.md` with what changed and any follow-up work.
- Reference relevant roadmap items or GitHub issues.

## 5. Review checklist

- [ ] Front matter updated with the current date.
- [ ] Internal links work after moving or renaming files.
- [ ] Screenshots attached for visual changes (Streamlit or other UI updates).
- [ ] Roadmap updated if new workstreams are introduced.

Questions? Reach out in `#hotpass` on Slack or tag `@Docs` in your pull request.
