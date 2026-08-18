from app.services.recommendation.recommendation_score_v8 import (
    build_recommendation_score_v8,
    normalize_priority,
)

from app.services.recommendation.reason_engine import (
    classify_recommendation_type,
)


def test_exploration_mode_remains_distinct_priority() -> None:
    assert normalize_priority("exploration") == "exploration"

    result = build_recommendation_score_v8(
        {},
        {
            "quality": 70,
            "price": 60,
            "trust": 50,
            "popularity": 40,
        },
        priority="exploration",
        market_score=30,
        identity_validation={
            "identity_score": 80,
        },
    )

    assert result["priority"] == "exploration"

    label, _ = classify_recommendation_type(
        {},
        priority="exploration",
    )

    assert label == "🧭 탐색 추천"


def test_discovery_mode_remains_distinct_priority() -> None:
    assert normalize_priority("discovery") == "discovery"

    result = build_recommendation_score_v8(
        {},
        {
            "quality": 70,
            "price": 60,
            "trust": 50,
            "popularity": 40,
        },
        priority="discovery",
        market_score=30,
        identity_validation={
            "identity_score": 80,
        },
    )

    assert result["priority"] == "discovery"

    label, _ = classify_recommendation_type(
        {},
        priority="discovery",
    )

    assert label == "💎 발견 추천"


def test_exploration_and_discovery_are_not_collapsed_to_mix() -> None:
    assert normalize_priority("exploration") != "mix"
    assert normalize_priority("discovery") != "mix"
