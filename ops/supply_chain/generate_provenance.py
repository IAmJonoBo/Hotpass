"""Generate in-toto provenance statement for build artifacts."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ARTIFACT_GLOBS = ["dist/*.whl", "dist/*.tar.gz"]


def sha256_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_subjects() -> list[dict[str, Any]]:
    subjects: list[dict[str, Any]] = []
    for glob in ARTIFACT_GLOBS:
        for artifact in Path().glob(glob):
            subjects.append(
                {
                    "name": artifact.name,
                    "uri": str(artifact.resolve()),
                    "digest": {"sha256": sha256_digest(artifact)},
                }
            )
    return subjects


def generate_provenance(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    statement = {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": build_subjects(),
        "predicateType": "https://slsa.dev/provenance/v1",
        "predicate": {
            "buildType": "https://github.com/IAmJonoBo/Hotpass/.github/workflows/process-data.yml@v1",
            "builder": {
                "id": "https://github.com/IAmJonoBo/Hotpass/actions",
            },
            "buildConfig": {
                "command": "uv run uv build",
                "environment": "github-actions",
            },
            "metadata": {
                "buildStartedOn": datetime.now(UTC).isoformat(),
                "buildFinishedOn": datetime.now(UTC).isoformat(),
            },
        },
    }
    output_path = output_dir / "provenance.json"
    output_path.write_text(json.dumps(statement, indent=2))
    return output_path


def main() -> None:
    provenance_path = generate_provenance(Path("dist/provenance"))
    print(f"Provenance statement written to {provenance_path}")


if __name__ == "__main__":
    main()
