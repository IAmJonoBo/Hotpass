"""Tests covering Prefect deployment manifests and registration logic."""

from __future__ import annotations

import sys
import types
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

prefect_module = pytest.importorskip("prefect")
prefect_flow = prefect_module.flow

for module_name in ("duckdb", "polars", "pyarrow"):
    sys.modules.setdefault(module_name, types.ModuleType(module_name))

MODULE_NAME = "hotpass.prefect.deployments"
module_path = Path(__file__).resolve().parents[1] / "src" / "hotpass" / "prefect" / "deployments.py"
spec = spec_from_file_location(MODULE_NAME, module_path)
if spec is None or spec.loader is None:  # pragma: no cover - defensive guard
    raise RuntimeError("Unable to load deployment module spec")

hotpass_pkg = sys.modules.setdefault("hotpass", types.ModuleType("hotpass"))
hotpass_pkg.__path__ = []  # type: ignore[attr-defined]
prefect_pkg = sys.modules.setdefault("hotpass.prefect", types.ModuleType("hotpass.prefect"))
hotpass_pkg.prefect = prefect_pkg  # type: ignore[attr-defined]

deployments = module_from_spec(spec)
sys.modules[MODULE_NAME] = deployments
spec.loader.exec_module(deployments)
prefect_pkg.deployments = deployments  # type: ignore[attr-defined]

if "hotpass.orchestration" not in sys.modules:
    orchestration_module = types.ModuleType("hotpass.orchestration")

    @prefect_flow(name="hotpass-refinement-pipeline", validate_parameters=False)
    def refinement_pipeline_flow(**kwargs: object) -> dict[str, object]:
        return dict(kwargs)

    @prefect_flow(name="hotpass-backfill", validate_parameters=False)
    def backfill_pipeline_flow(**kwargs: object) -> dict[str, object]:
        return dict(kwargs)

    orchestration_module.refinement_pipeline_flow = refinement_pipeline_flow
    orchestration_module.backfill_pipeline_flow = backfill_pipeline_flow
    sys.modules["hotpass.orchestration"] = orchestration_module


def expect(condition: bool, message: str) -> None:
    """Fail with a descriptive message when the condition is false."""

    if not condition:
        pytest.fail(message)


@pytest.fixture(scope="module")
def loaded_specs() -> dict[str, deployments.DeploymentSpec]:
    specs = deployments.load_deployment_specs(Path("prefect"))
    expect(bool(specs), "No deployment specs discovered under the prefect/ directory.")
    return {spec.identifier: spec for spec in specs}


def test_specs_include_refinement_and_backfill(
    loaded_specs: dict[str, deployments.DeploymentSpec],
) -> None:
    """The repo should ship manifests for both refinement and backfill flows."""

    expected_keys = {"refinement", "backfill"}
    expect(
        set(loaded_specs) == expected_keys,
        f"Deployment manifest identifiers should be {expected_keys} but were {set(loaded_specs)}.",
    )


def test_refinement_manifest_encodes_incremental_resume_options(
    loaded_specs: dict[str, deployments.DeploymentSpec],
) -> None:
    """The refinement manifest encodes parameters for incremental and resumable runs."""

    spec = loaded_specs["refinement"]
    expect(
        spec.parameters.get("backfill") is False,
        "Refinement flow should disable backfill by default.",
    )
    expect(
        spec.parameters.get("incremental") is True,
        "Refinement flow should run incrementally.",
    )
    expect(
        "since" in spec.parameters,
        (
            "Refinement deployment should expose a 'since' parameter "
            "so runs can resume from checkpoints."
        ),
    )
    schedule = spec.schedule
    expect(schedule is not None, "Refinement manifest should include a schedule block.")
    if schedule is not None:
        expect(
            schedule.kind == "cron",
            "Refinement schedule must use cron semantics.",
        )
        expect(
            schedule.timezone == "UTC",
            "Refinement schedule should explicitly set UTC timezone.",
        )


@pytest.mark.parametrize("identifier", ["refinement", "backfill"])
def test_build_runner_deployment_renders_prefect_model(
    identifier: str, loaded_specs: dict[str, deployments.DeploymentSpec]
) -> None:
    """Deployment manifests compile into Prefect RunnerDeployment objects."""

    pytest.importorskip("prefect.deployments.runner")
    spec = loaded_specs[identifier]
    runner_deployment = deployments.build_runner_deployment(spec)
    expect(
        runner_deployment.name == spec.name,
        "Runner deployment name should match manifest name.",
    )
    expect(
        runner_deployment.parameters == spec.parameters,
        "Runner deployment should propagate manifest parameters verbatim.",
    )
    if spec.schedule is not None:
        expect(
            runner_deployment.schedules is not None and len(runner_deployment.schedules) == 1,
            "Scheduled deployments should yield exactly one schedule entry.",
        )


class DummyRunnerDeployRecorder:
    def __init__(self) -> None:
        self.calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def __call__(self, *deployments_args: object, **kwargs: object) -> list[str]:
        self.calls.append((deployments_args, kwargs))
        return ["deployment-id"]


def test_deploy_pipeline_filters_and_registers(monkeypatch: pytest.MonkeyPatch) -> None:
    """Deploy pipeline should register the selected deployment manifests via Prefect runner API."""

    pytest.importorskip("prefect.deployments.runner")
    monkeypatch.setattr(deployments, "PREFECT_AVAILABLE", True, raising=False)

    recorder = DummyRunnerDeployRecorder()
    monkeypatch.setattr(deployments.runner, "deploy", recorder, raising=False)

    registered = deployments.deploy_pipeline(flows=("refinement",))

    expect(registered == ["deployment-id"], "Runner should return the Prefect deployment IDs.")
    expect(len(recorder.calls) == 1, "Runner deploy should have been invoked once.")
    args, kwargs = recorder.calls[0]
    expect(len(args) == 1, "Only the selected refinement deployment should be registered.")
    expect(kwargs.get("build") is False, "Deploy should skip image builds for in-repo flows.")
    expect(kwargs.get("push") is False, "Deploy should avoid pushing images during registration.")


def test_deploy_pipeline_without_prefect_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Deploying when Prefect is unavailable should raise a runtime error."""

    monkeypatch.setattr(deployments, "PREFECT_AVAILABLE", False, raising=False)
    with pytest.raises(RuntimeError, match="Prefect is not installed"):
        deployments.deploy_pipeline()
