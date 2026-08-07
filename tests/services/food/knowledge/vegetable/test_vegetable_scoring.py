from copy import deepcopy

import pytest

from app.services.food.knowledge.vegetable.scoring import (
    calculate_vegetable_final_score,
    calculate_vegetable_information_score,
    calculate_vegetable_scores,
)


def test_vegetable_information_score_complete():
    attributes = {
        "product_name": "국산 상추 500g",
        "origin": "국산",
        "variety": "상추",
        "grade": "특",
        "weight": "500g",
    }

    assert (
        calculate_vegetable_information_score(
            attributes
        )
        == 100.0
    )


def test_vegetable_information_score_partial():
    attributes = {
        "product_name": "상추",
        "origin": None,
        "variety": "상추",
        "grade": None,
        "weight": None,
    }

    assert (
        calculate_vegetable_information_score(
            attributes
        )
        == 40.0
    )


def test_vegetable_scoring_is_deterministic():
    product = {
        "quality_score": 80,
        "price_score": 70,
        "trust_score": 90,
    }

    attributes = {
        "product_name": "상추 500g",
        "origin": "국산",
        "variety": "상추",
        "grade": "특",
        "weight": "500g",
    }

    first = calculate_vegetable_scores(
        product,
        attributes,
    )

    second = calculate_vegetable_scores(
        product,
        attributes,
    )

    assert first == second
    assert first is not second


def test_vegetable_scoring_does_not_mutate_inputs():
    product = {
        "quality_score": 80,
    }

    attributes = {
        "product_name": "상추",
        "variety": "상추",
    }

    product_before = deepcopy(product)
    attributes_before = deepcopy(
        attributes
    )

    calculate_vegetable_scores(
        product,
        attributes,
    )

    assert product == product_before
    assert attributes == attributes_before


def test_vegetable_final_score():
    final_score = (
        calculate_vegetable_final_score(
            {
                "quality": 80,
                "price": 70,
                "trust": 90,
                "information": 100,
            }
        )
    )

    assert final_score == 85.0


def test_vegetable_final_score_rejects_non_mapping():
    with pytest.raises(
        TypeError,
        match="scores must be a Mapping",
    ):
        calculate_vegetable_final_score(
            [80, 70]  # type: ignore[arg-type]
        )
