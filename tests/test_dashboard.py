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
from hotpass.dashboard import (
    PASSWORD_INPUT_LABEL,
    RUN_BUTTON_LABEL,
    UNLOCK_BUTTON_LABEL,
    load_pipeline_history,
    save_pipeline_run,
)


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
    def __init__(self, parent: FakeStreamlit) -> None:
        self._parent = parent

    def header(self, *_: object, **__: object) -> None:
        return None

    def text_input(self, label: str, value: str = "", **_: object) -> str:
        return self._parent.text_input(f"sidebar::{label}", value)

    def selectbox(self, label: str, options: list[str], **_: object) -> str:
        return self._parent.selectbox(f"sidebar::{label}", options)

    def number_input(self, label: str, value: int = 0, **_: object) -> int:
        return self._parent.number_input(f"sidebar::{label}", value)

    def button(self, label: str, **_: object) -> bool:
        return self._parent.button(f"sidebar::{label}")


class FakeStreamlit:
    """Minimal Streamlit shim capturing notable interactions."""

    def __init__(self) -> None:
        self.sidebar = FakeSidebar(self)
        self.session_state: dict[str, object] = {}
        self._button_responses: dict[str, bool] = {}
        self._text_inputs: dict[str, str] = {}
        self._selectbox_values: dict[str, str] = {}
        self._number_inputs: dict[str, int] = {}
        self.info_messages: list[str] = []
        self.success_messages: list[str] = []
        self.warning_messages: list[str] = []
        self.error_messages: list[str] = []

    def set_button_response(self, label: str, pressed: bool) -> None:
        self._button_responses[label] = pressed

    def set_sidebar_text_input_value(self, label: str, value: str) -> None:
        self._text_inputs[f"sidebar::{label}"] = value

    def set_text_input_value(self, label: str, value: str) -> None:
        self._text_inputs[label] = value

    def text_input(self, label: str, value: str = "", **_: object) -> str:
        return self._text_inputs.get(label, value)

    def selectbox(self, label: str, options: list[str], **_: object) -> str:
        return self._selectbox_values.get(label, options[0])

    def number_input(self, label: str, value: int = 0, **_: object) -> int:
        return self._number_inputs.get(label, value)

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

    def button(self, label: str, **__: object) -> bool:
        return self._button_responses.get(label, False)

    def spinner(self, *_: object, **__: object) -> _FakeContext:
        return _FakeContext()

    def header(self, *_: object, **__: object) -> None:
        return None

    def info(self, message: str, **_: object) -> None:
        self.info_messages.append(message)

    def warning(self, *args: object, **__: object) -> None:
        if args:
            self.warning_messages.append(str(args[0]))
        return None

    def success(self, message: str, **_: object) -> None:
        self.success_messages.append(message)

    def error(self, *args: object, **__: object) -> None:
        if args:
            self.error_messages.append(str(args[0]))
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
    fake_streamlit.set_button_response(RUN_BUTTON_LABEL, False)

    dashboard.main()

    assert any(
        "No execution history available" in message
        for message in fake_streamlit.info_messages
    )


def test_dashboard_main_runs_pipeline_and_persists_history(
    tmp_path, monkeypatch, fake_streamlit
):
    """Executing the dashboard should trigger the pipeline and persist history."""

    fake_streamlit.set_button_response(RUN_BUTTON_LABEL, True)
    monkeypatch.chdir(tmp_path)

    class DummyQualityReport:
        def __init__(self) -> None:
            self.expectations_passed = True
            self.invalid_records = 0

        def to_dict(self) -> dict[str, object]:
            return {"status": "ok"}

    refined_df = pd.DataFrame({"data_quality_score": [0.9, 0.8]})
    run_result = SimpleNamespace(
        refined=refined_df, quality_report=DummyQualityReport()
    )

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


def test_dashboard_authentication_required(monkeypatch, tmp_path, fake_streamlit):
    """Pipeline execution is blocked until the dashboard password is provided."""

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(dashboard.AUTH_PASSWORD_ENV, "secret")
    fake_streamlit.set_sidebar_text_input_value(PASSWORD_INPUT_LABEL, "")
    fake_streamlit.set_button_response(f"sidebar::{UNLOCK_BUTTON_LABEL}", False)
    fake_streamlit.set_button_response(RUN_BUTTON_LABEL, True)

    pipeline_called = False

    def _run_pipeline(config):  # type: ignore[no-redef]
        nonlocal pipeline_called
        pipeline_called = True
        raise AssertionError("Pipeline should not run without authentication")

    monkeypatch.setattr(dashboard, "run_pipeline", _run_pipeline)

    dashboard.main()

    assert not pipeline_called
    assert any(
        "Authentication required" in message
        for message in fake_streamlit.warning_messages
    )


def test_dashboard_authentication_unlocks_session(
    monkeypatch, tmp_path, fake_streamlit
):
    """Providing the correct password unlocks the dashboard for the session."""

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(dashboard.AUTH_PASSWORD_ENV, "secret")
    fake_streamlit.set_sidebar_text_input_value(PASSWORD_INPUT_LABEL, "secret")
    fake_streamlit.set_button_response(f"sidebar::{UNLOCK_BUTTON_LABEL}", True)
    fake_streamlit.set_button_response(RUN_BUTTON_LABEL, True)

    class DummyQualityReport:
        def __init__(self) -> None:
            self.expectations_passed = True
            self.invalid_records = 0

        def to_dict(self) -> dict[str, object]:
            return {"status": "ok"}

    refined_df = pd.DataFrame({"data_quality_score": [1.0]})
    run_result = SimpleNamespace(
        refined=refined_df, quality_report=DummyQualityReport()
    )

    monkeypatch.setattr(
        dashboard,
        "get_default_profile",
        lambda profile: SimpleNamespace(name=profile),
    )
    monkeypatch.setattr(dashboard, "run_pipeline", lambda config: run_result)

    dashboard.main()

    assert fake_streamlit.success_messages
    assert fake_streamlit.session_state[dashboard.AUTH_STATE_KEY] is True


def test_dashboard_blocks_paths_outside_allowlist(
    monkeypatch, tmp_path, fake_streamlit
):
    """Input and output paths must stay within the configured allowlist."""

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(dashboard.ALLOWED_ROOTS_ENV, str(tmp_path / "allowed"))
    fake_streamlit.set_sidebar_text_input_value(
        "Input Directory", str(tmp_path / "forbidden")
    )
    fake_streamlit.set_sidebar_text_input_value(
        "Output Path", str(tmp_path.parent / "refined.xlsx")
    )
    fake_streamlit.set_button_response(RUN_BUTTON_LABEL, True)

    monkeypatch.setattr(
        dashboard,
        "get_default_profile",
        lambda profile: SimpleNamespace(name=profile),
    )

    def _fail_if_called(config):  # type: ignore[no-redef]
        raise AssertionError("Pipeline must not run when paths are outside allowlist")

    monkeypatch.setattr(dashboard, "run_pipeline", _fail_if_called)

    dashboard.main()

    assert fake_streamlit.error_messages
