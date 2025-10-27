"""Compatibility tests for the legacy `hotpass-enhanced` entrypoint."""

from __future__ import annotations

import pytest

pytest.importorskip("frictionless")

from hotpass import cli_enhanced


def test_cli_enhanced_delegates_to_unified_cli(monkeypatch: pytest.MonkeyPatch) -> None:
    invoked: list[tuple[tuple[str, ...], dict[str, object]]] = []

    def fake_main(argv: tuple[str, ...] | None = None) -> int:
        invoked.append((tuple(argv or ()), {}))
        return 0

    monkeypatch.setattr(cli_enhanced, "_UNIFIED_ENTRYPOINT", fake_main)
    exit_code = cli_enhanced.main(["run"])

    assert exit_code == 0
    assert invoked and invoked[0][0] == ("run",)


def test_cli_enhanced_warns_about_deprecation(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli_enhanced, "_UNIFIED_ENTRYPOINT", lambda argv=None: 0)

    exit_code = cli_enhanced.main([])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "deprecated" in captured.err.lower()
