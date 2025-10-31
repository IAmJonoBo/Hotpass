"""State persistence helpers for CLI commands."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

STATE_ENV_VAR = "HOTPASS_STATE_DIR"
DEFAULT_STATE_DIR = Path(".hotpass")


def _resolve_state_dir() -> Path:
    """Return the directory that stores CLI state files."""

    override = os.environ.get(STATE_ENV_VAR)
    if override:
        return Path(override).expanduser().resolve()
    return DEFAULT_STATE_DIR


def ensure_state_dir() -> Path:
    """Ensure the CLI state directory exists and return it."""

    state_dir = _resolve_state_dir()
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir


def state_path(name: str) -> Path:
    """Return the path for a named state file (creating the directory if required)."""

    return ensure_state_dir() / name


def load_state(name: str, *, default: Any = None) -> Any:
    """Load a JSON-serialised state file."""

    path = state_path(name)
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def write_state(name: str, payload: Any) -> None:
    """Write a JSON payload to the state directory atomically."""

    path = state_path(name)
    temp_path = path.with_suffix(".tmp")
    temp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temp_path.replace(path)


def remove_state(name: str) -> None:
    """Remove a state file if it exists."""

    path = state_path(name)
    try:
        path.unlink()
    except FileNotFoundError:
        return
