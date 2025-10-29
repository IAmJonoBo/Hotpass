from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from hotpass import cli


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _write_config(path: Path, *, input_dir: str = "./data") -> Path:
    config_path = path / "config.toml"
    config_path.write_text(
        dedent(
            f"""
            [pipeline]
            input_dir = "{input_dir}"
            output_path = "./dist/refined.xlsx"
            dist_dir = "./dist"

            [governance]
            intent = ["Refine baseline dataset"]
            data_owner = "Data Governance"
            classification = "internal"
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return config_path


def test_doctor_reports_summary_when_workspace_ready(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    config_path = _write_config(tmp_path)
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "sample.xlsx").write_bytes(b"")
    (tmp_path / "dist").mkdir()

    monkeypatch.chdir(tmp_path)
    exit_code = cli.main(["doctor", "--config", str(config_path)])
    captured = capsys.readouterr()

    expect(exit_code == 0, "doctor should exit successfully when checks pass")
    expect("Environment diagnostics" in captured.out, "environment header missing")
    expect("Health score" in captured.out, "summary should include health score")


def test_doctor_flags_missing_directories(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    config_path = _write_config(tmp_path, input_dir="./missing")

    monkeypatch.chdir(tmp_path)
    exit_code = cli.main(["doctor", "--config", str(config_path)])
    captured = capsys.readouterr()

    expect(exit_code == 1, "doctor should fail when directories are missing")
    expect("FAIL" in captured.out, "failure details should be surfaced")
    expect("missing" in captured.out, "missing directory should be reported")
