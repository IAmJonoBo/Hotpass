"""Lead scoring helpers used to prioritise enriched contacts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from hotpass.enrichment.validators import logistic_scale

DEFAULT_WEIGHTS: Mapping[str, float] = {
    "completeness": 0.3,
    "email_confidence": 0.25,
    "phone_confidence": 0.15,
    "source_priority": 0.2,
    "intent": 0.1,
}


@dataclass(slots=True)
class LeadScore:
    """Lead score enriched with contributing components."""

    value: float
    components: Mapping[str, float]


class LeadScorer:
    """Combine quality signals into a normalised lead score."""

    def __init__(self, weights: Mapping[str, float] | None = None) -> None:
        self.weights = dict(weights or DEFAULT_WEIGHTS)
        if not self.weights:
            raise ValueError("weights must contain at least one entry")

    def _normalise(self, components: Mapping[str, float]) -> float:
        weighted = 0.0
        total_weight = 0.0
        for key, raw_value in components.items():
            weight = self.weights.get(key, 0.0)
            if weight <= 0:
                continue
            total_weight += weight
            weighted += weight * max(0.0, min(1.0, raw_value))
        if total_weight == 0:
            return 0.0
        return weighted / total_weight

    def score(
        self,
        *,
        completeness: float,
        email_confidence: float,
        phone_confidence: float,
        source_priority: float,
        intent_score: float = 0.0,
    ) -> LeadScore:
        components = {
            "completeness": completeness,
            "email_confidence": email_confidence,
            "phone_confidence": phone_confidence,
            "source_priority": source_priority,
            "intent": intent_score,
        }
        normalised = self._normalise(components)
        scaled = logistic_scale(normalised)
        return LeadScore(value=scaled, components=components)
