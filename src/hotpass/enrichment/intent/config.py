"""Configuration dataclasses powering intent signal collection."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class IntentCollectorDefinition:
    """Describe a collector used to retrieve intent signals."""

    name: str
    options: Mapping[str, Any] = field(default_factory=dict)
    enabled: bool = True
    weight: float = 1.0


@dataclass(frozen=True, slots=True)
class IntentTargetDefinition:
    """Entity for which intent signals should be gathered."""

    identifier: str
    slug: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class IntentPlan:
    """Overall plan defining collectors and targets for intent analysis."""

    enabled: bool = False
    collectors: Sequence[IntentCollectorDefinition] = field(default_factory=tuple)
    targets: Sequence[IntentTargetDefinition] = field(default_factory=tuple)
    deduplicate: bool = True

    def active_collectors(self) -> tuple[IntentCollectorDefinition, ...]:
        return tuple(collector for collector in self.collectors if collector.enabled)

    def active_targets(self) -> tuple[IntentTargetDefinition, ...]:
        return tuple(self.targets)


__all__ = [
    "IntentCollectorDefinition",
    "IntentPlan",
    "IntentTargetDefinition",
]
