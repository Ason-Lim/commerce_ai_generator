from __future__ import annotations

import pytest

from app.services.food.knowledge.meat.chicken.parser import (
    ChickenParser,
)
from app.services.food.knowledge.meat.chicken.scoring import (
    calculate_available_average,
    calculate_chicken_final_score,
    calculate_chicken_knowledge_score,
    calculate_chicken_scores,
    clamp_score,
    extract_registry_scores,
    safe_float,
)


@pytest.fixture
def complete_product() -> dict[str, object]:
    return {
        "product_name": (
            "국내산 토종닭 Ross 308 "
            "닭다리살 500g"
        ),
        "quality_score": 80,
        "price_score": 70,
        "trust_score": 90,
    }


def test_safe_float_and_clamp_score() -> None:
    assert safe_float("12.5") == 12.5
    assert safe_float("invalid") == 0.0
    assert safe_float(None, default=7.0) == 7.0

    assert clamp_score(-10) == 0.0
    assert clamp_score(120) == 100.0
    assert clamp_score("82.5") == 82.5


def test_calculate_available_average() -> None:
    assert (
        calculate_available_average(
            80,
            90,
            0,
            None,
        )
        == 85.0
    )
    assert (
        calculate_available_average(
            0,
            None,
            "invalid",
        )
        == 0.0
    )


def test_extract_registry_scores_complete_product(
    complete_product: dict[str, object],
) -> None:
    parse_result = ChickenParser().parse_product(
        complete_product
    )

    scores = extract_registry_scores(
        parse_result
    )

    assert scores == {
        "chicken_type": 88.0,
        "breed": 82.0,
        "cut": 88.0,
        "tenderness": 85.0,
        "flavor": 83.0,
        "growth": 94.0,
        "rarity": 35.0,
        "fat": 78.0,
        "yield": 82.0,
    }


def test_calculate_chicken_knowledge_score_complete() -> None:
    assert (
        calculate_chicken_knowledge_score(
            chicken_type_score=88,
            breed_score=82,
            cut_score=88,
        )
        == 86.8
    )


def test_knowledge_score_renormalizes_missing_fields() -> None:
    assert (
        calculate_chicken_knowledge_score(
            chicken_type_score=0,
            breed_score=0,
            cut_score=82,
        )
        == 82.0
    )

    assert (
        calculate_chicken_knowledge_score(
            chicken_type_score=88,
            breed_score=0,
            cut_score=82,
        )
        == 84.25
    )


def test_calculate_chicken_scores_complete_product(
    complete_product: dict[str, object],
) -> None:
    parse_result = ChickenParser().parse_product(
        complete_product
    )

    scores = calculate_chicken_scores(
        product=complete_product,
        parse_result=parse_result,
    )

    assert scores == {
        "quality": 80.0,
        "price": 70.0,
        "trust": 90.0,
        "chicken_type": 88.0,
        "breed": 82.0,
        "cut": 88.0,
        "tenderness": 85.0,
        "flavor": 83.0,
        "growth": 94.0,
        "rarity": 35.0,
        "fat": 78.0,
        "yield": 82.0,
        "knowledge": 86.8,
    }


def test_calculate_chicken_scores_cut_only() -> None:
    product = {
        "product_name": "국내산 닭가슴살 1kg",
    }

    parse_result = ChickenParser().parse_product(
        product
    )

    scores = calculate_chicken_scores(
        product=product,
        parse_result=parse_result,
    )

    assert scores["chicken_type"] == 0.0
    assert scores["breed"] == 0.0
    assert scores["cut"] == 82.0
    assert scores["knowledge"] == 82.0
    assert scores["tenderness"] == 78.0
    assert scores["flavor"] == 70.0
    assert scores["growth"] == 0.0
    assert scores["rarity"] == 0.0


def test_calculate_chicken_final_score(
    complete_product: dict[str, object],
) -> None:
    parse_result = ChickenParser().parse_product(
        complete_product
    )

    scores = calculate_chicken_scores(
        product=complete_product,
        parse_result=parse_result,
    )

    assert (
        calculate_chicken_final_score(scores)
        == 83.4
    )


def test_final_score_supports_custom_weights() -> None:
    assert (
        calculate_chicken_final_score(
            {
                "quality": 80,
                "knowledge": 90,
            },
            weights={
                "quality": 0.5,
                "knowledge": 0.5,
            },
        )
        == 85.0
    )


def test_scoring_clamps_external_scores() -> None:
    product = {
        "product_name": "닭가슴살",
        "quality_score": 120,
        "price_score": -5,
        "trust_score": "invalid",
    }

    parse_result = ChickenParser().parse_product(
        product
    )

    scores = calculate_chicken_scores(
        product=product,
        parse_result=parse_result,
    )

    assert scores["quality"] == 100.0
    assert scores["price"] == 0.0
    assert scores["trust"] == 0.0


def test_scoring_rejects_invalid_product() -> None:
    parse_result = ChickenParser().parse(
        "닭가슴살"
    )

    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        calculate_chicken_scores(
            product="닭가슴살",  # type: ignore[arg-type]
            parse_result=parse_result,
        )


def test_scoring_rejects_invalid_parse_result() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "parse_result must be "
            "ChickenParseResult"
        ),
    ):
        calculate_chicken_scores(
            product={
                "product_name": "닭가슴살"
            },
            parse_result=object(),  # type: ignore[arg-type]
        )


def test_final_score_rejects_non_mapping() -> None:
    with pytest.raises(
        TypeError,
        match="scores must be a Mapping",
    ):
        calculate_chicken_final_score(
            []  # type: ignore[arg-type]
        )
