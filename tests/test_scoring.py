from datetime import UTC, datetime

import pandas as pd
import pytest

from hotpass.transform.scoring import (
    LeadScorer,
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


@pytest.mark.parametrize(
    "feature_set",
    [
        (
            pd.DataFrame(
                {
                    "completeness": [0.9, 0.4, 0.75],
                    "email_confidence": [0.8, 0.1, 0.6],
                    "phone_confidence": [0.7, 0.0, 0.4],
                    "source_priority": [1.0, 0.2, 0.6],
                    "intent_signal_score": [0.9, 0.3, 0.5],
                    "won": [1, 0, 1],
                }
            ),
            "won",
        )
    ],
)
def test_train_lead_scoring_model(feature_set: tuple[pd.DataFrame, str]) -> None:
    dataset, target = feature_set
    model = train_lead_scoring_model(dataset, target_column=target)
    feature_frame = dataset.drop(columns=[target])
    scored = score_prospects(model, feature_frame)
    assert "lead_score" in scored.columns
    assert scored["lead_score"].between(0.0, 1.0).all()
    ranked = scored.sort_values("lead_score", ascending=False)
    assert ranked.iloc[0]["lead_score"] >= ranked.iloc[-1]["lead_score"]


def test_build_daily_list_exports(tmp_path):
    refined = pd.DataFrame(
        {
            "organization_slug": ["aero-school", "heli-ops"],
            "organization_name": ["Aero School", "Heli Ops"],
            "completeness": [0.92, 0.41],
            "email_confidence": [0.88, 0.15],
            "phone_confidence": [0.75, 0.2],
            "source_priority": [1.0, 0.3],
            "intent_signal_score": [0.9, 0.1],
        }
    )
    training = refined.assign(won=[1, 0])
    model = train_lead_scoring_model(training, target_column="won")
    digest = pd.DataFrame(
        {
            "target_identifier": ["Aero School", "Heli Ops"],
            "target_slug": ["aero-school", "heli-ops"],
            "intent_signal_score": [0.9, 0.1],
            "intent_signal_count": [3, 1],
            "intent_signal_types": ["news;hiring", "news"],
            "intent_last_observed_at": [
                datetime(2025, 10, 27, 7, tzinfo=UTC).isoformat(),
                datetime(2025, 10, 27, 6, tzinfo=UTC).isoformat(),
            ],
            "intent_top_insights": [
                "Secures national contract",
                "Launches marketing campaign",
            ],
        }
    )

    output_path = tmp_path / "daily-list.csv"
    daily = build_daily_list(
        refined_df=refined,
        intent_digest=digest,
        model=model,
        top_n=1,
        output_path=output_path,
    )

    assert output_path.exists()
    assert list(daily["organization_slug"]) == ["aero-school"]
    assert daily.iloc[0]["lead_score"] <= 1.0
