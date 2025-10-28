"""Telemetry metric helpers for the Hotpass pipeline."""

from __future__ import annotations

from collections.abc import Callable, Mapping
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

        self.automation_requests = meter.create_counter(
            name="hotpass.automation.requests",
            description="Automation delivery attempts",
            unit="requests",
        )

        self.automation_failures = meter.create_counter(
            name="hotpass.automation.failures",
            description="Failed automation deliveries",
            unit="requests",
        )

        self.automation_latency = meter.create_histogram(
            name="hotpass.automation.duration",
            description="Delivery latency for automation requests",
            unit="seconds",
        )

        self.acquisition_duration = meter.create_histogram(
            name="hotpass.acquisition.duration",
            description="Duration of acquisition activity by scope (plan, agent, provider)",
            unit="seconds",
        )

        self.acquisition_records = meter.create_counter(
            name="hotpass.acquisition.records",
            description="Number of records produced during acquisition",
            unit="records",
        )

        self.acquisition_warnings = meter.create_counter(
            name="hotpass.acquisition.warnings",
            description="Number of compliance or runtime warnings raised during acquisition",
            unit="warnings",
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

    def record_automation_delivery(
        self,
        *,
        target: str,
        status: str,
        endpoint: str | None,
        attempts: int,
        latency: float | None,
        idempotency: str,
    ) -> None:
        attributes: dict[str, Any] = {
            "target": target,
            "status": status,
            "attempts": attempts,
            "idempotency": idempotency,
        }
        if endpoint:
            attributes["endpoint"] = endpoint

        self.automation_requests.add(1, attributes)
        if status != "delivered":
            self.automation_failures.add(1, attributes)
        if latency is not None:
            self.automation_latency.record(latency, attributes)

    def record_acquisition_duration(
        self,
        seconds: float,
        *,
        scope: str,
        agent: str | None = None,
        provider: str | None = None,
        extra_attributes: Mapping[str, Any] | None = None,
    ) -> None:
        attributes = self._acquisition_attributes(scope, agent, provider, extra_attributes)
        self.acquisition_duration.record(seconds, attributes)

    def record_acquisition_records(
        self,
        count: int,
        *,
        scope: str,
        agent: str | None = None,
        provider: str | None = None,
        extra_attributes: Mapping[str, Any] | None = None,
    ) -> None:
        attributes = self._acquisition_attributes(scope, agent, provider, extra_attributes)
        self.acquisition_records.add(count, attributes)

    def record_acquisition_warnings(
        self,
        count: int,
        *,
        scope: str,
        agent: str | None = None,
        provider: str | None = None,
        extra_attributes: Mapping[str, Any] | None = None,
    ) -> None:
        attributes = self._acquisition_attributes(scope, agent, provider, extra_attributes)
        self.acquisition_warnings.add(count, attributes)

    @staticmethod
    def _acquisition_attributes(
        scope: str,
        agent: str | None,
        provider: str | None,
        extra_attributes: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        attributes: dict[str, Any] = {"scope": scope}
        if agent:
            attributes["agent"] = agent
        if provider:
            attributes["provider"] = provider
        if extra_attributes:
            attributes.update(extra_attributes)
        return attributes
