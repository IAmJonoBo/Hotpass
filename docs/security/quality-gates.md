---
title: Quality and security gates
summary: Expanded automated gates covering testing, linting, mutation, contracts, and security scans.
last_updated: 2025-10-25
---

# Quality and security gates

## Current automation

| Gate                     | Tooling                | Command                                                                           | Evidence                    |
| ------------------------ | ---------------------- | --------------------------------------------------------------------------------- | --------------------------- |
| Unit + integration tests | pytest                 | `uv run pytest --cov=src --cov=tests`                                             | QA job (`process-data.yml`) |
| Linting                  | Ruff                   | `uv run ruff check`                                                               | QA job                      |
| Formatting               | Ruff                   | `uv run ruff format --check`                                                      | QA job                      |
| Types                    | mypy                   | `uv run mypy src tests scripts`                                                   | QA job                      |
| Security                 | Bandit                 | `uv run bandit -r src scripts`                                                    | QA job                      |
| Secrets                  | detect-secrets         | `uv run detect-secrets scan src tests scripts`                                    | QA job                      |
| Build                    | uv build               | `uv run uv build`                                                                 | QA job                      |
| Accessibility            | pytest marker          | `uv run pytest -m accessibility`                                                  | Accessibility job           |
| Mutation testing         | mutmut                 | `uv run python scripts/qa/run_mutation_tests.py`                                  | Mutation job                |
| Contract testing         | pytest contract suite  | `uv run pytest tests/contracts`                                                   | QA job                      |
| Static analysis          | Semgrep                | `uv run semgrep --config=auto`                                                    | Static-analysis job         |
| Supply-chain             | CycloneDX + provenance | `uv run python scripts/supply_chain/generate_sbom.py`                             | Supply-chain job            |
| Policy-as-code           | OPA                    | `opa eval --data policy --input dist/sbom/hotpass-sbom.json "data.hotpass.allow"` | Supply-chain job            |

## Additional gates roadmap

- **OWASP ZAP baseline** — Execute via Docker action targeting Streamlit staging env (pending).
- **Performance budget** — Add `pytest-benchmark` thresholds for pipeline latency.
- **Accessibility budget** — Gate on zero critical axe violations once Playwright integration lands.
- **CodeQL** — Evaluate integration for static code analysis (pending GitHub Advanced Security licence).

## Governance

- Document gate owners in `Next_Steps.md` tasks.
- Capture waiver process (owner approval, expiry date) in `docs/governance/pr-playbook.md`.
- Record gate outcomes per release in `docs/roadmap/30-60-90.md`.
