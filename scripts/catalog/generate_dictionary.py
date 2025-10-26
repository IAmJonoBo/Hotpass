"""CLI helper to generate the Hotpass data dictionary."""

from __future__ import annotations

import argparse
from pathlib import Path

from hotpass.domain.party import render_dictionary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("dist/catalog/hotpass_data_dictionary.md"),
        help="Destination path for the rendered Markdown data dictionary",
    )
    return parser


def generate_dictionary(output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = render_dictionary()
    output_path.write_text(content, encoding="utf-8")
    return output_path


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    destination = generate_dictionary(args.output)
    print(f"Data dictionary written to {destination}")
    return 0


if __name__ == "__main__":  # pragma: no cover - script entry point
    raise SystemExit(main())
