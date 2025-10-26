from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd
import pytest
from rich.console import Console

pytest.importorskip("frictionless")

import hotpass.cli as cli  # noqa: E402
from hotpass.pipeline import PipelineConfig, QualityReport  # noqa: E402


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


def test_cli_json_logs_redact_sensitive_fields(capsys: pytest.CaptureFixture[str]) -> None:
    logger = cli.StructuredLogger("json", ["email"])
    report = QualityReport(
        total_records=1,
        invalid_records=0,
        schema_validation_errors=[],
        expectations_passed=True,
        expectation_failures=[],
        source_breakdown={},
        data_quality_distribution={"mean": 1.0, "min": 1.0, "max": 1.0},
        performance_metrics={},
        audit_trail=[{"contact_email": "sensitive@example.com"}],
    )

    logger.log_summary(report)

    captured = capsys.readouterr()
    records = _collect_json_lines(captured.out)
    summary = next(item for item in records if item["event"] == "pipeline.summary")
    masked = summary["data"]["audit_trail"][0]["contact_email"]
    assert masked == cli.REDACTED_PLACEHOLDER


class _RecordingTask:
    def __init__(self, task_id: int, description: str, total: int) -> None:
        self.id = task_id
        self.description = description
        self.total = total
        self.completed = 0


class _RecordingProgress:
    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401 - parity with Progress
        self.tasks: list[_RecordingTask] = []
        self.log_messages: list[str] = []

    def __enter__(self) -> _RecordingProgress:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - no cleanup needed
        return None

    def add_task(self, description: str, total: int = 1) -> int:
        task_id = len(self.tasks) + 1
        task = _RecordingTask(task_id, description, total)
        self.tasks.append(task)
        return task_id

    def update(
        self,
        task_id: int,
        *,
        total: int | None = None,
        completed: int | None = None,
    ) -> None:
        task = next(task for task in self.tasks if task.id == task_id)
        if total is not None:
            task.total = total
        if completed is not None:
            task.completed = completed

    def log(self, message: str) -> None:
        self.log_messages.append(message)


def test_pipeline_progress_throttles_high_volume_events() -> None:
    console = Console(record=True)
    progress = cli.PipelineProgress(
        console,
        progress_factory=_RecordingProgress,
        throttle_seconds=0.01,
    )

    with progress:
        progress.handle_event(cli.PIPELINE_EVENT_START, {})
        progress.handle_event(cli.PIPELINE_EVENT_AGGREGATE_STARTED, {"total": 100})
        for completed in range(1000):
            progress.handle_event(
                cli.PIPELINE_EVENT_AGGREGATE_PROGRESS,
                {"completed": completed},
            )
        progress.handle_event(
            cli.PIPELINE_EVENT_AGGREGATE_COMPLETED,
            {"aggregated_records": 100, "conflicts": 0},
        )

    recording_progress: _RecordingProgress = progress._progress  # type: ignore[assignment]
    aggregate_task = next(
        task for task in recording_progress.tasks if task.description == "Aggregating organisations"
    )
    assert aggregate_task.completed == aggregate_task.total
    suppression_logs = [msg for msg in recording_progress.log_messages if "Suppressed" in msg]
    assert suppression_logs, "high volume updates should emit suppression summary"


def test_cli_attaches_progress_listener_when_rich_logging(
    sample_data_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured_listener: Callable[[str, dict[str, Any]], None] | None = None

    class DummyResult:
        def __init__(self) -> None:
            self.refined = pd.DataFrame()
            self.quality_report = QualityReport(
                total_records=0,
                invalid_records=0,
                schema_validation_errors=[],
                expectations_passed=True,
                expectation_failures=[],
                source_breakdown={},
                data_quality_distribution={"mean": 0.0, "min": 0.0, "max": 0.0},
                performance_metrics={},
            )

    def fake_run_pipeline(config: PipelineConfig) -> DummyResult:
        nonlocal captured_listener
        captured_listener = config.progress_listener
        return DummyResult()

    monkeypatch.setattr(cli, "run_pipeline", fake_run_pipeline)

    exit_code = cli.main(
        [
            "--input-dir",
            str(sample_data_dir),
            "--output-path",
            str(tmp_path / "refined.xlsx"),
            "--log-format",
            "rich",
        ]
    )

    assert exit_code == 0
    assert captured_listener is not None


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
