"""Evaluate SBOM against policy requirements."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def evaluate(sbom_path: Path) -> None:
    data = json.loads(sbom_path.read_text(encoding="utf-8"))
    metadata = data.get("metadata", {})
    component = metadata.get("component", {})
    if component.get("name") != "hotpass":
        raise SystemExit("SBOM missing Hotpass component entry")
    components = data.get("components", [])
    if not components:
        raise SystemExit("SBOM missing component list")
    print("Policy evaluation passed")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: evaluate_policy.py <sbom.json>")
    evaluate(Path(sys.argv[1]))


if __name__ == "__main__":
    main()
