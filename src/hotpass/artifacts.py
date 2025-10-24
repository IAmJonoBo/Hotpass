"""Utilities for packaging refined Hotpass datasets."""

from __future__ import annotations

import hashlib
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def create_refined_archive(
    excel_path: Path,
    archive_dir: Path,
    *,
    timestamp: datetime | None = None,
    checksum_prefix_length: int = 12,
) -> Path:
    """Package the refined Excel output into a timestamped, checksum-stamped zip archive.

    Parameters
    ----------
    excel_path:
        Path to the refined Excel workbook produced by the pipeline.
    archive_dir:
        Directory that will receive the packaged archive.
    timestamp:
        Optional datetime override (used primarily for testing). When omitted the
        current UTC timestamp is used.
    checksum_prefix_length:
        Number of SHA256 characters to embed in the archive filename.
    """

    if not excel_path.exists():  # pragma: no cover - defensive guard
        msg = f"Refined workbook not found at {excel_path}"
        raise FileNotFoundError(msg)

    archive_dir.mkdir(parents=True, exist_ok=True)

    excel_bytes = excel_path.read_bytes()
    checksum = hashlib.sha256(excel_bytes).hexdigest()[:checksum_prefix_length]

    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    timestamp_label = timestamp.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    archive_name = f"refined-data-{timestamp_label}-{checksum}.zip"
    archive_path = archive_dir / archive_name

    with zipfile.ZipFile(
        archive_path, mode="w", compression=zipfile.ZIP_DEFLATED
    ) as zip_file:
        zip_file.write(excel_path, excel_path.name)
        zip_file.writestr("SHA256SUMS", f"{checksum}  {excel_path.name}\n")

    return archive_path


__all__ = ["create_refined_archive"]
