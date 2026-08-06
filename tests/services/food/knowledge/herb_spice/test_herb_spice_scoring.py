from __future__ import annotations

from copy import deepcopy

import pytest

from app.services.food.knowledge.herb_spice.parser import (
    HerbSpiceParser,
)
from app.services.food.knowledge.herb_spice.scoring import (
    HERB_SPICE_FINAL_SCORE_WEIGHTS,
    HERB_SPICE_KNOWLEDGE_WEIGHTS,
    calculate_available_average,
    calculate_available_weighted_score,
    calculate_herb_spice_final_score,
    calculate_herb_spice_knowledge_score,
    calculate_herb_spice_scores,
    clamp_score,
    extract_registry_scores,
    safe_float,
)


def _complete_product() -> dict[str, object]:
    return {
        "product_name": (
            "프랑스산 건조 로즈마리 "
            "오븐 구이용"
        ),
        "classification": "herb",
        "ingredient": "rosemary",
        "origin": "France",
        "product_form": "dried herb",
        "recommended_usage": "roasting",
        "quality_score": 80,
        "price_score": 70,
        "trust_score": 90,
    }


def test_default_scoring_weights() -> None:
    assert HERB_SPICE_KNOWLEDGE_WEIGHTS == {
        "ingredient": 0.40,
        "origin": 0.20,
        "form": 0.20,
        "usage": 0.20,
    }

    assert round(
        sum(
            HERB_SPICE_KNOWLEDGE_WEIGHTS.values()
        ),
        10,
    ) == 1.0

    assert HERB_SPICE_FINAL_SCORE_WEIGHTS == {
        "quality": 0.20,
        "price": 0.15,
        "trust": 0.15,
        "knowledge": 0.50,
    }


def test_safe_float() -> None:
    assert safe_float("12.5") == 12.5
    assert safe_float(10) == 10.0
    assert safe_float(None) == 0.0
    assert safe_float(
        "invalid",
        7.0,
    ) == 7.0


@pytest.mark.parametrize(
    (
        "value",
        "expected",
    ),
    [
        (-10, 0.0),
        (0, 0.0),
        (50, 50.0),
        (100, 100.0),
        (120, 100.0),
        ("75.5", 75.5),
        (None, 0.0),
    ],
)
def test_clamp_score(
    value: object,
    expected: float,
) -> None:
    assert clamp_score(value) == expected


def test_calculate_available_average() -> None:
    assert calculate_available_average(
        80,
        90,
        0,
        None,
    ) == 85.0

    assert calculate_available_average(
        0,
        None,
        "invalid",
    ) == 0.0


def test_calculate_available_weighted_score() -> None:
    score = calculate_available_weighted_score(
        scores={
            "ingredient": 80,
            "origin": 100,
            "form": 0,
            "usage": 0,
        },
        weights={
            "ingredient": 0.40,
            "origin": 0.20,
            "form": 0.20,
            "usage": 0.20,
        },
    )

    expected = round(
        (
            (80 * 0.40)
            + (100 * 0.20)
        )
        / (0.40 + 0.20),
        2,
    )

    assert score == expected


def test_weighted_score_rejects_invalid_inputs() -> None:
    with pytest.raises(
        TypeError,
        match="scores must be a Mapping",
    ):
        calculate_available_weighted_score(
            scores=[],  # type: ignore[arg-type]
            weights={},
        )

    with pytest.raises(
        TypeError,
        match="weights must be a Mapping",
    ):
        calculate_available_weighted_score(
            scores={},
            weights=[],  # type: ignore[arg-type]
        )


def test_extract_complete_registry_scores() -> None:
    parse_result = (
        HerbSpiceParser().parse_product(
            _complete_product()
        )
    )

    scores = extract_registry_scores(
        parse_result
    )

    # 현재 Herb & Spice YAML Registry score는 모두 0이다.
    assert scores == {
        "ingredient": 0.0,
        "origin": 0.0,
        "form": 0.0,
        "usage": 0.0,
    }


def test_extract_spice_registry_scores() -> None:
    parse_result = (
        HerbSpiceParser().parse(
            "인도산 큐민 파우더 스튜용"
        )
    )

    scores = extract_registry_scores(
        parse_result
    )

    assert scores == {
        "ingredient": 0.0,
        "origin": 0.0,
        "form": 0.0,
        "usage": 0.0,
    }


def test_extract_partial_registry_scores() -> None:
    parse_result = (
        HerbSpiceParser().parse(
            "프랑스산 건조 상품"
        )
    )

    scores = extract_registry_scores(
        parse_result
    )

    assert scores["ingredient"] == 0.0
    assert scores["origin"] == 0.0
    assert scores["form"] == 0.0
    assert scores["usage"] == 0.0


def test_extract_unknown_registry_scores() -> None:
    parse_result = (
        HerbSpiceParser().parse(
            "상품 정보가 없는 일반 문자열"
        )
    )

    scores = extract_registry_scores(
        parse_result
    )

    assert all(
        score == 0.0
        for score in scores.values()
    )


def test_extract_registry_scores_rejects_wrong_type() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "parse_result must be "
            "HerbSpiceParseResult"
        ),
    ):
        extract_registry_scores(
            object()  # type: ignore[arg-type]
        )


def test_calculate_complete_knowledge_score() -> None:
    score = (
        calculate_herb_spice_knowledge_score(
            ingredient_score=90,
            origin_score=80,
            form_score=70,
            usage_score=100,
        )
    )

    expected = round(
        (
            (90 * 0.40)
            + (80 * 0.20)
            + (70 * 0.20)
            + (100 * 0.20)
        ),
        2,
    )

    assert score == expected


def test_knowledge_score_uses_available_fields() -> None:
    score = (
        calculate_herb_spice_knowledge_score(
            ingredient_score=80,
            origin_score=100,
        )
    )

    expected = round(
        (
            (80 * 0.40)
            + (100 * 0.20)
        )
        / (0.40 + 0.20),
        2,
    )

    assert score == expected

    assert (
        calculate_herb_spice_knowledge_score()
        == 0.0
    )


def test_knowledge_score_custom_weights() -> None:
    score = (
        calculate_herb_spice_knowledge_score(
            ingredient_score=80,
            usage_score=100,
            weights={
                "ingredient": 0.0,
                "usage": 1.0,
            },
        )
    )

    assert score == 100.0


def test_calculate_herb_spice_scores() -> None:
    product = _complete_product()

    parse_result = (
        HerbSpiceParser().parse_product(
            product
        )
    )

    scores = calculate_herb_spice_scores(
        product=product,
        parse_result=parse_result,
    )

    assert scores["quality"] == 80.0
    assert scores["price"] == 70.0
    assert scores["trust"] == 90.0

    # Registry YAML score가 모두 0이므로 Knowledge도 0이다.
    assert scores["knowledge"] == 0.0

    assert scores["ingredient"] == 0.0
    assert scores["origin"] == 0.0
    assert scores["form"] == 0.0
    assert scores["usage"] == 0.0


def test_calculate_scores_clamps_external_scores() -> None:
    product = {
        "product_name": "로즈마리",
        "quality_score": 150,
        "price_score": -20,
        "trust_score": "85",
    }

    parse_result = (
        HerbSpiceParser().parse_product(
            product
        )
    )

    scores = calculate_herb_spice_scores(
        product=product,
        parse_result=parse_result,
    )

    assert scores["quality"] == 100.0
    assert scores["price"] == 0.0
    assert scores["trust"] == 85.0
    assert scores["knowledge"] == 0.0


def test_calculate_scores_without_external_scores() -> None:
    product = {
        "product_name": "로즈마리",
    }

    parse_result = (
        HerbSpiceParser().parse_product(
            product
        )
    )

    scores = calculate_herb_spice_scores(
        product=product,
        parse_result=parse_result,
    )

    assert scores["quality"] == 0.0
    assert scores["price"] == 0.0
    assert scores["trust"] == 0.0
    assert scores["knowledge"] == 0.0


def test_calculate_scores_rejects_invalid_product() -> None:
    parse_result = (
        HerbSpiceParser().parse(
            "로즈마리"
        )
    )

    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        calculate_herb_spice_scores(
            product="로즈마리",  # type: ignore[arg-type]
            parse_result=parse_result,
        )


def test_calculate_scores_rejects_wrong_result() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "parse_result must be "
            "HerbSpiceParseResult"
        ),
    ):
        calculate_herb_spice_scores(
            product={
                "product_name": "로즈마리",
            },
            parse_result=object(),  # type: ignore[arg-type]
        )


def test_calculate_final_score() -> None:
    score = calculate_herb_spice_final_score(
        {
            "quality": 80,
            "price": 70,
            "trust": 90,
            "knowledge": 85,
        }
    )

    assert score == 82.5


def test_final_score_missing_values_are_not_renormalized() -> None:
    score = calculate_herb_spice_final_score(
        {
            "knowledge": 90,
        }
    )

    assert score == 45.0


def test_final_score_custom_weights() -> None:
    score = calculate_herb_spice_final_score(
        {
            "quality": 80,
            "price": 70,
            "trust": 90,
            "knowledge": 85,
        },
        weights={
            "quality": 0.0,
            "price": 0.0,
            "trust": 0.0,
            "knowledge": 1.0,
        },
    )

    assert score == 85.0


def test_final_score_clamps_values() -> None:
    score = calculate_herb_spice_final_score(
        {
            "quality": 200,
            "price": -10,
            "trust": "90",
            "knowledge": 120,
        }
    )

    expected = round(
        (
            (100 * 0.20)
            + (0 * 0.15)
            + (90 * 0.15)
            + (100 * 0.50)
        ),
        2,
    )

    assert score == expected


def test_final_score_rejects_non_mapping() -> None:
    with pytest.raises(
        TypeError,
        match="scores must be a Mapping",
    ):
        calculate_herb_spice_final_score(
            [80, 70, 90]  # type: ignore[arg-type]
        )


def test_scoring_does_not_mutate_inputs() -> None:
    product = _complete_product()
    product_before = deepcopy(product)

    parse_result = (
        HerbSpiceParser().parse_product(
            product
        )
    )
    parse_result_before = (
        parse_result.to_dict()
    )

    calculate_herb_spice_scores(
        product=product,
        parse_result=parse_result,
    )

    assert product == product_before
    assert (
        parse_result.to_dict()
        == parse_result_before
    )


def test_scoring_is_deterministic() -> None:
    product = _complete_product()

    parse_result = (
        HerbSpiceParser().parse_product(
            product
        )
    )

    first = calculate_herb_spice_scores(
        product=product,
        parse_result=parse_result,
    )
    second = calculate_herb_spice_scores(
        product=product,
        parse_result=parse_result,
    )

    assert first == second
    assert first is not second

    assert (
        calculate_herb_spice_final_score(
            first
        )
        == calculate_herb_spice_final_score(
            second
        )
    )
