---
title: Adopt uv build backend and consolidated QA entrypoint
summary: Switch the repository build backend to uv and standardise the QA workflow behind a single command.
last_updated: 2025-02-15
status: Accepted
---

# Context

Hotpass contributors were invoking a long sequence of commands to build the
package, lint, test, run type checks, and scan for security or secrets issues.
That workflow was easy to drift from and difficult to document consistently
across README, governance guides, and contributor instructions. The project also
continued to rely on `setuptools.build_meta` even though the team already
standardised on `uv` for dependency management and scripting.

# Decision

We switched the PEP 517 build backend to `uv.core.build` with the corresponding
`requires = ["uv<1"]` declaration, keeping all existing PEP 621 metadata
unchanged. We also introduced a `make qa` target that executes the
repository's required checks in one pass: Ruff formatting and linting, pytest
with coverage, mypy (strict for the pipeline configuration module and QA tooling with targeted
overrides), Bandit, detect-secrets, and all configured pre-commit hooks.

# Consequences

- Contributors have a single, documented command to run locally before opening
  a pull request, reducing drift from CI behaviour.
- Using uv's build backend aligns packaging with the dependency workflow,
  eliminating redundant bootstrap steps.
- The consolidated QA entrypoint makes it easier to extend or reorder checks,
  because updates now happen in one script rather than multiple documentation
  snippets.
- Developers must ensure `uv` is available in environments that build or test
  the project, but that dependency was already required for sync and execution
  workflows.
