from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

from rich.console import Console

from tests.helpers.assertions import expect

BOOTSTRAP_MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "idp" / "bootstrap.py"


def _load_bootstrap_module() -> ModuleType:
    if "scripts" not in sys.modules:
        scripts_pkg = ModuleType("scripts")
        scripts_pkg.__path__ = [str(BOOTSTRAP_MODULE_PATH.parent.parent)]
        sys.modules["scripts"] = scripts_pkg
    if "scripts.idp" not in sys.modules:
        idp_pkg = ModuleType("scripts.idp")
        idp_pkg.__path__ = [str(BOOTSTRAP_MODULE_PATH.parent)]
        sys.modules["scripts.idp"] = idp_pkg

    spec = importlib.util.spec_from_file_location("scripts.idp.bootstrap", BOOTSTRAP_MODULE_PATH)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive guard
        msg = "Unable to load bootstrap module specification"
        raise RuntimeError(msg)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


bootstrap = _load_bootstrap_module()


def test_build_bootstrap_plan_includes_supply_chain(tmp_path: Path) -> None:
    env_file = tmp_path / ".env.hotpass"
    plan = bootstrap.build_bootstrap_plan(["dev", "docs"], "hotpass-dev", env_file, None)

    commands = [step.command for step in plan if step.command]
    expect(["uv", "venv"] in commands, "Bootstrap plan should include uv venv command")
    expect(
        ["uv", "run", "python", "scripts/supply_chain/generate_sbom.py"] in commands,
        "Bootstrap plan should include SBOM generation",
    )
    expect(
        [
            "uv",
            "run",
            "python",
            "scripts/supply_chain/generate_provenance.py",
        ]
        in commands,
        "Bootstrap plan should include provenance generation",
    )


def test_env_step_creates_file(tmp_path: Path) -> None:
    env_file = tmp_path / ".env.hotpass"
    plan = bootstrap.build_bootstrap_plan(
        ["dev"], "demo-profile", env_file, "https://vault.example"
    )
    env_step = next(step for step in plan if step.action is not None)

    console = Console(record=True)
    exit_code = env_step.run(True, console)

    expect(exit_code == 0, "Environment step should succeed")
    contents = env_file.read_text().splitlines()
    expect(
        "HOTPASS_PREFECT_PROFILE=demo-profile" in contents,
        "Env file should contain HOTPASS_PREFECT_PROFILE",
    )
    expect(
        "HOTPASS_VAULT_ADDR=https://vault.example" in contents,
        "Env file should contain HOTPASS_VAULT_ADDR",
    )
