# ADR-0007: CLI onboarding commands for workspace bootstrap

**Status:** Accepted

**Date:** 2025-12-08

## Context

Hotpass users relied on manual steps to set up configuration files and verify their environment
before running the pipeline. Documentation referenced ad-hoc scripts and expected contributors to
assemble directories, Prefect manifests, and governance metadata by hand. Review feedback on the
quickstart tutorial highlighted that new operators struggled to locate the right configuration
files and often skipped critical governance checks.

## Decision

Introduce two dedicated CLI subcommands to streamline onboarding:

1. `hotpass init` scaffolds a workspace with sample configuration, a matching profile, and a
   Prefect deployment stub so operators can start with a consistent project layout.
2. `hotpass doctor` layers environment diagnostics on top of `ConfigDoctor`, reporting Python
   compatibility, directory readiness, and governance issues. An optional `--autofix` flag applies
   safe governance defaults before the report prints.

Both commands integrate with the existing parser and honour shared options such as `--config` and
`--profile`. Tutorials and how-to guides instruct users to run the commands before executing the
pipeline so the workflow becomes part of the canonical onboarding path.

## Consequences

### Positive

- New projects start with a reproducible directory structure and sample deployment artefacts.
- Governance checks become part of the default workflow, reducing the risk of missing intent or
  data owner metadata.
- Documentation can reference concrete commands rather than bespoke scripts, improving clarity.

### Neutral

- Additional CLI help output introduces two more commands that operators must learn.

### Negative

- Maintaining the scaffold templates requires periodic updates when configuration defaults change.

## Alternatives considered

1. **Document manual setup steps** — Rejected because the existing tutorials already struggled with
   manual instructions and still left gaps in governance validation.
2. **Bundle scaffolding scripts outside the CLI** — Rejected to avoid divergence between documented
   workflows and the supported CLI entry points.

## References

- `apps/data-platform/hotpass/cli/commands/init.py`
- `apps/data-platform/hotpass/cli/commands/doctor.py`
- `docs/tutorials/quickstart.md`
- `docs/reference/cli.md`
- `docs/how-to-guides/configure-pipeline.md`
