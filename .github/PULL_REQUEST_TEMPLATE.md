## Summary

- [ ] Linked roadmap item / issue (e.g. closes #123):
- [ ] Documentation updated (Diátaxis + TechDocs)
- [ ] `Next_Steps.md` updated

## Testing

- [ ] `uv run pytest --cov=src --cov=tests`
- [ ] Tests avoid bare `assert` (use `expect(..., message)` per `docs/how-to-guides/assert-free-pytest.md`)
- [ ] `uv run ruff check`
- [ ] `uv run ruff format --check`
- [ ] `uv run mypy src tests scripts`
- [ ] `uv run bandit -r src scripts`
- [ ] `uv run detect-secrets scan src tests scripts`
- [ ] `uv run uv build`
- [ ] `uv run pytest -m accessibility`
- [ ] `uv run python scripts/qa/run_mutation_tests.py`
- [ ] `uv run python scripts/quality/fitness_functions.py`
- [ ] `uv run python scripts/supply_chain/generate_sbom.py`
- [ ] `uv run python scripts/supply_chain/generate_provenance.py`
- [ ] `uv run semgrep --config=auto`

## Risk & mitigation

- Describe risk, blast radius, rollback plan.

## Artefacts

- Attach SBOM/provenance/accessibility reports if relevant.
