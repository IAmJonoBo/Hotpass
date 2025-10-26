from __future__ import annotations

import hashlib
import zipfile
from datetime import UTC, datetime, tzinfo
from pathlib import Path

import pandas as pd
import pytest

pytest.importorskip("frictionless")

import hotpass.artifacts as artifacts  # noqa: E402
from hotpass.artifacts import create_refined_archive  # noqa: E402


def test_create_refined_archive_embeds_checksum(tmp_path: Path) -> None:
    excel_path = tmp_path / "refined_data.xlsx"
    df = pd.DataFrame({"organization_name": ["Aero School"], "province": ["Gauteng"]})
    df.to_excel(excel_path, index=False)

    timestamp = datetime(2025, 1, 1, 12, 30, tzinfo=UTC)
    archive_dir = tmp_path / "dist"

    archive_path = create_refined_archive(excel_path, archive_dir, timestamp=timestamp)

    assert archive_path.exists()
    expected_prefix = "refined-data-20250101T123000Z-"
    assert archive_path.name.startswith(expected_prefix)

    with zipfile.ZipFile(archive_path) as zf:
        assert excel_path.name in zf.namelist()
        sha_sums = zf.read("SHA256SUMS").decode().strip()

    digest = hashlib.sha256(excel_path.read_bytes()).hexdigest()[:12]
    assert archive_path.stem.endswith(digest)
    assert sha_sums == f"{digest}  {excel_path.name}"


def test_create_refined_archive_defaults_to_utc(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    excel_path = tmp_path / "refined_data.xlsx"
    pd.DataFrame({"organization_name": ["Heli Ops"]}).to_excel(excel_path, index=False)

    fixed_timestamp = datetime(2025, 1, 2, 15, 45, tzinfo=UTC)

    class _FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz: tzinfo | None = None) -> datetime:  # type: ignore[override]
            return fixed_timestamp

    monkeypatch.setattr(artifacts, "datetime", _FrozenDateTime)

    archive_path = create_refined_archive(excel_path, tmp_path)
    digest = hashlib.sha256(excel_path.read_bytes()).hexdigest()[:12]

    assert archive_path.name == f"refined-data-20250102T154500Z-{digest}.zip"
