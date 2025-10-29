from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("duckdb")
pytest.importorskip("polars")
pytest.importorskip("pyarrow")

from hotpass import orchestration
from hotpass.pipeline.config import PipelineConfig
from tests.fixtures.lineage import CapturedLineage


def expect(condition: bool, message: str) -> None:
    """Fail the test with a descriptive assertion message."""

    if not condition:
        pytest.fail(message)


class _StubQualityReport:
    def __init__(self) -> None:
        self.expectations_passed = True

    def to_dict(self) -> dict[str, Any]:
        return {"expectations_passed": True}


class _StubPipelineResult:
    def __init__(self) -> None:
        self.quality_report = _StubQualityReport()
        self.refined = [1, 2]


def _successful_runner(config: PipelineConfig, **_: Any) -> _StubPipelineResult:
    return _StubPipelineResult()


def _failing_runner(config: PipelineConfig, **_: Any) -> None:
    raise RuntimeError("pipeline-error")


def test_execute_pipeline_emits_start_and_complete_events(
    tmp_path: Path, capture_lineage: CapturedLineage
) -> None:
    """Successful runs should emit START and COMPLETE lineage events."""

    input_dir = tmp_path / "inputs"
    input_dir.mkdir()
    (input_dir / "sample.xlsx").write_text("", encoding="utf-8")

    output_path = tmp_path / "refined.xlsx"
    config = PipelineConfig(input_dir=input_dir, output_path=output_path)

    summary = orchestration._execute_pipeline(
        config,
        runner=_successful_runner,
        runner_kwargs=None,
        archive=False,
        archive_dir=None,
    )

    expect(summary.success is True, "Expected summary to reflect a successful run.")

    events = capture_lineage.events
    expect(len(events) == 2, "Expected start and complete events to be recorded.")

    start_event, complete_event = events
    expect(start_event.eventType == "START", "First event should denote run start.")
    expect(
        complete_event.eventType == "COMPLETE",
        "Second event should denote run completion.",
    )
    expect(
        start_event.run.runId == complete_event.run.runId,
        "Run identifiers should remain stable across events.",
    )
    expect(
        any(output_path.name in dataset.name for dataset in complete_event.outputs),
        "Output datasets should include the refined workbook path.",
    )


def test_execute_pipeline_emits_fail_event_on_error(
    tmp_path: Path, capture_lineage: CapturedLineage
) -> None:
    """When the runner raises, the emitter should record a FAIL event."""

    input_dir = tmp_path / "inputs"
    input_dir.mkdir()
    (input_dir / "sample.xlsx").write_text("", encoding="utf-8")

    output_path = tmp_path / "refined.xlsx"
    config = PipelineConfig(input_dir=input_dir, output_path=output_path)

    with pytest.raises(RuntimeError):
        orchestration._execute_pipeline(
            config,
            runner=_failing_runner,
            runner_kwargs=None,
            archive=False,
            archive_dir=None,
        )

    events = capture_lineage.events
    expect(len(events) == 2, "Expected start and failure events to be recorded.")
    expect(events[-1].eventType == "FAIL", "Last event should denote run failure.")
