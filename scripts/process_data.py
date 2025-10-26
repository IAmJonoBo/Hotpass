"""Deprecated shim script that proxies to the packaged Hotpass CLI."""

from __future__ import annotations

# Deprecated shim that proxies to the packaged Hotpass CLI.
from hotpass.cli import main

if __name__ == "__main__":  # pragma: no cover - legacy script entry point
    raise SystemExit(main())
