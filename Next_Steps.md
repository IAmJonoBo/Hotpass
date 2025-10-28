# Next Steps

## Active Deliverables
| Due | Owner(s) | Item | Notes |
| --- | --- | --- | --- |
| 2025-12-13 | QA & Engineering | Add regression coverage for modular pipeline stages | Finalise `tests/pipeline/fixtures/` by 2025-12-09; pair nightly dry-run after CLI stress test. |
| 2025-12-20 | QA | Exercise CLI progress reporting under high-volume fixtures | Generate 10k-run dataset in `tests/cli/fixtures/progress_high_volume.json` and reserve 02:00–04:00 UTC window. |
| 2025-12-31 | QA | Execute full E2E runs with canonical configuration toggles | Book staging slot on 2025-12-18; reuse Prefect deployment `hotpass-e2e-staging`. |
| 2025-12-31 | Engineering | Add Prefect flow integration tests for canonical overrides | Extend `tests/test_orchestration.py` and capture fixtures during the 2025-12-18 staging run alongside QA. |
| 2026-01-05 | Platform | Validate Prefect backfill deployment guardrails in staging | Share staging credentials and freeze changes week of 2025-12-29 to avoid holiday overlap. |
| 2026-01-15 | Engineering | Benchmark `HotpassConfig.merge` on large payloads | Run benchmarks alongside December integration tests; feed results into January ADR updates. |
| 2026-01-15 | QA & Engineering | Extend orchestrate/resolve CLI coverage for advanced profiles | Draft scope by 2025-12-19; reuse CLI stress fixtures and add resolve scenarios in `tests/cli/test_resolve.py`. |

## Watch List
- Track upstream `uv.core.build` availability and prepare re-adoption plan (Platform, target: 2025-12-05) — monitor Astral release notes, expand `docs/adr/0001-qa-tooling.md`, and stage QA dry-run when preview artefact lands.
- Monitor Semgrep SSL root-cause work; once the corporate CA bundle is available, update `docs/security/tooling.md` and clear the sandbox block (Security, target: 2025-12-12).

## Recently Completed Highlights
- Governance automation stack verified end-to-end (commitlint, labeler, release drafter, Renovate grouping) and captured in ADR 0002.
- Local pytest baseline verified after `make sync EXTRAS="dev"` (`.venv/bin/pytest --maxfail=1 --disable-warnings`).
- Dependency profile helper (`scripts/uv_sync_extras.sh`) introduced; workflows, README, and AGENTS guidance updated to use `HOTPASS_UV_EXTRAS`.
- Semgrep auto script added (`scripts/security/semgrep_auto.sh`) with CA bundle support; `make semgrep-auto` target available for local and CI runs.
- Consolidated QA gate (`make qa`) restored by refreshing the detect-secrets baseline and normalising test fixtures.
- Weekly `mypy-audit` workflow added with automatic issue creation on failures.
- Bootstrap execute-mode how-to published, covering guardrails and rollback steps.

## Quality Gates
### Open
- None (all current gates verified)

### Verified
| Gate | Last Verified |
| --- | --- |
| Pytest with coverage ≥ 80% | 2025-10-28 (local `.venv/bin/pytest --maxfail=1 --disable-warnings` after `HOTPASS_UV_EXTRAS="dev" bash scripts/uv_sync_extras.sh`) |
| Ruff lint & format checks | 2025-10-28 |
| Mypy strict targets (`uv run mypy src tests scripts`) | 2025-10-28 |
| Bandit security scan (`uv run bandit -r src scripts`) | 2025-10-28 |
| Detect-secrets scan (`uv run detect-secrets scan src tests scripts`) | 2025-10-28 |
| Package build succeeds (`uv run uv build`) | 2025-10-28 |
| Accessibility smoke tests (`uv run pytest -m accessibility`) | 2025-10-28 |
| Mutation harness (`uv run python scripts/qa/run_mutation_tests.py`) | 2025-10-28 |
| Fitness functions (`uv run python scripts/quality/fitness_functions.py`) | 2025-10-28 |
| SBOM and provenance scripts | 2025-10-28 |
| Semgrep static analysis (`uv run semgrep --config=policy/semgrep/hotpass.yml --metrics=off`) | 2025-10-28 |
| Semgrep auto (`make semgrep-auto`, optional `HOTPASS_CA_BUNDLE_B64`) | 2025-10-28 |
| Automation metrics coverage (`tests/test_observability.py::test_record_automation_delivery_tracks_requests`) | 2025-10-28 |
| ScanCode licence audit / REUSE lint | 2025-10-28 |

## Reference Commands
- Tests: `.venv/bin/pytest --cov=src --cov=tests --cov-report=term-missing`
- Lint: `.venv/bin/ruff check`
- Format: `.venv/bin/ruff format --check`
- Warning gate: `uv run pytest -W error --maxfail=1`
- Types: `.venv/bin/mypy src tests scripts`
- Security: `uv run bandit -r src scripts`
- Secrets: `uv run detect-secrets scan src tests scripts` <!-- pragma: allowlist secret -->
- Build: `uv run uv build`
- Docs build: `uv run sphinx-build -n -W -b html docs docs/_build/html`
- Docs linkcheck: `uv run sphinx-build -b linkcheck docs docs/_build/linkcheck`
- Accessibility: `uv run pytest -m accessibility`
- Mutation: `uv run python scripts/qa/run_mutation_tests.py`
- Fitness functions: `uv run python scripts/quality/fitness_functions.py`
- SBOM: `uv run python scripts/supply_chain/generate_sbom.py`
- Provenance: `uv run python scripts/supply_chain/generate_provenance.py`
- Compliance cadence: `uv run python scripts/compliance/run_verification.py --reviewer "Compliance Bot" --notes "Initial automation baseline"`
