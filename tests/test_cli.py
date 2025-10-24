from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

import hotpass.cli as cli


def _collect_json_lines(output: str) -> list[dict[str, Any]]:
    lines = [line for line in output.strip().splitlines() if line.strip()]
    return [json.loads(line) for line in lines]


def test_cli_outputs_json_summary(
    sample_data_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output_path = tmp_path / "refined.xlsx"

    exit_code = cli.main(
        [
            "--input-dir",
            str(sample_data_dir),
            "--output-path",
            str(output_path),
            "--log-format",
            "json",
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    log_records = _collect_json_lines(captured.out)
    summary = next(item for item in log_records if item["event"] == "pipeline.summary")

    assert summary["data"]["total_records"] == 2
    assert summary["data"]["expectations_passed"] is True
    metrics = summary["data"].get("performance_metrics")
    assert metrics is not None
    assert metrics["total_seconds"] >= 0.0
    assert metrics["rows_per_second"] > 0.0
    assert output_path.exists()


def test_cli_writes_markdown_report(
    sample_data_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output_path = tmp_path / "refined.xlsx"
    report_path = tmp_path / "report.md"

    exit_code = cli.main(
        [
            "--input-dir",
            str(sample_data_dir),
            "--output-path",
            str(output_path),
            "--report-path",
            str(report_path),
            "--report-format",
            "markdown",
            "--log-format",
            "json",
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    log_records = _collect_json_lines(captured.out)
    assert any(item["event"] == "report.write" for item in log_records)

    assert report_path.exists()
    contents = report_path.read_text()
    assert "Hotpass Quality Report" in contents
    assert "Total records" in contents
    assert "Performance Metrics" in contents


def test_cli_merges_config_file(
    sample_data_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output_path = tmp_path / "refined.xlsx"
    dist_dir = tmp_path / "dist"
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps({"archive": True, "log_format": "json", "dist_dir": str(dist_dir)})
    )

    exit_code = cli.main(
        [
            "--config",
            str(config_path),
            "--input-dir",
            str(sample_data_dir),
            "--output-path",
            str(output_path),
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    log_records = _collect_json_lines(captured.out)
    archive_event = next(item for item in log_records if item["event"] == "archive.created")

    assert output_path.exists()
    assert Path(archive_event["data"]["path"]).exists()
    assert archive_event["data"]["path"].startswith(str(dist_dir))


def test_cli_supports_rich_logging(
    sample_data_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output_path = tmp_path / "refined.xlsx"
    report_path = tmp_path / "report.html"
    dist_dir = tmp_path / "dist"

    exit_code = cli.main(
        [
            "--input-dir",
            str(sample_data_dir),
            "--output-path",
            str(output_path),
            "--log-format",
            "rich",
            "--report-path",
            str(report_path),
            "--archive",
            "--dist-dir",
            str(dist_dir),
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Hotpass Quality Report" in captured.out
    assert "Archive created" in captured.out
    assert "Load seconds" in captured.out
    assert report_path.exists()
    assert report_path.suffix == ".html"


def test_cli_accepts_excel_tuning_options(
    sample_data_dir: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_path = tmp_path / "refined.xlsx"
    stage_dir = tmp_path / "stage"

    calls: list[Path] = []

    def _fake_to_parquet(self: pd.DataFrame, path: Path, *, index: bool = False) -> None:
        calls.append(Path(path))

    monkeypatch.setattr(pd.DataFrame, "to_parquet", _fake_to_parquet, raising=False)

    exit_code = cli.main(
        [
            "--input-dir",
            str(sample_data_dir),
            "--output-path",
            str(output_path),
            "--log-format",
            "json",
            "--excel-chunk-size",
            "1",
            "--excel-stage-dir",
            str(stage_dir),
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    summary = next(
        item for item in _collect_json_lines(captured.out) if item["event"] == "pipeline.summary"
    )
    assert summary["data"]["total_records"] == 2
    assert calls, "staging to parquet should be attempted when a stage directory is provided"


def test_cli_parse_args_missing_config(tmp_path: Path) -> None:
    missing = tmp_path / "missing.toml"
    with pytest.raises(FileNotFoundError):
        cli.parse_args(["--config", str(missing)])


def test_cli_rejects_invalid_config_values(tmp_path: Path) -> None:
    config_path = tmp_path / "bad.json"
    config_path.write_text(json.dumps({"log_format": "yaml"}))

    with pytest.raises(ValueError):
        cli.parse_args(["--config", str(config_path)])


def test_cli_accepts_toml_config(
    sample_data_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config_path = tmp_path / "options.toml"
    report_path = tmp_path / "report.md"
    dist_dir = tmp_path / "dist"
    config_path.write_text(
        "archive = true\n"
        'log_format = "json"\n'
        f'report_path = "{report_path}"\n'
        f'dist_dir = "{dist_dir}"\n'
    )

    output_path = tmp_path / "refined.xlsx"
    exit_code = cli.main(
        [
            "--config",
            str(config_path),
            "--input-dir",
            str(sample_data_dir),
            "--output-path",
            str(output_path),
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    records = _collect_json_lines(captured.out)
    assert any(item["event"] == "report.write" for item in records)
    assert report_path.exists()


def test_structured_logger_rich_error_output(
    capsys: pytest.CaptureFixture[str],
) -> None:
    logger = cli.StructuredLogger("rich")
    logger.log_error("something went wrong")

    captured = capsys.readouterr()
    assert "something went wrong" in captured.out
