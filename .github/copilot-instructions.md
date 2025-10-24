# Hotpass Repository Guidance for GitHub Copilot

## Project Overview
- Hotpass is a Python 3.13 data-refinement pipeline that consolidates heterogeneous Excel inputs into a governed single source of truth.
- Tooling is managed with uv; documentation is built with Sphinx + MyST; QA is enforced through pre-commit hooks (ruff, black, mypy, detect-secrets, bandit).
- Source code lives under `src/hotpass/`; automation scripts are in `scripts/`; documentation is in `docs/` with MyST-flavoured Markdown under `docs/source/`.

## Required Toolchain
- Install dependencies with `uv sync --extra dev --extra docs` (lockfile enforced).
- Execute commands through `uv run ...` to reuse the managed virtual environment.
- Primary entry points:
  - `uv run hotpass --help` for CLI usage.
  - `uv run pytest` for the full test suite.
  - `uv run ruff check` and `uv run ruff format --check` for lint/format.
  - `uv run mypy src scripts` for type checks.
  - `uv run sphinx-build docs/source docs/build` to regenerate HTML docs.

## Coding Expectations
- Keep line length ≤100 characters; rely on ruff/black for formatting.
- Add tests in `tests/` for new behaviour; prefer parametrised pytest cases where feasible.
- Update documentation alongside code changes (especially `docs/source/*.md`) to stay release-ready.
- Preserve provenance and compliance hooks in `hotpass.artifacts`, `hotpass.contacts`, and configuration profiles when modifying pipeline logic.

## Useful Resources
- Docs overview: `docs/architecture-overview.md`, `docs/implementation-guide.md`, `docs/gap-analysis.md`.
- QA workflow mirrors `.github/workflows/process-data.yml`; emulate those steps locally before large changes.
- For benchmarking or packaging, see `tests/test_artifacts.py` and existing CLI scripts.

## When Assigning Tasks to Copilot
1. Ensure dependencies are synced (setup steps workflow covers this for the agent).
2. Reference specific paths or functions to narrow scope.
3. Ask Copilot to run targeted QA commands (ruff, pytest, mypy, docs build) before completion.
4. Mention compliance considerations when touching sensitive data handling code.

## Networking Notes
- Copilot relies on outbound HTTPS access to GitHub and PyPI when installing dependencies. If a proxy is required, populate `HTTPS_PROXY`/`HTTP_PROXY` environment variables in the repository’s `copilot` environment to mirror local settings.
- For private package indexes or additional services, store tokens as Copilot environment secrets and expose them through environment variables in setup steps.
- Prefect Cloud endpoints are blocked in the agent environment; avoid commands that require `sens-o-matic.prefect.io` or other external Prefect services. Use the local profile configured by setup steps (`PREFECT_API_URL=http://127.0.0.1:4200/api`) and keep orchestration tasks in offline mode.
