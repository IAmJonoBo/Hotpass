"""Compatibility shim for the legacy `hotpass-enhanced` entry point."""

from __future__ import annotations

import sys
from collections.abc import Callable, Sequence

from hotpass.cli import build_parser as _build_parser
from hotpass.cli import main as _cli_main

_DEPRECATION_MESSAGE = (
    "hotpass-enhanced is deprecated. Use `hotpass` with subcommands instead (for example, "
    "`hotpass run` or `hotpass orchestrate`)."
)


def build_enhanced_parser() -> object:
    """Return the unified CLI parser for backwards compatibility."""

    return _build_parser()


def main(argv: Sequence[str] | None = None) -> int:
    """Delegate to the unified CLI after emitting a deprecation warning."""

    print(_DEPRECATION_MESSAGE, file=sys.stderr)
    normalised = list(argv) if argv is not None else None
    return _UNIFIED_ENTRYPOINT(normalised)


_UNIFIED_ENTRYPOINT: Callable[[Sequence[str] | None], int] = _cli_main

__all__ = ["build_enhanced_parser", "main"]
