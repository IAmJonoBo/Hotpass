"""Tests for dashboard persistence helpers."""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

if "streamlit" not in sys.modules:
    sys.modules["streamlit"] = types.ModuleType("streamlit")

import hotpass.dashboard as dashboard
from hotpass.dashboard import load_pipeline_history, save_pipeline_run


class _FakeContext:
    """Basic context manager used for tabs, columns, and expanders."""

    def __enter__(self):  # noqa: D401 - trivial wrapper
        return self

    def __exit__(self, exc_type, exc, tb):  # type: ignore[override]
        return False


class FakeColumn(_FakeContext):
    def info(self, *_: object, **__: object) -> None:
        return None

    def metric(self, *_: object, **__: object) -> None:
        return None


class FakeTab(_FakeContext):
    def header(self, *_: object, **__: object) -> None:
        return None


class FakeExpander(_FakeContext):
    def json(self, *_: object, **__: object) -> None:
        return None

    def dataframe(self, *_: object, **__: object) -> None:
        return None


class FakeSidebar:
    def header(self, *_: object, **__: object) -> None:
        return None

    def text_input(self, _label: str, value: str = "", **_: object) -> str:
        return value

    def selectbox(self, _label: str, options: list[str], **_: object) -> str:
        return options[0]

    def number_input(self, _label: str, value: int = 0, **_: object) -> int:
        return value


class FakeStreamlit:
    """Minimal Streamlit shim capturing notable interactions."""

    def __init__(self) -> None:
        self.sidebar = FakeSidebar()
        self._button_pressed = False
        self.info_messages: list[str] = []
        self.success_messages: list[str] = []

    def set_button_response(self, pressed: bool) -> None:
        self._button_pressed = pressed

    def set_page_config(self, **_: object) -> None:
        return None

    def title(self, *_: object, **__: object) -> None:
        return None

    def markdown(self, *_: object, **__: object) -> None:
        return None

    def tabs(self, labels: list[str]) -> tuple[FakeTab, ...]:
        return tuple(FakeTab() for _ in labels)

    def columns(self, specs: list[int] | tuple[int, ...] | int) -> list[FakeColumn]:
        if isinstance(specs, int):
            count = specs
        else:
            count = len(specs)
        return [FakeColumn() for _ in range(count)]

    def button(self, *_: object, **__: object) -> bool:
        return self._button_pressed

    def spinner(self, *_: object, **__: object) -> _FakeContext:
        return _FakeContext()

    def header(self, *_: object, **__: object) -> None:
        return None

    def info(self, message: str, **_: object) -> None:
        self.info_messages.append(message)

    def warning(self, *_: object, **__: object) -> None:
        return None

    def success(self, message: str, **_: object) -> None:
        self.success_messages.append(message)

    def error(self, *_: object, **__: object) -> None:
        return None

    def exception(self, *_: object, **__: object) -> None:
        return None

    def metric(self, *_: object, **__: object) -> None:
        return None

    def subheader(self, *_: object, **__: object) -> None:
        return None

    def line_chart(self, *_: object, **__: object) -> None:
        return None

    def dataframe(self, *_: object, **__: object) -> None:
        return None

    def json(self, *_: object, **__: object) -> None:
        return None

    def expander(self, *_: object, **__: object) -> FakeExpander:
        return FakeExpander()


def test_load_pipeline_history_missing_file(tmp_path):
    """Loading history from a missing file should return an empty list."""

    history_file = tmp_path / "history.json"

    history = load_pipeline_history(history_file)

    assert history == []


def test_save_pipeline_run_appends_entries(tmp_path):
    """Saving multiple runs should append to the history file."""

    history_file = tmp_path / "logs" / "history.json"

    first = {"run": 1, "status": "success"}
    second = {"run": 2, "status": "failure"}

    save_pipeline_run(history_file, first)
    save_pipeline_run(history_file, second)

    history = load_pipeline_history(history_file)

    assert len(history) == 2
    assert history[0]["run"] == 1
    assert history[1]["status"] == "failure"
    assert history == [first, second]


@pytest.fixture
def fake_streamlit(monkeypatch):
    """Provide a patched Streamlit shim for dashboard tests."""

    fake = FakeStreamlit()
    monkeypatch.setattr(dashboard, "st", fake)
    return fake


def test_dashboard_main_without_history(tmp_path, monkeypatch, fake_streamlit):
    """Dashboard should render informative message when history is empty."""

    monkeypatch.chdir(tmp_path)
    fake_streamlit.set_button_response(False)

    dashboard.main()

    assert any(
        "No execution history available" in message for message in fake_streamlit.info_messages
    )


def test_dashboard_main_runs_pipeline_and_persists_history(tmp_path, monkeypatch, fake_streamlit):
    """Executing the dashboard should trigger the pipeline and persist history."""

    fake_streamlit.set_button_response(True)
    monkeypatch.chdir(tmp_path)

    class DummyQualityReport:
        def __init__(self) -> None:
            self.expectations_passed = True
            self.invalid_records = 0

        def to_dict(self) -> dict[str, object]:
            return {"status": "ok"}

    refined_df = pd.DataFrame({"data_quality_score": [0.9, 0.8]})
    run_result = SimpleNamespace(refined=refined_df, quality_report=DummyQualityReport())

    monkeypatch.setattr(
        dashboard,
        "get_default_profile",
        lambda profile: SimpleNamespace(name=profile),
    )
    monkeypatch.setattr(dashboard, "run_pipeline", lambda config: run_result)

    dashboard.main()

    history_path = Path("logs/pipeline_history.json")
    assert history_path.exists()
    history = json.loads(history_path.read_text())
    assert len(history) == 1
    assert history[0]["total_records"] == len(refined_df)
    assert fake_streamlit.success_messages
