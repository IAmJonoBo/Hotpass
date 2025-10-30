# Hotpass

Hotpass ingests messy spreadsheet collections (primarily XLSX) alongside orchestrated research crawlers managed through the CLI and MCP server. It cleans, normalises, backfills, maps relationships, and publishes analysis-ready outputs so teams can run deeper investigations with trusted data.

## Why Hotpass

- **Industry-ready**: Configurable profiles tailor validation rules, mappings, and terminology to your sector.
- **Quality first**: Great Expectations, POPIA compliance checks, and actionable quality reports keep stakeholders informed.
- **Operational**: Prefect orchestration, OpenTelemetry metrics, and a Streamlit dashboard make the pipeline production-friendly.

## Five-minute quickstart

1. Create an isolated environment with uv:

   ```bash
   uv venv
   export HOTPASS_UV_EXTRAS="dev docs"
   bash scripts/uv_sync_extras.sh
   ```

   Need orchestration or enrichment extras? Append them to
   `HOTPASS_UV_EXTRAS` before rerunning the helper script.

2. Confirm the CLI surface and available profiles:

   ```bash
   uv run hotpass overview
   ```

   The overview command lists the core verbs (`refine`, `enrich`, `qa`, `contracts`) and reports the
   installed extras/profile set so agents and operators can plan the next steps.

3. Run the refinement pipeline against the bundled fixtures:

   ```bash
   uv run hotpass refine \
     --input-dir ./data \
     --output-path ./dist/refined.xlsx \
     --profile generic \
     --archive
   ```

   The command writes refined outputs to `dist/refined.xlsx` and publishes the
   latest Great Expectations Data Docs under `dist/data-docs/`.

4. Optional: enrich the refined workbook deterministically (network off by default):

   ```bash
   uv run hotpass enrich \
     --input ./dist/refined.xlsx \
     --output ./dist/enriched.xlsx \
     --profile generic \
     --allow-network=false
   ```

5. Optional: regenerate validation reports explicitly while exploring the
   dataset contracts:

   ```bash
   uv run python scripts/validation/refresh_data_docs.py
   ```

6. Optional: build an adaptive research plan for a specific entity:

   ```bash
   uv run hotpass plan research \\
     --dataset ./dist/refined.xlsx \\
     --row-id 0 \\
     --allow-network
   ```

   The planner surfaces cached authority snapshots, deterministic enrichment updates, and
   crawl/backfill recommendations before you enable network access.

7. Launch the interactive bootstrap when you are ready to provision Prefect,
   observability, and supply-chain integrations:

   ```bash
   python scripts/idp/bootstrap.py --execute
   ```

Working on a hosted runner? Use `make sync EXTRAS="dev orchestration enrichment geospatial compliance dashboards"`
to replicate the environment bootstrap above with a single command.

## Preflight checks

Run these gates before opening a pull request so local results align with CI:

- `make qa` — runs Ruff format/lint, pytest with coverage, mypy, Bandit,
  detect-secrets, and pre-commit hooks.
- `uv run hotpass qa all` — executes the CLI-driven quality gates (QG‑1 → QG‑5)
  and mirrors the GitHub Actions workflow.
- `uv run python scripts/validation/refresh_data_docs.py` — refreshes Data Docs
  to confirm expectation suites remain in sync with contracts.
- `uv run python scripts/quality/fitness_functions.py` — exercises the
  architectural fitness checks documented in `docs/architecture/fitness-functions.md`.

## Documentation

The full documentation lives under [`docs/`](docs/index.md) and follows the Diátaxis framework:

- [Tutorials](docs/tutorials/quickstart.md) — end-to-end walkthroughs.
- [How-to guides](docs/how-to-guides/configure-pipeline.md) — targeted tasks such as configuring profiles or enabling observability. See the [dependency profile guide](docs/how-to-guides/dependency-profiles.md) to pick the right extras.
- [Reference](docs/reference/cli.md) — command syntax, data model, and expectation catalogue.
- Governance artefacts — [Data Docs](docs/reference/data-docs.md),
  [schema exports](docs/reference/schema-exports.md), and the
  [Marquez lineage quickstart](docs/observability/marquez.md).
- [Explanations](docs/explanations/architecture.md) — architectural decisions and platform scope.
- [Roadmap](docs/roadmap.md) — delivery status, quality gates, and tracked follow-ups. See also the
  repository-level [ROADMAP.md](ROADMAP.md) for a per-phase PR checklist.

## Contributing

Read the [documentation contributing guide](docs/CONTRIBUTING.md) and [style guide](docs/style.md), then submit pull requests using Conventional Commits. The contributing guide now includes a five-minute documentation quickstart plus preflight reminders. Run the consolidated QA suite before opening a PR:

```bash
make qa
```

The `qa` target runs Ruff formatting and linting, pytest with coverage, mypy (strict for the pipeline configuration module and QA tooling), Bandit, detect-secrets, and repository pre-commit hooks so local results match CI.

Join the conversation in the `#hotpass` Slack channel or open an issue using the templates under `.github/ISSUE_TEMPLATE/`.
