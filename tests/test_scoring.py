from hotpass.transform.scoring import LeadScorer


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
