# Hotpass

Hotpass refines messy spreadsheets into a governed single source of truth. The platform normalises columns, resolves duplicates, enriches data, and publishes quality signals so teams can trust the results.

## Why Hotpass

- **Industry-ready**: Configurable profiles tailor validation rules, mappings, and terminology to your sector.
- **Quality first**: Great Expectations, POPIA compliance checks, and actionable quality reports keep stakeholders informed.
- **Operational**: Prefect orchestration, OpenTelemetry metrics, and a Streamlit dashboard make the pipeline production-friendly.

## Get started

```bash
uv venv
export HOTPASS_UV_EXTRAS="dev docs"
bash scripts/uv_sync_extras.sh
uv run hotpass --input-dir ./data --output-path ./dist/refined.xlsx --archive
```

Run `python scripts/idp/bootstrap.py` (add `--execute` to apply changes) for an interactive bootstrap that provisions dependencies, Prefect profiles, and supply-chain tooling.

Need orchestration or enrichment? Set `HOTPASS_UV_EXTRAS` to the extras you need before running the helper script:

```bash
HOTPASS_UV_EXTRAS="dev orchestration enrichment geospatial compliance dashboards" bash scripts/uv_sync_extras.sh
```

## Documentation

The full documentation lives under [`docs/`](docs/index.md) and follows the Diátaxis framework:

- [Tutorials](docs/tutorials/quickstart.md) — end-to-end walkthroughs.
- [How-to guides](docs/how-to-guides/configure-pipeline.md) — targeted tasks such as configuring profiles or enabling observability. See the [dependency profile guide](docs/how-to-guides/dependency-profiles.md) to pick the right extras.
- [Reference](docs/reference/cli.md) — command syntax, data model, and expectation catalogue.
- [Explanations](docs/explanations/architecture.md) — architectural decisions and platform scope.
- [Roadmap](docs/roadmap.md) — delivery status, quality gates, and tracked follow-ups.

## Contributing

Read the [documentation contributing guide](docs/CONTRIBUTING.md) and [style guide](docs/style.md), then submit pull requests using Conventional Commits. Run the consolidated QA suite before opening a PR:

```bash
make qa
```

The `qa` target runs Ruff formatting and linting, pytest with coverage, mypy (strict for the pipeline configuration module and QA tooling), Bandit, detect-secrets, and repository pre-commit hooks so local results match CI.

Join the conversation in the `#hotpass` Slack channel or open an issue using the templates under `.github/ISSUE_TEMPLATE/`.
