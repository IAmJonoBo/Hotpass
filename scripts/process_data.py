"""CLI entrypoint for running the Hotpass SSOT refinement pipeline."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--archive",
        action="store_true",
        help="Package the refined workbook into a timestamped zip archive",
    )
    parser.add_argument(
        "--dist-dir",
        type=Path,
        default=PROJECT_ROOT / "dist",
        help="Directory for packaged artifacts (default: %(default)s)",
    )
    return parser.parse_args()


def main() -> None:
    if str(SRC_PATH) not in sys.path:
        sys.path.insert(0, str(SRC_PATH))

    args = parse_args()

    from hotpass.artifacts import create_refined_archive  # noqa: E402
    from hotpass.pipeline import PipelineConfig, run_pipeline  # noqa: E402

    project_root = PROJECT_ROOT
    data_dir = project_root / "data"
    output_path = data_dir / "refined_data.xlsx"

    config = PipelineConfig(input_dir=data_dir, output_path=output_path)
    result = run_pipeline(config)

    report = result.quality_report
    print("Hotpass SSOT pipeline completed")
    print(f"Records processed: {report.total_records}")
    print(f"Invalid records dropped: {report.invalid_records}")
    print(f"Expectation suite passed: {report.expectations_passed}")
    if report.expectation_failures:
        print("Expectation failures:")
        for failure in report.expectation_failures:
            print(f"  - {failure}")
    print("Data quality distribution:")
    for key, value in report.data_quality_distribution.items():
        print(f"  {key}: {value:.2f}")

    if args.archive:
        archive_path = create_refined_archive(output_path, args.dist_dir)
        print(f"Packaged archive created at: {archive_path}")


if __name__ == "__main__":  # pragma: no cover - script entry point
    main()
