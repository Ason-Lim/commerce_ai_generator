from copy import deepcopy

from app.services.recommendation.recommendation_score_v8 import (
    build_recommendation_score_v8,
)


def test_recommendation_score_v8_is_deterministic() -> None:
    item = {
        "product_name": "테스트 상품",
        "trend_score": 65,
    }

    scores = {
        "quality": 82,
        "price": 74,
        "trust": 91,
        "popularity": 55,
    }

    identity = {
        "identity_score": 88,
    }

    first = build_recommendation_score_v8(
        deepcopy(item),
        deepcopy(scores),
        priority="mix",
        market_score=65,
        identity_validation=deepcopy(identity),
    )

    second = build_recommendation_score_v8(
        deepcopy(item),
        deepcopy(scores),
        priority="mix",
        market_score=65,
        identity_validation=deepcopy(identity),
    )

    assert first == second


def test_recommendation_score_v8_is_clamped_to_valid_range() -> None:
    result = build_recommendation_score_v8(
        {},
        {
            "quality": 1000,
            "price": -100,
            "trust": 200,
            "popularity": -50,
        },
        priority="mix",
        market_score=500,
        identity_validation={
            "identity_score": 999,
        },
    )

    assert 0 <= result["final_score"] <= 100

    for component in result["components"].values():
        assert 0 <= component <= 100
