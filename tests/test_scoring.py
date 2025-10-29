from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from hotpass.enrichment.validators import logistic_scale
from hotpass.transform.scoring import (
    LeadScorer,
    LeadScoringModel,
    build_daily_list,
    score_prospects,
    train_lead_scoring_model,
)


def test_lead_scorer_ranges():
    scorer = LeadScorer()
    high = scorer.score(
        completeness=1.0,
        email_confidence=0.9,
        phone_confidence=0.85,
        source_priority=1.0,
        intent_score=0.7,
    )
    low = scorer.score(
        completeness=0.2,
        email_confidence=0.1,
        phone_confidence=0.0,
        source_priority=0.0,
        intent_score=0.0,
    )

    assert 0.0 <= high.value <= 1.0
    assert 0.0 <= low.value <= 1.0
    assert high.value > low.value


def test_lead_scorer_accepts_custom_weights():
    scorer = LeadScorer(weights={"completeness": 1.0})
    score = scorer.score(
        completeness=0.5,
        email_confidence=0.0,
        phone_confidence=0.0,
        source_priority=0.0,
    )
    assert (
        score.value
        == scorer.score(
            completeness=0.5,
            email_confidence=0.0,
            phone_confidence=0.0,
            source_priority=0.0,
        ).value
    )


def _build_training_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "completeness": [0.9, 0.4, 0.75, 0.3, 0.85, 0.6, 0.7, 0.5],
            "email_confidence": [0.8, 0.1, 0.6, 0.2, 0.75, 0.5, 0.55, 0.3],
            "phone_confidence": [0.7, 0.0, 0.4, 0.2, 0.65, 0.3, 0.45, 0.25],
            "source_priority": [1.0, 0.2, 0.6, 0.1, 0.9, 0.4, 0.5, 0.3],
            "intent_signal_score": [0.9, 0.3, 0.5, 0.2, 0.8, 0.4, 0.6, 0.35],
            "won": [1, 0, 1, 0, 1, 0, 1, 0],
        }
    )


def test_train_lead_scoring_model_reports_metrics(tmp_path: Path) -> None:
    pytest.importorskip("sklearn", reason="scikit-learn extra required for training tests")
    dataset = _build_training_frame()
    metrics_path = tmp_path / "metrics.json"
    result = train_lead_scoring_model(
        dataset,
        target_column="won",
        metrics_path=metrics_path,
    )

    assert metrics_path.exists()
    feature_frame = dataset.drop(columns=["won"])
    scored = score_prospects(result.model, feature_frame)
    assert "lead_score" in scored.columns
    assert scored["lead_score"].between(0.0, 1.0).all()
    ranked = scored.sort_values("lead_score", ascending=False)
    assert ranked.iloc[0]["lead_score"] >= ranked.iloc[-1]["lead_score"]

    assert result.metrics["roc_auc"] >= 0.5
    assert result.metrics["precision"] > 0.0
    assert result.metrics["recall"] > 0.0
    assert result.metadata["target_column"] == "won"
    assert result.metadata["feature_names"] == tuple(feature_frame.columns)


def test_train_lead_scoring_model_enforces_thresholds() -> None:
    pytest.importorskip("sklearn", reason="scikit-learn extra required for training tests")
    # Create a dataset with all same target (poor model performance)
    dataset = _build_training_frame().copy()
    # Ensure we have both classes but poor separation
    dataset.loc[0:3, "won"] = 0
    dataset.loc[4:7, "won"] = 1
    # Shuffle features to ensure poor performance
    dataset.loc[:, "completeness"] = 0.5
    dataset.loc[:, "email_confidence"] = 0.5

    with pytest.raises(RuntimeError, match="Validation metrics below required thresholds"):
        train_lead_scoring_model(
            dataset,
            target_column="won",
            metric_thresholds={"roc_auc": 0.95},  # Unrealistically high threshold
        )


def test_score_prospects_calibrates_predictions() -> None:
    class DummyEstimator:
        def __init__(self, probabilities: list[float]) -> None:
            self._probabilities = probabilities

        def predict_proba(self, frame: Any) -> Any:
            positive = pd.Series(self._probabilities, index=frame.index)
            negative = 1 - positive
            return pd.concat([negative, positive], axis=1).to_numpy()

    dummy = LeadScoringModel(
        estimator=DummyEstimator([0.2, 0.6, 0.9]),
        feature_names=("signal",),
        trained_at=datetime(2025, 10, 28, tzinfo=UTC),
    )
    frame = pd.DataFrame({"signal": [0.2, 0.6, 0.9]})
    scored = score_prospects(dummy, frame)

    expected = frame["signal"].apply(logistic_scale)
    pd.testing.assert_series_equal(scored["lead_score"], expected, check_names=False)


def test_build_daily_list_exports(tmp_path):
    pytest.importorskip("sklearn", reason="scikit-learn extra required for training tests")
    refined = pd.DataFrame(
        {
            "organization_slug": [
                "aero-school",
                "heli-ops",
                "cargo-air",
                "flight-academy",
                "sky-training",
                "jet-services",
            ],
            "organization_name": [
                "Aero School",
                "Heli Ops",
                "Cargo Air",
                "Flight Academy",
                "Sky Training",
                "Jet Services",
            ],
            "completeness": [0.92, 0.41, 0.85, 0.65, 0.78, 0.55],
            "email_confidence": [0.88, 0.15, 0.75, 0.55, 0.68, 0.45],
            "phone_confidence": [0.75, 0.2, 0.65, 0.45, 0.58, 0.35],
            "source_priority": [1.0, 0.3, 0.9, 0.5, 0.7, 0.4],
            "intent_signal_score": [0.9, 0.1, 0.8, 0.4, 0.6, 0.3],
        }
    )
    training = refined.assign(won=[1, 0, 1, 0, 1, 0])
    model = train_lead_scoring_model(training, target_column="won").model
    digest = pd.DataFrame(
        {
            "target_identifier": [
                "Aero School",
                "Heli Ops",
                "Cargo Air",
                "Flight Academy",
                "Sky Training",
                "Jet Services",
            ],
            "target_slug": [
                "aero-school",
                "heli-ops",
                "cargo-air",
                "flight-academy",
                "sky-training",
                "jet-services",
            ],
            "intent_signal_score": [0.9, 0.1, 0.8, 0.4, 0.6, 0.3],
            "intent_signal_count": [3, 1, 2, 1, 2, 1],
            "intent_signal_types": [
                "news;hiring",
                "news",
                "expansion",
                "news",
                "hiring",
                "news",
            ],
            "intent_last_observed_at": [
                datetime(2025, 10, 27, 7, tzinfo=UTC).isoformat(),
                datetime(2025, 10, 27, 6, tzinfo=UTC).isoformat(),
                datetime(2025, 10, 27, 5, tzinfo=UTC).isoformat(),
                datetime(2025, 10, 27, 4, tzinfo=UTC).isoformat(),
                datetime(2025, 10, 27, 3, tzinfo=UTC).isoformat(),
                datetime(2025, 10, 27, 2, tzinfo=UTC).isoformat(),
            ],
            "intent_top_insights": [
                "Secures national contract",
                "Launches marketing campaign",
                "Opens new facility",
                "Hires new instructors",
                "Expands training fleet",
                "Announces partnership",
            ],
        }
    )

    output_path = tmp_path / "daily-list.csv"
    daily = build_daily_list(
        refined_df=refined,
        intent_digest=digest,
        model=model,
        top_n=2,
        output_path=output_path,
    )

    assert output_path.exists()
    assert len(daily) <= 2
    assert daily.iloc[0]["lead_score"] <= 1.0
