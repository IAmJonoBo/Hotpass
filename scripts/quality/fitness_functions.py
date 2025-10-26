"""Evaluate automated fitness functions for Hotpass."""

from __future__ import annotations

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src" / "hotpass"


class FitnessFailure(Exception):
    """Raised when a fitness function fails."""


def check_module_length(module: str, max_lines: int) -> None:
    path = SRC_ROOT / module
    line_count = sum(1 for _ in path.open("r", encoding="utf-8"))
    if line_count > max_lines:
        raise FitnessFailure(f"{module} exceeds {max_lines} lines ({line_count})")


def check_import(module: str, module_path: str, symbol: str) -> None:
    path = SRC_ROOT / module
    tree = ast.parse(path.read_text(encoding="utf-8"))
    if not any(
        isinstance(node, ast.ImportFrom)
        and node.module == module_path
        and any(alias.name == symbol for alias in node.names)
        for node in ast.walk(tree)
    ):
        raise FitnessFailure(f"{module} missing instrumentation import {symbol} from {module_path}")


def check_public_api(module: str, symbols: list[str]) -> None:
    path = SRC_ROOT / module
    tree = ast.parse(path.read_text(encoding="utf-8"))
    exported: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "__all__":
                value = node.value
                if isinstance(value, ast.List | ast.Tuple):
                    for element in value.elts:
                        if isinstance(element, ast.Constant) and isinstance(element.value, str):
                            exported.add(element.value)
    missing = [symbol for symbol in symbols if symbol not in exported]
    if missing:
        raise FitnessFailure(f"{module} missing public exports: {missing}")


def main() -> None:
    checks = [
        lambda: check_module_length("pipeline.py", 1300),
        lambda: check_module_length("pipeline_enhanced.py", 200),
        lambda: check_import(
            "observability.py",
            "opentelemetry.sdk.trace.export",
            "BatchSpanProcessor",
        ),
        lambda: check_public_api("__init__.py", ["run_pipeline", "PipelineConfig"]),
    ]

    failures: list[str] = []
    for check in checks:
        try:
            check()
        except FitnessFailure as exc:  # pragma: no cover - exit path
            failures.append(str(exc))

    if failures:
        for failure in failures:
            print(f"❌ {failure}")
        raise SystemExit(1)

    print("✅ Fitness functions satisfied")


if __name__ == "__main__":
    main()
