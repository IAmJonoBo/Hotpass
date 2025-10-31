from __future__ import annotations


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
