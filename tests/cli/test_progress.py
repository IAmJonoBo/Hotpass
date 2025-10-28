"""Tests ensuring pipeline progress rendering remains responsive."""

from __future__ import annotations

from typing import Any

from rich.console import Console

from hotpass import cli
from hotpass.pipeline import (
    PIPELINE_EVENT_AGGREGATE_COMPLETED,
    PIPELINE_EVENT_AGGREGATE_PROGRESS,
    PIPELINE_EVENT_AGGREGATE_STARTED,
    PIPELINE_EVENT_START,
)


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
        progress.handle_event(PIPELINE_EVENT_START, {})
        progress.handle_event(PIPELINE_EVENT_AGGREGATE_STARTED, {"total": 100})
        for completed in range(1000):
            progress.handle_event(
                PIPELINE_EVENT_AGGREGATE_PROGRESS,
                {"completed": completed},
            )
        progress.handle_event(
            PIPELINE_EVENT_AGGREGATE_COMPLETED,
            {"aggregated_records": 100, "conflicts": 0},
        )

    recording_progress: _RecordingProgress = progress._progress  # type: ignore[assignment]
    aggregate_task = next(
        task for task in recording_progress.tasks if task.description == "Aggregating organisations"
    )
    assert aggregate_task.completed == aggregate_task.total
    suppression_logs = [msg for msg in recording_progress.log_messages if "Suppressed" in msg]
    assert suppression_logs, "high volume updates should emit suppression summary"
