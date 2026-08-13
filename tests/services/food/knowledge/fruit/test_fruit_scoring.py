from __future__ import annotations

import pytest

from app.services.food.knowledge.fruit.scoring import (
    apply_context_score_adjustments,
    calculate_fruit_final_score,
    calculate_information_score,
    calculate_sweetness_score,
)
from app.services.food.knowledge.models import (
    FoodKnowledgeContext,
)


@pytest.mark.parametrize(
    ("brix", "expected"),
    [
        (None, 0.0),
        (7.0, 0.0),
        (8.0, 0.0),
        (12.0, 50.0),
        (16.0, 100.0),
        (20.0, 100.0),
    ],
)
def test_sweetness_score_boundaries(
    brix: float | None,
    expected: float,
) -> None:
    assert calculate_sweetness_score(
        brix
    ) == expected


def test_information_score_empty() -> None:
    assert calculate_information_score(
        {}
    ) == 0.0


def test_information_score_half_complete() -> None:
    attributes = {
        "product_name": "사과",
        "origin": "대한민국",
        "variety": "부사",
    }

    assert calculate_information_score(
        attributes
    ) == 50.0


def test_information_score_complete() -> None:
    attributes = {
        "product_name": "사과",
        "origin": "대한민국",
        "variety": "부사",
        "grade": "특",
        "brix": 13.0,
        "weight": "1kg",
    }

    assert calculate_information_score(
        attributes
    ) == 100.0


def test_quality_priority_boosts_quality_only() -> None:
    scores = {
        "quality": 70.0,
        "price": 60.0,
        "trust": 50.0,
        "sweetness": 40.0,
        "information": 30.0,
    }

    adjusted = apply_context_score_adjustments(
        scores,
        context=FoodKnowledgeContext(
            priority="quality"
        ),
    )

    assert adjusted["quality"] == 73.0
    assert adjusted["price"] == 60.0
    assert adjusted["trust"] == 50.0


def test_price_priority_boosts_price_only() -> None:
    scores = {
        "quality": 70.0,
        "price": 60.0,
        "trust": 50.0,
        "sweetness": 40.0,
        "information": 30.0,
    }

    adjusted = apply_context_score_adjustments(
        scores,
        context=FoodKnowledgeContext(
            priority="price"
        ),
    )

    assert adjusted["quality"] == 70.0
    assert adjusted["price"] == 63.0
    assert adjusted["trust"] == 50.0


def test_trust_priority_boosts_trust_only() -> None:
    scores = {
        "quality": 70.0,
        "price": 60.0,
        "trust": 50.0,
        "sweetness": 40.0,
        "information": 30.0,
    }

    adjusted = apply_context_score_adjustments(
        scores,
        context=FoodKnowledgeContext(
            priority="trust"
        ),
    )

    assert adjusted["quality"] == 70.0
    assert adjusted["price"] == 60.0
    assert adjusted["trust"] == 53.0


def test_score_boost_is_clamped() -> None:
    scores = {
        "quality": 99.0,
        "price": 0.0,
        "trust": 0.0,
        "sweetness": 0.0,
        "information": 0.0,
    }

    adjusted = apply_context_score_adjustments(
        scores,
        context=FoodKnowledgeContext(
            priority="quality"
        ),
    )

    assert adjusted["quality"] == 100.0


def test_default_final_score_is_deterministic() -> None:
    scores = {
        "quality": 80.0,
        "price": 60.0,
        "trust": 70.0,
        "sweetness": 50.0,
        "information": 100.0,
    }

    first = calculate_fruit_final_score(
        scores
    )
    second = calculate_fruit_final_score(
        scores
    )

    assert first == second
    assert 0.0 <= first <= 100.0


def test_priority_changes_final_weighting() -> None:
    scores = {
        "quality": 100.0,
        "price": 0.0,
        "trust": 0.0,
        "sweetness": 0.0,
        "information": 0.0,
    }

    default_score = calculate_fruit_final_score(
        scores
    )

    quality_score = calculate_fruit_final_score(
        scores,
        FoodKnowledgeContext(
            priority="quality"
        ),
    )

    assert quality_score > default_score
