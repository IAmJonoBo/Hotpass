"""Governed data contract validation utilities."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import cast

import pandas as pd
from frictionless import Schema
from frictionless.exception import FrictionlessException
from frictionless.resources import TableResource

from .error_handling import DataContractError

try:  # pragma: no cover - Great Expectations is an optional dependency
    from great_expectations.core.batch import Batch
    from great_expectations.core.expectation_suite import ExpectationSuite
    from great_expectations.core.expectation_validation_result import (
        ExpectationSuiteValidationResult,
    )
    from great_expectations.data_context.data_context import context_factory as ge_context_factory
    from great_expectations.data_context.data_context.ephemeral_data_context import (
        EphemeralDataContext,
    )
    from great_expectations.data_context.types.base import (
        DataContextConfig,
        InMemoryStoreBackendDefaults,
    )
    from great_expectations.execution_engine.pandas_execution_engine import PandasExecutionEngine
    from great_expectations.expectations.expectation_configuration import ExpectationConfiguration
    from great_expectations.validator.validator import Validator
except ImportError as exc:  # pragma: no cover - handled via tests when GE absent
    raise RuntimeError("Great Expectations must be installed for contract validation") from exc


def _project_root() -> Path:
    """Find the project root by searching for a marker file (pyproject.toml) upwards."""
    current = Path(__file__).resolve().parent
    for parent in [current] + list(current.parents):
        if (parent / "pyproject.toml").is_file():
            return parent
    raise RuntimeError("Could not find project root (pyproject.toml not found in any parent directory)")


def _resource_path(folder: str, name: str) -> Path:
    package_candidate = resources.files("hotpass") / folder / name
    with resources.as_file(package_candidate) as path:
        if Path(path).is_file():
            return Path(path)
    fallback = _project_root() / folder / name
    if fallback.exists():
        return fallback
    raise FileNotFoundError(f"Unable to resolve resource {folder}/{name}")


def _load_schema(name: str) -> Schema:
    schema_path = _resource_path("schemas", name)
    with schema_path.open("r", encoding="utf-8") as handle:
        descriptor = json.load(handle)
    return Schema(descriptor=descriptor)


def _load_expectation_suite(name: str) -> ExpectationSuite:
    suite_path = _resource_path("data_expectations", name)
    with suite_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    expectations = [
        ExpectationConfiguration(
            type=item["expectation_type"],
            kwargs=item.get("kwargs", {}),
            meta=item.get("meta"),
        )
        for item in payload.get("expectations", [])
    ]
    suite = ExpectationSuite(
        name=payload["expectation_suite_name"],
        expectations=expectations,
        meta=payload.get("meta", {}),
    )
    return suite


def validate_with_frictionless(
    df: pd.DataFrame,
    *,
    schema_descriptor: str,
    table_name: str,
    source_file: str,
) -> None:
    schema = _load_schema(schema_descriptor)
    sanitized = df.where(pd.notnull(df), None).copy()
    for field in schema.fields:
        if field.type == "string" and field.name in sanitized.columns:
            sanitized[field.name] = sanitized[field.name].astype("string")
    resource = TableResource(data=sanitized.to_dict(orient="records"), schema=schema)
    try:
        report = resource.validate()
    except FrictionlessException as exc:  # pragma: no cover - surfaced via report
        raise DataContractError.from_frictionless(
            table_name,
            expected_fields=[field.name for field in schema.fields],
            actual_fields=list(df.columns),
            issues=[str(exc)],
            source_file=source_file,
        ) from exc

    if report.valid:
        return

    issues: list[str] = []
    for task in report.tasks:
        for error in task.errors:
            issues.append(error.note)

    raise DataContractError.from_frictionless(
        table_name,
        expected_fields=[field.name for field in schema.fields],
        actual_fields=list(df.columns),
        issues=issues,
        source_file=source_file,
    )


def validate_with_expectations(
    df: pd.DataFrame,
    *,
    suite_descriptor: str,
    source_file: str,
) -> None:
    suite = _load_expectation_suite(suite_descriptor)
    config = DataContextConfig(
        config_version=4,
        expectations_store_name="expectations_store",
        validation_results_store_name="validation_results_store",
        checkpoint_store_name="checkpoint_store",
        data_docs_sites={},
        analytics_enabled=False,
        store_backend_defaults=InMemoryStoreBackendDefaults(init_temp_docs_sites=False),
    )

    with EphemeralDataContext(project_config=config) as context:
        project_manager = ge_context_factory.project_manager
        previous_project = project_manager.get_project()
        project_manager.set_project(context)

        try:
            validator = Validator(
                execution_engine=PandasExecutionEngine(),
                expectation_suite=suite,
                batches=[Batch(data=df)],
                data_context=context,
            )
            validator.set_default_expectation_argument("catch_exceptions", True)
            results = cast(ExpectationSuiteValidationResult, validator.validate())
        finally:
            project_manager.set_project(previous_project)
    if results.success:
        return

    failures: list[str] = []
    for result in results.results:
        if result.success:
            continue
        expectation_config = result.expectation_config
        if expectation_config is None:
            failures.append("Expectation without configuration metadata")
            continue
        expectation = expectation_config.type
        kwargs = expectation_config.kwargs or {}
        column = kwargs.get("column")
        if column:
            expectation = f"{expectation} ({column})"
        unexpected = result.result.get("unexpected_list")
        if unexpected:
            failures.append(f"{expectation}: unexpected {unexpected[:3]}")
        else:
            failures.append(expectation)

    raise DataContractError.from_expectations(
        suite.name or suite.meta.get("expectation_suite_name", "unknown_suite"),
        failures=failures,
        source_file=source_file,
    )


def load_schema_descriptor(name: str) -> dict[str, object]:
    """Return a raw schema descriptor for downstream metadata exporters."""
    schema_path = _resource_path("schemas", name)
    with schema_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)
