"""Intent signal collectors powering enrichment automation."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, ClassVar

from ...normalization import slugify


@dataclass(slots=True)
class IntentCollectorContext:
    """Contextual information passed to collectors."""

    country_code: str
    credentials: Mapping[str, str]
    issued_at: datetime


@dataclass(slots=True)
class IntentSignal:
    """Structured signal emitted by collectors."""

    target_identifier: str
    target_slug: str | None
    signal_type: str
    score: float
    observed_at: datetime
    metadata: Mapping[str, Any]
    collector: str


class IntentCollectorError(RuntimeError):
    """Raised when collector configuration is invalid."""


class BaseIntentCollector:
    """Base class for all intent collectors."""

    name: ClassVar[str]

    def __init__(self, options: Mapping[str, Any] | None = None) -> None:
        self.options = dict(options or {})

    def _normalise_key(self, target_identifier: str, target_slug: str | None) -> tuple[str, ...]:
        keys = []
        if target_slug:
            keys.append(target_slug.lower())
        identifier_slug = slugify(target_identifier)
        if identifier_slug:
            keys.append(identifier_slug)
        keys.append(target_identifier.lower())
        return tuple(dict.fromkeys(keys))

    def collect(
        self,
        target_identifier: str,
        target_slug: str | None,
        context: IntentCollectorContext,
    ) -> Iterable[IntentSignal]:  # pragma: no cover - abstract
        raise NotImplementedError


class NewsMentionCollector(BaseIntentCollector):
    """Collector parsing news-like events from static configuration."""

    name = "news"

    def collect(
        self,
        target_identifier: str,
        target_slug: str | None,
        context: IntentCollectorContext,
    ) -> Iterable[IntentSignal]:
        dataset = self.options.get("events", {})
        signals: list[IntentSignal] = []
        for key in self._normalise_key(target_identifier, target_slug):
            events = dataset.get(key)
            if not events:
                continue
            for event in events:
                headline = str(event.get("headline") or "").strip()
                intent = float(event.get("intent", 0.0) or 0.0)
                sentiment = float(event.get("sentiment", 0.0) or 0.0)
                score = max(0.0, min(1.0, intent + 0.25 * max(sentiment, 0.0)))
                observed_raw = event.get("timestamp")
                observed_at = _parse_timestamp(observed_raw, context.issued_at)
                metadata = {
                    "headline": headline or None,
                    "url": event.get("url"),
                    "sentiment": sentiment if sentiment else None,
                }
                signals.append(
                    IntentSignal(
                        target_identifier=target_identifier,
                        target_slug=target_slug,
                        signal_type="news",
                        score=score,
                        observed_at=observed_at,
                        metadata={k: v for k, v in metadata.items() if v},
                        collector=self.name,
                    )
                )
        return signals


class HiringPulseCollector(BaseIntentCollector):
    """Collector summarising hiring signals for key roles."""

    name = "hiring"

    def collect(
        self,
        target_identifier: str,
        target_slug: str | None,
        context: IntentCollectorContext,
    ) -> Iterable[IntentSignal]:
        dataset = self.options.get("events", {})
        signals: list[IntentSignal] = []
        for key in self._normalise_key(target_identifier, target_slug):
            events = dataset.get(key)
            if not events:
                continue
            for event in events:
                role = str(event.get("role") or "").strip()
                seniority = float(event.get("seniority", 0.6) or 0.6)
                intent = float(event.get("intent", 0.0) or 0.0)
                score = max(0.0, min(1.0, intent + 0.2 * seniority))
                observed_at = _parse_timestamp(event.get("timestamp"), context.issued_at)
                metadata = {
                    "role": role or None,
                    "location": event.get("location"),
                }
                signals.append(
                    IntentSignal(
                        target_identifier=target_identifier,
                        target_slug=target_slug,
                        signal_type="hiring",
                        score=score,
                        observed_at=observed_at,
                        metadata={k: v for k, v in metadata.items() if v},
                        collector=self.name,
                    )
                )
        return signals


class TrafficSpikeCollector(BaseIntentCollector):
    """Collector summarising digital traffic spikes."""

    name = "traffic"

    def collect(
        self,
        target_identifier: str,
        target_slug: str | None,
        context: IntentCollectorContext,
    ) -> Iterable[IntentSignal]:
        dataset = self.options.get("events", {})
        signals: list[IntentSignal] = []
        for key in self._normalise_key(target_identifier, target_slug):
            events = dataset.get(key)
            if not events:
                continue
            for event in events:
                magnitude = float(event.get("magnitude", 0.0) or 0.0)
                intent = float(event.get("intent", 0.0) or 0.0)
                score = max(0.0, min(1.0, intent + 0.1 * magnitude))
                observed_at = _parse_timestamp(event.get("timestamp"), context.issued_at)
                metadata = {
                    "source": event.get("source"),
                    "magnitude": magnitude if magnitude else None,
                }
                signals.append(
                    IntentSignal(
                        target_identifier=target_identifier,
                        target_slug=target_slug,
                        signal_type="traffic",
                        score=score,
                        observed_at=observed_at,
                        metadata={k: v for k, v in metadata.items() if v},
                        collector=self.name,
                    )
                )
        return signals


def _parse_timestamp(candidate: Any, fallback: datetime) -> datetime:
    if isinstance(candidate, datetime):
        return candidate.astimezone(UTC)
    if isinstance(candidate, str):
        try:
            parsed = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
        except ValueError:
            return fallback
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    return fallback


class IntentCollectorRegistry:
    """Registry managing collector implementations."""

    def __init__(self) -> None:
        self._collectors: dict[str, type[BaseIntentCollector]] = {}

    def register(self, name: str, collector: type[BaseIntentCollector]) -> None:
        self._collectors[name.lower()] = collector

    def create(self, name: str, options: Mapping[str, Any] | None = None) -> BaseIntentCollector:
        try:
            collector_cls = self._collectors[name.lower()]
        except KeyError as exc:  # pragma: no cover - defensive
            raise IntentCollectorError(f"Unknown collector: {name}") from exc
        return collector_cls(options)


COLLECTOR_REGISTRY = IntentCollectorRegistry()
COLLECTOR_REGISTRY.register(NewsMentionCollector.name, NewsMentionCollector)
COLLECTOR_REGISTRY.register(HiringPulseCollector.name, HiringPulseCollector)
COLLECTOR_REGISTRY.register(TrafficSpikeCollector.name, TrafficSpikeCollector)


__all__ = [
    "BaseIntentCollector",
    "COLLECTOR_REGISTRY",
    "HiringPulseCollector",
    "IntentCollectorContext",
    "IntentCollectorError",
    "IntentSignal",
    "NewsMentionCollector",
    "TrafficSpikeCollector",
]
