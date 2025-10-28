"""Entry point for the unified Hotpass CLI."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from .builder import CLIBuilder
from .commands import backfill, dashboard, deploy, orchestrate, resolve, run, version
from .configuration import (
    DEFAULT_PROFILE_DIRS,
    CLIProfile,
    ProfileIntentError,
    ProfileNotFoundError,
    ProfileValidationError,
    load_profile,
)

EPILOG = (
    "Profiles may be defined as TOML or YAML files. Use --profile-search-path to locate "
    "custom profiles."
)


def build_parser() -> argparse.ArgumentParser:
    builder = CLIBuilder(
        description="Hotpass CLI",
        epilog=EPILOG,
    )
    builder.register(run.register())
    builder.register(backfill.register())
    builder.register(orchestrate.register())
    builder.register(resolve.register())
    builder.register(dashboard.register())
    builder.register(deploy.register())
    builder.register(version.register())
    return builder.build()


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 1

    try:
        profile = _load_profile(args)
    except (ProfileNotFoundError, ProfileValidationError, ProfileIntentError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    return handler(args, profile)


def _load_profile(args: argparse.Namespace) -> CLIProfile | None:
    identifier = getattr(args, "profile", None)
    if not identifier:
        return None

    search_paths: list[Path] = []
    if args.profile_search_paths:
        search_paths.extend(Path(path) for path in args.profile_search_paths)
    search_paths.extend(DEFAULT_PROFILE_DIRS)

    return load_profile(identifier, search_paths=search_paths)


__all__ = ["build_parser", "main"]
