"""Telemetry metric helpers for the Hotpass pipeline."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class PipelineMetrics:
    """Metrics collector for pipeline operations."""

    def __init__(self, meter: Any, observation_factory: Callable[[float], Any]) -> None:
        self._meter = meter
        self.meter = meter
        self._observation_factory = observation_factory

        self.records_processed = meter.create_counter(
            name="hotpass.records.processed",
            description="Total number of records processed",
            unit="records",
        )

        self.validation_failures = meter.create_counter(
            name="hotpass.validation.failures",
            description="Number of validation failures",
            unit="failures",
        )

        self.load_duration = meter.create_histogram(
            name="hotpass.load.duration",
            description="Duration of data loading operations",
            unit="seconds",
        )

        self.aggregation_duration = meter.create_histogram(
            name="hotpass.aggregation.duration",
            description="Duration of aggregation operations",
            unit="seconds",
        )

        self.validation_duration = meter.create_histogram(
            name="hotpass.validation.duration",
            description="Duration of validation operations",
            unit="seconds",
        )

        self.write_duration = meter.create_histogram(
            name="hotpass.write.duration",
            description="Duration of write operations",
            unit="seconds",
        )

        self.data_quality_score = meter.create_observable_gauge(
            name="hotpass.data.quality_score",
            description="Overall data quality score",
            callbacks=[self._get_quality_score],
        )

        self._latest_quality_score = 0.0

    def _get_quality_score(self, *_: Any) -> list[Any]:
        return [self._observation_factory(self._latest_quality_score)]

    def record_records_processed(self, count: int, source: str = "unknown") -> None:
        self.records_processed.add(count, {"source": source})

    def record_validation_failure(self, rule_name: str) -> None:
        self.validation_failures.add(1, {"rule": rule_name})

    def record_load_duration(self, seconds: float, source: str = "unknown") -> None:
        self.load_duration.record(seconds, {"source": source})

    def record_aggregation_duration(self, seconds: float) -> None:
        self.aggregation_duration.record(seconds)

    def record_validation_duration(self, seconds: float) -> None:
        self.validation_duration.record(seconds)

    def record_write_duration(self, seconds: float) -> None:
        self.write_duration.record(seconds)

    def update_quality_score(self, score: float) -> None:
        self._latest_quality_score = score
