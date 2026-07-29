from __future__ import annotations

import pytest

from app.services.food.knowledge.meat.duck.parser import (
    DuckParser,
)
from app.services.food.knowledge.meat.duck.scoring import (
    calculate_available_average,
    calculate_duck_final_score,
    calculate_duck_knowledge_score,
    calculate_duck_scores,
    clamp_score,
    extract_registry_scores,
    safe_float,
)


@pytest.fixture
def complete_product() -> dict[str, object]:
    return {
        "product_name": (
            "국내산 훈제오리 체리밸리 "
            "오리가슴살 500g"
        ),
        "quality_score": 80,
        "price_score": 70,
        "trust_score": 90,
    }


def test_safe_float_and_clamp_score() -> None:
    assert safe_float("12.5") == 12.5
    assert safe_float("invalid") == 0.0
    assert safe_float(
        None,
        default=7.0,
    ) == 7.0

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
    parse_result = DuckParser().parse_product(
        complete_product
    )

    scores = extract_registry_scores(
        parse_result
    )

    assert scores == {
        "duck_type": 82.0,
        "breed": 85.0,
        "cut": 90.0,
        "tenderness": 85.5,
        "flavor": 87.0,
        "growth": 95.0,
        "rarity": 35.0,
        "fat": 78.0,
        "yield": 82.0,
    }


def test_calculate_duck_knowledge_score_complete() -> None:
    assert (
        calculate_duck_knowledge_score(
            duck_type_score=82,
            breed_score=85,
            cut_score=90,
        )
        == 86.6
    )


def test_knowledge_score_renormalizes_missing_fields() -> None:
    assert (
        calculate_duck_knowledge_score(
            duck_type_score=0,
            breed_score=0,
            cut_score=82,
        )
        == 82.0
    )

    assert (
        calculate_duck_knowledge_score(
            duck_type_score=82,
            breed_score=0,
            cut_score=90,
        )
        == 87.0
    )


def test_calculate_duck_scores_complete_product(
    complete_product: dict[str, object],
) -> None:
    parse_result = DuckParser().parse_product(
        complete_product
    )

    scores = calculate_duck_scores(
        product=complete_product,
        parse_result=parse_result,
    )

    assert scores == {
        "quality": 80.0,
        "price": 70.0,
        "trust": 90.0,
        "duck_type": 82.0,
        "breed": 85.0,
        "cut": 90.0,
        "tenderness": 85.5,
        "flavor": 87.0,
        "growth": 95.0,
        "rarity": 35.0,
        "fat": 78.0,
        "yield": 82.0,
        "knowledge": 86.6,
    }


def test_calculate_duck_scores_cut_only() -> None:
    product = {
        "product_name": "국내산 오리가슴살 1kg",
    }

    parse_result = DuckParser().parse_product(
        product
    )

    scores = calculate_duck_scores(
        product=product,
        parse_result=parse_result,
    )

    assert scores["duck_type"] == 0.0
    assert scores["breed"] == 0.0
    assert scores["cut"] == 90.0
    assert scores["knowledge"] == 90.0
    assert scores["tenderness"] == 86.0
    assert scores["flavor"] == 92.0
    assert scores["growth"] == 0.0
    assert scores["rarity"] == 0.0
    assert scores["fat"] == 78.0
    assert scores["yield"] == 82.0


def test_calculate_duck_final_score(
    complete_product: dict[str, object],
) -> None:
    parse_result = DuckParser().parse_product(
        complete_product
    )

    scores = calculate_duck_scores(
        product=complete_product,
        parse_result=parse_result,
    )

    assert (
        calculate_duck_final_score(scores)
        == 83.3
    )


def test_final_score_supports_custom_weights() -> None:
    assert (
        calculate_duck_final_score(
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
        "product_name": "오리가슴살",
        "quality_score": 120,
        "price_score": -5,
        "trust_score": "invalid",
    }

    parse_result = DuckParser().parse_product(
        product
    )

    scores = calculate_duck_scores(
        product=product,
        parse_result=parse_result,
    )

    assert scores["quality"] == 100.0
    assert scores["price"] == 0.0
    assert scores["trust"] == 0.0


def test_scoring_rejects_invalid_product() -> None:
    parse_result = DuckParser().parse(
        "오리가슴살"
    )

    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        calculate_duck_scores(
            product="오리가슴살",  # type: ignore[arg-type]
            parse_result=parse_result,
        )


def test_scoring_rejects_invalid_parse_result() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "parse_result must be "
            "DuckParseResult"
        ),
    ):
        calculate_duck_scores(
            product={
                "product_name": "오리가슴살"
            },
            parse_result=object(),  # type: ignore[arg-type]
        )


def test_extract_scores_rejects_invalid_parse_result() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "parse_result must be "
            "DuckParseResult"
        ),
    ):
        extract_registry_scores(
            object()  # type: ignore[arg-type]
        )


def test_final_score_rejects_non_mapping() -> None:
    with pytest.raises(
        TypeError,
        match="scores must be a Mapping",
    ):
        calculate_duck_final_score(
            []  # type: ignore[arg-type]
        )
