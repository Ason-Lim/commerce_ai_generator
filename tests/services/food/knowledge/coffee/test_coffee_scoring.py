from __future__ import annotations

from copy import deepcopy

import pytest

from app.services.food.knowledge.coffee import (
    COFFEE_FINAL_SCORE_WEIGHTS,
    COFFEE_KNOWLEDGE_WEIGHTS,
    CoffeeParser,
    calculate_available_average,
    calculate_available_weighted_score,
    calculate_coffee_final_score,
    calculate_coffee_knowledge_score,
    calculate_coffee_scores,
    clamp_score,
    extract_registry_scores,
    safe_float,
)


def _complete_product() -> dict[str, object]:
    return {
        "product_name": (
            "에티오피아 100% 아라비카 "
            "라이트 로스트 워시드 원두"
        ),
        "bean_type": "100% arabica",
        "origin_country": "Ethiopia",
        "roast_level": "light roast",
        "processing_method": "washed process",
        "quality_score": 80,
        "price_score": 70,
        "trust_score": 90,
    }


def test_default_scoring_weights() -> None:
    assert COFFEE_KNOWLEDGE_WEIGHTS == {
        "bean": 0.30,
        "origin": 0.25,
        "roast": 0.20,
        "process": 0.25,
    }

    assert COFFEE_FINAL_SCORE_WEIGHTS == {
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
        CoffeeParser().parse_product(
            _complete_product()
        )
    )

    scores = extract_registry_scores(
        parse_result
    )

    assert scores["bean"] == 92.0
    assert scores["origin"] == 96.0
    assert scores["roast"] == 91.0
    assert scores["process"] == 91.0

    assert scores["acidity"] == 92.67
    assert scores["body"] == 72.25
    assert scores["aroma"] == 94.67
    assert scores["clarity"] == 96.0
    assert scores["sweetness"] == 82.0


def test_extract_partial_registry_scores() -> None:
    parse_result = CoffeeParser().parse(
        "에티오피아 워시드 커피"
    )

    scores = extract_registry_scores(
        parse_result
    )

    assert scores["bean"] == 0.0
    assert scores["origin"] == 96.0
    assert scores["roast"] == 0.0
    assert scores["process"] == 91.0

    assert scores["acidity"] == 94.0
    assert scores["body"] == 74.0
    assert scores["aroma"] == 98.0
    assert scores["clarity"] == 96.0
    assert scores["sweetness"] == 82.0


def test_extract_unknown_registry_scores() -> None:
    parse_result = CoffeeParser().parse(
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
            "CoffeeParseResult"
        ),
    ):
        extract_registry_scores(
            object()  # type: ignore[arg-type]
        )


def test_calculate_complete_knowledge_score() -> None:
    score = calculate_coffee_knowledge_score(
        bean_score=92,
        origin_score=96,
        roast_score=91,
        process_score=91,
    )

    assert score == 92.55


def test_knowledge_score_uses_available_fields() -> None:
    score = calculate_coffee_knowledge_score(
        origin_score=96,
        process_score=91,
    )

    assert score == 93.5

    assert calculate_coffee_knowledge_score(
        bean_score=0,
        origin_score=0,
        roast_score=0,
        process_score=0,
    ) == 0.0


def test_knowledge_score_custom_weights() -> None:
    score = calculate_coffee_knowledge_score(
        bean_score=80,
        process_score=100,
        weights={
            "bean": 0.0,
            "process": 1.0,
        },
    )

    assert score == 100.0


def test_calculate_coffee_scores() -> None:
    product = _complete_product()

    parse_result = (
        CoffeeParser().parse_product(
            product
        )
    )

    scores = calculate_coffee_scores(
        product=product,
        parse_result=parse_result,
    )

    assert scores["quality"] == 80.0
    assert scores["price"] == 70.0
    assert scores["trust"] == 90.0
    assert scores["knowledge"] == 92.55

    assert scores["bean"] == 92.0
    assert scores["origin"] == 96.0
    assert scores["roast"] == 91.0
    assert scores["process"] == 91.0


def test_calculate_coffee_scores_clamps_external_scores() -> None:
    product = {
        "product_name": "아라비카 원두",
        "quality_score": 150,
        "price_score": -20,
        "trust_score": "85",
    }

    parse_result = (
        CoffeeParser().parse_product(
            product
        )
    )

    scores = calculate_coffee_scores(
        product=product,
        parse_result=parse_result,
    )

    assert scores["quality"] == 100.0
    assert scores["price"] == 0.0
    assert scores["trust"] == 85.0
    assert scores["knowledge"] == 92.0


def test_calculate_coffee_scores_rejects_invalid_product() -> None:
    parse_result = CoffeeParser().parse(
        "아라비카 원두"
    )

    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        calculate_coffee_scores(
            product="아라비카",  # type: ignore[arg-type]
            parse_result=parse_result,
        )


def test_calculate_coffee_scores_rejects_wrong_parse_result() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "parse_result must be "
            "CoffeeParseResult"
        ),
    ):
        calculate_coffee_scores(
            product={
                "product_name": (
                    "아라비카 원두"
                ),
            },
            parse_result=object(),  # type: ignore[arg-type]
        )


def test_calculate_coffee_final_score() -> None:
    final_score = (
        calculate_coffee_final_score(
            {
                "quality": 80,
                "price": 70,
                "trust": 90,
                "knowledge": 92.55,
            }
        )
    )

    assert final_score == 86.28


def test_final_score_missing_external_values() -> None:
    final_score = (
        calculate_coffee_final_score(
            {
                "knowledge": 93.5,
            }
        )
    )

    assert final_score == 46.75


def test_final_score_custom_weights() -> None:
    final_score = (
        calculate_coffee_final_score(
            {
                "quality": 80,
                "price": 70,
                "trust": 90,
                "knowledge": 92.55,
            },
            weights={
                "quality": 0.0,
                "price": 0.0,
                "trust": 0.0,
                "knowledge": 1.0,
            },
        )
    )

    assert final_score == 92.55


def test_final_score_rejects_non_mapping() -> None:
    with pytest.raises(
        TypeError,
        match="scores must be a Mapping",
    ):
        calculate_coffee_final_score(
            [80, 70, 90]  # type: ignore[arg-type]
        )


def test_scoring_does_not_mutate_inputs() -> None:
    product = _complete_product()
    product_before = deepcopy(product)

    parse_result = (
        CoffeeParser().parse_product(
            product
        )
    )
    parse_result_before = (
        parse_result.to_dict()
    )

    calculate_coffee_scores(
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
        CoffeeParser().parse_product(
            product
        )
    )

    first = calculate_coffee_scores(
        product=product,
        parse_result=parse_result,
    )

    second = calculate_coffee_scores(
        product=product,
        parse_result=parse_result,
    )

    assert first == second
    assert first is not second
