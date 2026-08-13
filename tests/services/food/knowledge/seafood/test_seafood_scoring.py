from __future__ import annotations

from app.services.food.knowledge.seafood.scoring import (
    DEFAULT_SEAFOOD_SCORE_WEIGHTS,
    calculate_seafood_final_score,
    calculate_seafood_information_score,
    calculate_seafood_scores,
)


def test_seafood_score_weights_sum_to_one():
    assert round(
        sum(DEFAULT_SEAFOOD_SCORE_WEIGHTS.values()),
        10,
    ) == 1.0


def test_calculate_seafood_scores_uses_external_scores():
    scores = calculate_seafood_scores(
        {
            "quality_score": 82,
            "price_score": 72,
            "trust_score": 88,
        },
        {
            "product_name": "연어",
            "species": "salmon",
            "seafood_group": "fish",
            "origin": "노르웨이",
            "processing_state": "fresh",
            "weight": "500g",
        },
    )

    assert scores["quality"] == 82.0
    assert scores["price"] == 72.0
    assert scores["trust"] == 88.0
    assert scores["information"] == 100.0


def test_information_score_handles_missing_fields():
    score = calculate_seafood_information_score(
        {
            "product_name": "연어",
            "species": "salmon",
            "seafood_group": "fish",
            "origin": None,
            "processing_state": None,
            "weight": None,
        }
    )

    assert score == 50.0


def test_final_score_is_deterministic():
    scores = {
        "quality": 82.0,
        "price": 72.0,
        "trust": 88.0,
        "information": 83.33,
    }

    first = calculate_seafood_final_score(scores)
    second = calculate_seafood_final_score(scores)

    assert first == second
    assert first == 81.53
