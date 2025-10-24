from pathlib import Path

from hotpass import benchmarks
from hotpass.data_sources import ExcelReadOptions


def test_run_benchmark_returns_metrics(sample_data_dir: Path, tmp_path: Path) -> None:
    output_path = tmp_path / "refined.xlsx"
    result = benchmarks.run_benchmark(
        input_dir=sample_data_dir,
        output_path=output_path,
        runs=1,
        excel_options=ExcelReadOptions(chunk_size=1),
    )

    assert result.runs == 1
    assert result.metrics["total_seconds"] >= 0.0
    assert result.samples[0]["rows_per_second"] > 0.0
