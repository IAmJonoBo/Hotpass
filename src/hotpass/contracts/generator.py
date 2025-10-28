"""Utilities for regenerating dataset JSON schemas and documentation."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from .datasets import DATASET_CONTRACTS
from .types import DatasetContract, render_reference_markdown

__all__ = [
    "regenerate_json_schemas",
    "regenerate_reference_doc",
    "main",
]

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_SCHEMA_DIR = _REPO_ROOT / "schemas"
_DEFAULT_DOC_PATH = _REPO_ROOT / "docs" / "reference" / "schemas.md"


def regenerate_json_schemas(
    *,
    contracts: Sequence[DatasetContract] = DATASET_CONTRACTS,
    schema_dir: Path | None = None,
) -> list[Path]:
    """Write the JSON schemas for all dataset contracts to disk."""

    target_dir = schema_dir or _DEFAULT_SCHEMA_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    generated: list[Path] = []
    for contract in contracts:
        generated.append(contract.dump_json_schema(target_dir))
    return generated


def regenerate_reference_doc(
    *,
    contracts: Sequence[DatasetContract] = DATASET_CONTRACTS,
    doc_path: Path | None = None,
    last_updated: date | None = None,
) -> Path:
    """Render the schema reference documentation page."""

    destination = doc_path or _DEFAULT_DOC_PATH
    destination.parent.mkdir(parents=True, exist_ok=True)
    render_date = last_updated or date.today()
    markdown = render_reference_markdown(contracts, last_updated=render_date)
    destination.write_text(markdown, encoding="utf-8")
    return destination


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Regenerate Hotpass dataset contract artefacts",
    )
    parser.add_argument(
        "--schemas",
        type=Path,
        default=_DEFAULT_SCHEMA_DIR,
        help="Directory where JSON schemas will be written (default: repository schemas/)",
    )
    parser.add_argument(
        "--docs",
        type=Path,
        default=_DEFAULT_DOC_PATH,
        help="Path to the generated documentation file (default: docs/reference/schemas.md)",
    )
    parser.add_argument(
        "--last-updated",
        type=str,
        default=None,
        help="ISO formatted date to use for docs front matter (default: today)",
    )
    parser.add_argument(
        "--skip-schemas",
        action="store_true",
        help="Skip regenerating the JSON schema files",
    )
    parser.add_argument(
        "--skip-docs",
        action="store_true",
        help="Skip regenerating the reference documentation",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entry point for regenerating contract artefacts."""

    args = _parse_args(argv)

    render_date = None
    if args.last_updated:
        try:
            render_date = date.fromisoformat(args.last_updated)
        except ValueError as exc:  # pragma: no cover - defensive guard for CLI usage
            msg = "--last-updated must be an ISO formatted date (YYYY-MM-DD)"
            raise SystemExit(msg) from exc

    if not args.skip_schemas:
        regenerate_json_schemas(schema_dir=args.schemas)

    if not args.skip_docs:
        regenerate_reference_doc(doc_path=args.docs, last_updated=render_date)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
