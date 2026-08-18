from app.services.recommendation.recommendation_score_v8 import (
    apply_recommendation_score_v8,
)


def test_v8_score_application_preserves_runtime_score_aliases() -> None:
    item = {}

    scores = {
        "quality": 80,
        "price": 70,
        "trust": 60,
        "popularity": 50,
    }

    result = apply_recommendation_score_v8(
        item,
        scores,
        priority="mix",
        market_score=40,
        identity_validation={
            "identity_score": 90,
        },
    )

    final_score = result["final_score"]

    assert item["v8_final_score"] == final_score
    assert item["_v8_final_score"] == final_score
    assert item["_display_score"] == final_score
    assert item["final_recommendation_score"] == final_score


def test_v8_score_result_records_version_and_components() -> None:
    item = {}

    result = apply_recommendation_score_v8(
        item,
        {
            "quality": 80,
            "price": 70,
            "trust": 60,
            "popularity": 50,
        },
        priority="trust",
        market_score=40,
        identity_validation={
            "identity_score": 90,
        },
    )

    assert result["version"] == "v8"
    assert result["priority"] == "trust"

    assert set(result["components"]) == {
        "quality",
        "price",
        "trust",
        "popularity",
        "market",
        "identity",
    }

    assert item["_recommendation_v8"] == result
