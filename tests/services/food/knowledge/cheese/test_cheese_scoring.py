from __future__ import annotations

from copy import deepcopy

import pytest

from app.services.food.knowledge.cheese import (
    CHEESE_FINAL_SCORE_WEIGHTS,
    CHEESE_KNOWLEDGE_WEIGHTS,
    CheeseParser,
    calculate_available_average,
    calculate_available_weighted_score,
    calculate_cheese_final_score,
    calculate_cheese_knowledge_score,
    calculate_cheese_scores,
    clamp_score,
    extract_registry_scores,
    safe_float,
)


def _complete_product() -> dict[str, object]:
    return {
        "product_name": (
            "프랑스 산양유 브리 "
            "소프트 치즈 12개월 숙성"
        ),
        "cheese_type": "brie",
        "milk_source": "goat milk",
        "country": "프랑스",
        "texture": "soft cheese",
        "aging": "12개월 숙성",
        "quality_score": 80,
        "price_score": 70,
        "trust_score": 90,
    }


def test_default_scoring_weights() -> None:
    assert CHEESE_KNOWLEDGE_WEIGHTS == {
        "cheese_type": 0.30,
        "milk_source": 0.15,
        "origin": 0.20,
        "texture": 0.15,
        "aging": 0.20,
    }

    assert CHEESE_FINAL_SCORE_WEIGHTS == {
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
    ("value", "expected"),
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
    result = (
        calculate_available_weighted_score(
            scores={
                "a": 80,
                "b": 100,
                "c": 0,
            },
            weights={
                "a": 0.25,
                "b": 0.75,
                "c": 1.0,
            },
        )
    )

    assert result == 95.0


def test_available_weighted_score_rejects_invalid_inputs() -> None:
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
        CheeseParser().parse_product(
            _complete_product()
        )
    )

    scores = extract_registry_scores(
        parse_result
    )

    assert scores["cheese_type"] == 92.0
    assert scores["milk_source"] == 91.0
    assert scores["origin"] == 96.0
    assert scores["texture"] == 89.0
    assert scores["aging"] == 94.0

    assert scores["flavor"] == 88.0
    assert scores["versatility"] == 82.0
    assert scores["richness"] == 87.0
    assert scores["availability"] == 68.0
    assert scores["tradition"] == 99.0
    assert scores["firmness"] == 30.0
    assert scores["moisture"] == 82.0


def test_extract_partial_registry_scores() -> None:
    parse_result = CheeseParser().parse(
        "24개월 숙성 "
        "파르미자노 레지아노"
    )

    scores = extract_registry_scores(
        parse_result
    )

    assert scores["cheese_type"] == 96.0
    assert scores["aging"] == 97.0

    assert scores["milk_source"] == 0.0
    assert scores["origin"] == 0.0
    assert scores["texture"] == 0.0

    assert scores["flavor"] == 96.0
    assert scores["versatility"] == 93.0


def test_extract_unknown_registry_scores() -> None:
    parse_result = CheeseParser().parse(
        "상품 정보가 없는 일반 문자열"
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
            "CheeseParseResult"
        ),
    ):
        extract_registry_scores(
            object()  # type: ignore[arg-type]
        )


def test_calculate_complete_knowledge_score() -> None:
    score = calculate_cheese_knowledge_score(
        cheese_type_score=92,
        milk_source_score=91,
        origin_score=96,
        texture_score=89,
        aging_score=94,
    )

    # 92×0.30 + 91×0.15 + 96×0.20
    # + 89×0.15 + 94×0.20
    assert score == 92.6


def test_knowledge_score_uses_available_fields() -> None:
    score = calculate_cheese_knowledge_score(
        cheese_type_score=96,
        aging_score=97,
    )

    # (96×0.30 + 97×0.20) / 0.50
    assert score == 96.4

    assert calculate_cheese_knowledge_score(
        cheese_type_score=0,
        milk_source_score=0,
        origin_score=0,
        texture_score=0,
        aging_score=0,
    ) == 0.0


def test_knowledge_score_custom_weights() -> None:
    score = calculate_cheese_knowledge_score(
        cheese_type_score=80,
        aging_score=100,
        weights={
            "cheese_type": 0.0,
            "aging": 1.0,
        },
    )

    assert score == 100.0


def test_calculate_cheese_scores() -> None:
    product = _complete_product()

    parse_result = (
        CheeseParser().parse_product(
            product
        )
    )

    scores = calculate_cheese_scores(
        product=product,
        parse_result=parse_result,
    )

    assert scores["quality"] == 80.0
    assert scores["price"] == 70.0
    assert scores["trust"] == 90.0
    assert scores["knowledge"] == 92.6

    assert scores["cheese_type"] == 92.0
    assert scores["milk_source"] == 91.0
    assert scores["origin"] == 96.0
    assert scores["texture"] == 89.0
    assert scores["aging"] == 94.0


def test_calculate_cheese_scores_clamps_external_scores() -> None:
    product = {
        "product_name": "브리 치즈",
        "quality_score": 150,
        "price_score": -20,
        "trust_score": "85",
    }

    parse_result = (
        CheeseParser().parse_product(
            product
        )
    )

    scores = calculate_cheese_scores(
        product=product,
        parse_result=parse_result,
    )

    assert scores["quality"] == 100.0
    assert scores["price"] == 0.0
    assert scores["trust"] == 85.0
    assert scores["knowledge"] == 92.0


def test_calculate_cheese_scores_rejects_invalid_product() -> None:
    parse_result = CheeseParser().parse(
        "브리 치즈"
    )

    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        calculate_cheese_scores(
            product="브리 치즈",  # type: ignore[arg-type]
            parse_result=parse_result,
        )


def test_calculate_cheese_scores_rejects_wrong_parse_result() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "parse_result must be "
            "CheeseParseResult"
        ),
    ):
        calculate_cheese_scores(
            product={
                "product_name": "브리 치즈",
            },
            parse_result=object(),  # type: ignore[arg-type]
        )


def test_calculate_cheese_final_score() -> None:
    final_score = (
        calculate_cheese_final_score(
            {
                "quality": 80,
                "price": 70,
                "trust": 90,
                "knowledge": 92.8,
            }
        )
    )

    # 80×0.20 + 70×0.15
    # + 90×0.15 + 92.8×0.50
    assert final_score == 86.4


def test_final_score_missing_external_values() -> None:
    final_score = (
        calculate_cheese_final_score(
            {
                "knowledge": 96.4,
            }
        )
    )

    assert final_score == 48.2


def test_final_score_custom_weights() -> None:
    final_score = (
        calculate_cheese_final_score(
            {
                "quality": 80,
                "price": 70,
                "trust": 90,
                "knowledge": 92.8,
            },
            weights={
                "quality": 0.0,
                "price": 0.0,
                "trust": 0.0,
                "knowledge": 1.0,
            },
        )
    )

    assert final_score == 92.8


def test_final_score_rejects_non_mapping() -> None:
    with pytest.raises(
        TypeError,
        match="scores must be a Mapping",
    ):
        calculate_cheese_final_score(
            [80, 70, 90]  # type: ignore[arg-type]
        )


def test_scoring_does_not_mutate_inputs() -> None:
    product = _complete_product()
    product_before = deepcopy(product)

    parse_result = (
        CheeseParser().parse_product(
            product
        )
    )
    parse_result_before = (
        parse_result.to_dict()
    )

    calculate_cheese_scores(
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
        CheeseParser().parse_product(
            product
        )
    )

    first = calculate_cheese_scores(
        product=product,
        parse_result=parse_result,
    )

    second = calculate_cheese_scores(
        product=product,
        parse_result=parse_result,
    )

    assert first == second
    assert first is not second
