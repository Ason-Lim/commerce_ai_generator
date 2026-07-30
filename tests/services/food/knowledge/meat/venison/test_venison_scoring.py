from __future__ import annotations

import pytest

from app.services.food.knowledge.meat.venison.parser import (
    VenisonParser,
)
from app.services.food.knowledge.meat.venison.scoring import (
    calculate_available_average,
    calculate_venison_final_score,
    calculate_venison_knowledge_score,
    calculate_venison_scores,
    clamp_score,
    extract_registry_scores,
    safe_float,
)


@pytest.fixture
def complete_product() -> dict[str, object]:
    return {
        "product_name": (
            "뉴질랜드산 어린사슴 "
            "레드디어 사슴안심 500g"
        ),
        "venison_type": "어린 사슴",
        "deer_species": "Red Deer",
        "cut": "사슴 안심",
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
    parse_result = VenisonParser().parse_product(
        complete_product
    )

    scores = extract_registry_scores(
        parse_result
    )

    assert scores == {
        "venison_type": 92.0,
        "breed": 90.0,
        "cut": 96.0,
        "tenderness": 91.0,
        "flavor": 87.0,
        "growth": 84.0,
        "rarity": 65.0,
        "fat": 30.0,
        "yield": 55.0,
    }


def test_calculate_venison_knowledge_score_complete() -> None:
    assert (
        calculate_venison_knowledge_score(
            venison_type_score=82,
            breed_score=85,
            cut_score=90,
        )
        == 86.6
    )


def test_knowledge_score_renormalizes_missing_fields() -> None:
    assert (
        calculate_venison_knowledge_score(
            venison_type_score=0,
            breed_score=0,
            cut_score=82,
        )
        == 82.0
    )

    assert (
        calculate_venison_knowledge_score(
            venison_type_score=82,
            breed_score=0,
            cut_score=90,
        )
        == 87.0
    )


def test_calculate_venison_scores_complete_product(
    complete_product: dict[str, object],
) -> None:
    parse_result = VenisonParser().parse_product(
        complete_product
    )

    scores = calculate_venison_scores(
        product=complete_product,
        parse_result=parse_result,
    )

    assert scores == {
        "quality": 80.0,
        "price": 70.0,
        "trust": 90.0,
        "venison_type": 92.0,
        "breed": 90.0,
        "cut": 96.0,
        "tenderness": 91.0,
        "flavor": 87.0,
        "growth": 84.0,
        "rarity": 65.0,
        "fat": 30.0,
        "yield": 55.0,
        "knowledge": 93.6,
    }


def test_calculate_venison_scores_cut_only() -> None:
    product = {
        "product_name": "뉴질랜드산 사슴안심 1kg",
        "cut": "사슴 안심",
    }

    parse_result = VenisonParser().parse_product(
        product
    )

    scores = calculate_venison_scores(
        product=product,
        parse_result=parse_result,
    )

    assert scores["venison_type"] == 0.0
    assert scores["breed"] == 0.0
    assert scores["cut"] == 96.0
    assert scores["knowledge"] == 96.0


def test_calculate_venison_final_score(
    complete_product: dict[str, object],
) -> None:
    parse_result = VenisonParser().parse_product(
        complete_product
    )

    scores = calculate_venison_scores(
        product=complete_product,
        parse_result=parse_result,
    )

    assert (
        calculate_venison_final_score(scores)
        == 86.8
    )


def test_final_score_supports_custom_weights() -> None:
    assert (
        calculate_venison_final_score(
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
        "product_name": "사슴가슴살",
        "quality_score": 120,
        "price_score": -5,
        "trust_score": "invalid",
    }

    parse_result = VenisonParser().parse_product(
        product
    )

    scores = calculate_venison_scores(
        product=product,
        parse_result=parse_result,
    )

    assert scores["quality"] == 100.0
    assert scores["price"] == 0.0
    assert scores["trust"] == 0.0


def test_scoring_rejects_invalid_product() -> None:
    parse_result = VenisonParser().parse(
        "사슴가슴살"
    )

    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        calculate_venison_scores(
            product="사슴가슴살",  # type: ignore[arg-type]
            parse_result=parse_result,
        )


def test_scoring_rejects_invalid_parse_result() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "parse_result must be "
            "VenisonParseResult"
        ),
    ):
        calculate_venison_scores(
            product={
                "product_name": "사슴가슴살"
            },
            parse_result=object(),  # type: ignore[arg-type]
        )


def test_extract_scores_rejects_invalid_parse_result() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "parse_result must be "
            "VenisonParseResult"
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
        calculate_venison_final_score(
            []  # type: ignore[arg-type]
        )
