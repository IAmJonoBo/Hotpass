from pathlib import Path

import pytest

pytest.importorskip("frictionless")

from hotpass import benchmarks  # noqa: E402
from hotpass.data_sources import ExcelReadOptions  # noqa: E402

from tests.helpers.assertions import expect  # noqa: E402


def test_run_benchmark_returns_metrics(sample_data_dir: Path, tmp_path: Path) -> None:
    output_path = tmp_path / "refined.xlsx"
    result = benchmarks.run_benchmark(
        input_dir=sample_data_dir,
        output_path=output_path,
        runs=1,
        excel_options=ExcelReadOptions(chunk_size=1),
    )

    expect(result.runs == 1, "Benchmark should execute requested number of runs")
    expect(
        result.metrics["total_seconds"] >= 0.0,
        "Total seconds metric should be non-negative",
    )
    expect(
        result.samples[0]["rows_per_second"] > 0.0,
        "Rows per second should be positive",
    )
