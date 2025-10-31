"""Configuration helpers for probabilistic linkage and review flows."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path


def _validate_threshold(value: float, label: str) -> float:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{label} must be within [0.0, 1.0]; received {value!r}")
    return value


@dataclass(slots=True)
class LinkageThresholds:
    """Decision thresholds for probabilistic linkage outputs."""

    high: float = 0.9
    review: float = 0.7
    reject: float = 0.0

    def __post_init__(self) -> None:
        _validate_threshold(self.high, "high")
        _validate_threshold(self.review, "review")
        _validate_threshold(self.reject, "reject")
        if not self.high >= self.review >= self.reject:
            raise ValueError(
                "Thresholds must satisfy high >= review >= reject;"
                f" received high={self.high}, review={self.review}, reject={self.reject}"
            )

    def classify(self, score: float) -> str:
        """Return a human readable label for the supplied probability."""

        _validate_threshold(score, "score")
        if score >= self.high:
            return "match"
        if score >= self.review:
            return "review"
        return "reject"

    def as_dict(self) -> dict[str, float]:
        return {"high": self.high, "review": self.review, "reject": self.reject}

    def as_tuple(self) -> tuple[float, float, float]:
        return (self.high, self.review, self.reject)

    def bounds(self) -> tuple[float, float]:
        """Return the inclusive lower bound for review and the match threshold."""

        return self.review, self.high


@dataclass(slots=True)
class LabelStudioConfig:
    """Connection details for the Label Studio reviewer workflow."""

    api_url: str
    api_token: str
    project_id: int
    timeout: float = 10.0
    verify_ssl: bool = True

    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Token {self.api_token}",
            "Content-Type": "application/json",
        }


@dataclass(slots=True)
class LinkagePersistence:
    """File layout for persisted linkage artefacts."""

    root_dir: Path = Path("dist/linkage")
    matches_filename: str = "linkage_matches.parquet"
    review_filename: str = "linkage_review_queue.parquet"
    decisions_filename: str = "linkage_reviewer_decisions.jsonl"
    metadata_filename: str = "linkage_metadata.json"

    def ensure(self) -> None:
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def matches_path(self) -> Path:
        return self.root_dir / self.matches_filename

    def review_path(self) -> Path:
        return self.root_dir / self.review_filename

    def decisions_path(self) -> Path:
        return self.root_dir / self.decisions_filename

    def metadata_path(self) -> Path:
        return self.root_dir / self.metadata_filename


@dataclass(slots=True)
class LinkageConfig:
    """Container for linkage execution parameters."""

    use_splink: bool = True
    thresholds: LinkageThresholds = field(default_factory=LinkageThresholds)
    persistence: LinkagePersistence = field(default_factory=LinkagePersistence)
    label_studio: LabelStudioConfig | None = None
    review_payload_fields: Iterable[str] | None = None

    def with_output_root(self, root: Path) -> LinkageConfig:
        """Return a copy with persistence rooted under *root*."""

        updated = LinkageConfig(
            use_splink=self.use_splink,
            thresholds=self.thresholds,
            persistence=LinkagePersistence(root_dir=root),
            label_studio=self.label_studio,
            review_payload_fields=self.review_payload_fields,
        )
        return updated
