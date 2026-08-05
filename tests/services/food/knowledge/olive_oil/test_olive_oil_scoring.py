from __future__ import annotations

from copy import deepcopy

import pytest

from app.services.food.knowledge.olive_oil.parser import (
    OliveOilParser,
)
from app.services.food.knowledge.olive_oil.scoring import (
    OLIVE_OIL_FINAL_SCORE_WEIGHTS,
    OLIVE_OIL_KNOWLEDGE_WEIGHTS,
    calculate_available_average,
    calculate_available_weighted_score,
    calculate_olive_oil_final_score,
    calculate_olive_oil_knowledge_score,
    calculate_olive_oil_scores,
    clamp_score,
    extract_registry_scores,
    safe_float,
)


def _complete_product() -> dict[str, object]:
    return {
        "product_name": (
            "스페인산 아르베키나 단일 품종 "
            "냉압착 엑스트라 버진 올리브오일"
        ),
        "olive_oil_type": "single varietal",
        "cultivar": "Arbequina",
        "origin_country": "Spain",
        "extraction_method": "cold pressed",
        "grade": "extra virgin olive oil",
        "quality_score": 80,
        "price_score": 70,
        "trust_score": 90,
    }


def test_default_scoring_weights() -> None:
    assert OLIVE_OIL_KNOWLEDGE_WEIGHTS == {
        "olive_oil_type": 0.20,
        "variety": 0.15,
        "origin": 0.20,
        "processing": 0.15,
        "grade": 0.30,
    }

    assert round(
        sum(OLIVE_OIL_KNOWLEDGE_WEIGHTS.values()),
        10,
    ) == 1.0

    assert OLIVE_OIL_FINAL_SCORE_WEIGHTS == {
        "quality": 0.20,
        "price": 0.15,
        "trust": 0.15,
        "knowledge": 0.50,
    }


def test_safe_float() -> None:
    assert safe_float("12.5") == 12.5
    assert safe_float(10) == 10.0
    assert safe_float(None) == 0.0
    assert safe_float("invalid", 7.0) == 7.0


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
    result = calculate_available_weighted_score(
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

    assert result == 95.0


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
    parse_result = OliveOilParser().parse_product(
        _complete_product()
    )

    scores = extract_registry_scores(parse_result)

    assert scores == {
        "olive_oil_type": 0.0,
        "variety": 0.0,
        "origin": 0.0,
        "processing": 0.0,
        "grade": 95.0,
    }


def test_extract_partial_registry_scores() -> None:
    parse_result = OliveOilParser().parse(
        "버진 올리브오일"
    )

    scores = extract_registry_scores(parse_result)

    assert scores["grade"] == 85.0
    assert scores["olive_oil_type"] == 0.0
    assert scores["variety"] == 0.0
    assert scores["origin"] == 0.0
    assert scores["processing"] == 0.0


def test_extract_unknown_registry_scores() -> None:
    parse_result = OliveOilParser().parse(
        "상품 정보가 없는 일반 문자열"
    )

    scores = extract_registry_scores(parse_result)

    assert all(
        score == 0.0
        for score in scores.values()
    )


def test_extract_registry_scores_rejects_wrong_type() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "parse_result must be "
            "OliveOilParseResult"
        ),
    ):
        extract_registry_scores(
            object()  # type: ignore[arg-type]
        )


def test_calculate_complete_knowledge_score() -> None:
    score = calculate_olive_oil_knowledge_score(
        olive_oil_type_score=80,
        variety_score=85,
        origin_score=90,
        processing_score=95,
        grade_score=100,
    )

    assert score == 91.0


def test_knowledge_score_uses_available_fields() -> None:
    score = calculate_olive_oil_knowledge_score(
        origin_score=80,
        grade_score=100,
    )

    assert score == 92.0
    assert calculate_olive_oil_knowledge_score() == 0.0


def test_knowledge_score_custom_weights() -> None:
    score = calculate_olive_oil_knowledge_score(
        olive_oil_type_score=80,
        grade_score=100,
        weights={
            "olive_oil_type": 0.0,
            "grade": 1.0,
        },
    )

    assert score == 100.0


def test_calculate_olive_oil_scores() -> None:
    product = _complete_product()
    parse_result = OliveOilParser().parse_product(
        product
    )

    scores = calculate_olive_oil_scores(
        product=product,
        parse_result=parse_result,
    )

    assert scores["quality"] == 80.0
    assert scores["price"] == 70.0
    assert scores["trust"] == 90.0
    assert scores["knowledge"] == 95.0

    assert scores["olive_oil_type"] == 0.0
    assert scores["variety"] == 0.0
    assert scores["origin"] == 0.0
    assert scores["processing"] == 0.0
    assert scores["grade"] == 95.0


def test_scores_clamp_external_values() -> None:
    product = {
        "product_name": (
            "엑스트라 버진 올리브오일"
        ),
        "quality_score": 150,
        "price_score": -20,
        "trust_score": "85",
    }

    parse_result = OliveOilParser().parse_product(
        product
    )

    scores = calculate_olive_oil_scores(
        product=product,
        parse_result=parse_result,
    )

    assert scores["quality"] == 100.0
    assert scores["price"] == 0.0
    assert scores["trust"] == 85.0
    assert scores["knowledge"] == 95.0


def test_scores_without_registry_match() -> None:
    product = {
        "product_name": "등록되지 않은 일반 상품",
    }

    parse_result = OliveOilParser().parse_product(
        product
    )

    scores = calculate_olive_oil_scores(
        product=product,
        parse_result=parse_result,
    )

    assert scores["quality"] == 0.0
    assert scores["price"] == 0.0
    assert scores["trust"] == 0.0
    assert scores["knowledge"] == 0.0


def test_scores_reject_invalid_product() -> None:
    parse_result = OliveOilParser().parse(
        "엑스트라 버진 올리브오일"
    )

    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        calculate_olive_oil_scores(
            product="invalid",  # type: ignore[arg-type]
            parse_result=parse_result,
        )


def test_scores_reject_wrong_parse_result() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "parse_result must be "
            "OliveOilParseResult"
        ),
    ):
        calculate_olive_oil_scores(
            product={
                "product_name": "올리브오일",
            },
            parse_result=object(),  # type: ignore[arg-type]
        )


def test_calculate_final_score() -> None:
    score = calculate_olive_oil_final_score(
        {
            "quality": 80,
            "price": 70,
            "trust": 90,
            "knowledge": 95,
        }
    )

    assert score == 87.5


def test_final_score_missing_external_values() -> None:
    score = calculate_olive_oil_final_score(
        {
            "knowledge": 95,
        }
    )

    assert score == 47.5


def test_final_score_custom_weights() -> None:
    score = calculate_olive_oil_final_score(
        {
            "quality": 80,
            "price": 70,
            "trust": 90,
            "knowledge": 95,
        },
        weights={
            "quality": 0.0,
            "price": 0.0,
            "trust": 0.0,
            "knowledge": 1.0,
        },
    )

    assert score == 95.0


def test_final_score_rejects_non_mapping() -> None:
    with pytest.raises(
        TypeError,
        match="scores must be a Mapping",
    ):
        calculate_olive_oil_final_score(
            [80, 70, 90]  # type: ignore[arg-type]
        )


def test_scoring_does_not_mutate_inputs() -> None:
    product = _complete_product()
    product_before = deepcopy(product)

    parse_result = OliveOilParser().parse_product(
        product
    )
    parse_result_before = parse_result.to_dict()

    calculate_olive_oil_scores(
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

    parse_result = OliveOilParser().parse_product(
        product
    )

    first = calculate_olive_oil_scores(
        product=product,
        parse_result=parse_result,
    )
    second = calculate_olive_oil_scores(
        product=product,
        parse_result=parse_result,
    )

    assert first == second
    assert first is not second

    assert (
        calculate_olive_oil_final_score(first)
        == calculate_olive_oil_final_score(second)
    )
