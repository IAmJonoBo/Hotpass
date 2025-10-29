---
title: Contributing to the documentation
summary: Workflow and expectations for updating the Hotpass documentation set.
last_updated: 2025-12-26
---

# Contributing to the documentation

Thank you for improving Hotpass docs. Follow this lightweight workflow to keep contributions consistent.

> 💡 Working on application code instead? Run `make qa` from the repository root to execute Ruff lint/format, pytest with coverage, mypy (strict for pipeline configuration and QA tooling), Bandit, detect-secrets, and pre-commit hooks before submitting your pull request.

## Five-minute documentation quickstart

1. Create or activate the uv environment used by the engineering team:

   ```bash
   uv sync --extra docs
   ```

2. Open the documentation landing page at [`docs/index.md`](./index.md) to verify
   where your update fits within the Diátaxis structure. Governance artefacts
   such as the [Data Docs reference](./reference/data-docs.md) and
   [schema export reference](./reference/schema-exports.md) now surface directly
   from the landing page.

3. Edit the relevant Markdown/MyST files and update the YAML front matter with
   the current date.

4. Run the preflight checks:

   ```bash
   uv run python scripts/validation/refresh_data_docs.py
   uv run sphinx-build -n -W -b html docs docs/_build/html
   ```

5. Cross-check navigation by opening `_build/html/index.html` in a browser and
   following links to the refreshed governance references.

## 1. Set up your environment

```bash
uv sync --extra docs
uv run pre-commit install
```

## 2. Make focused changes

- Use the Diátaxis structure: tutorials, how-to guides, reference, explanations.
- Update or create pages under `docs/` with YAML front matter (`title`, `summary`, `last_updated`).
- Keep README changes minimal—link out to full documentation when possible.
- When touching pytest suites, follow the [assert-free pattern](./how-to-guides/assert-free-pytest.md) (`expect(..., message)`) so Bandit stays green without waivers.
- Apply the Conventional Commit label taxonomy when opening PRs: automation attaches `type:*` (feature/fix/docs/ci/chore) and `scope:*` (dependencies/governance) labels plus `prefect`/`uv` for orchestrator extras. Double-check the labeler output so Release Drafter summarises your work accurately.

## 3. Run quality checks

```bash
uv run sphinx-build -n -W -b html docs docs/_build/html
uv run sphinx-build -b linkcheck docs docs/_build/linkcheck
```

When updates touch validation guidance, also regenerate Data Docs with
`uv run python scripts/validation/refresh_data_docs.py` so reviewers can inspect
the refreshed reports alongside the new copy.

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
