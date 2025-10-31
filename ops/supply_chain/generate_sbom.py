"""Generate CycloneDX SBOM for the Hotpass project."""

from __future__ import annotations

import subprocess  # nosec B404
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def generate_sbom(output_dir: Path) -> Path:
    """Run cyclonedx-bom to produce an SBOM in JSON format."""

    output_dir.mkdir(parents=True, exist_ok=True)
    sbom_path = output_dir / "hotpass-sbom.json"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "cyclonedx_py",
            "environment",
            "--of",
            "JSON",
            "-o",
            str(sbom_path),
            "--pyproject",
            str((PROJECT_ROOT / "pyproject.toml").resolve()),
            sys.executable,
        ],
        check=True,
    )  # nosec B603
    return sbom_path


def main() -> None:
    """Entry point for CLI usage."""

    sbom_path = generate_sbom(Path("dist/sbom"))
    print(f"SBOM written to {sbom_path}")


if __name__ == "__main__":
    main()
