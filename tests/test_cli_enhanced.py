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

    from tests.helpers.assertions import expect

    expect(exit_code == 0, "Enhanced CLI should return 0 on success")
    expect(len(invoked) == 1, "Should invoke unified CLI once")
    expect(invoked[0][0] == ("run",), "Should pass 'run' argument to unified CLI")


def test_cli_enhanced_warns_about_deprecation(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli_enhanced, "_UNIFIED_ENTRYPOINT", lambda argv=None: 0)

    exit_code = cli_enhanced.main([])

    captured = capsys.readouterr()

    from tests.helpers.assertions import expect

    expect(exit_code == 0, "Enhanced CLI should return 0")
    expect("deprecated" in captured.err.lower(), "Should warn about deprecation")
