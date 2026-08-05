from __future__ import annotations

from copy import deepcopy

import pytest

from app.services.food.knowledge.tea.parser import (
    TeaParser,
)
from app.services.food.knowledge.tea.scoring import (
    TEA_FINAL_SCORE_WEIGHTS,
    TEA_KNOWLEDGE_WEIGHTS,
    calculate_available_average,
    calculate_available_weighted_score,
    calculate_tea_final_score,
    calculate_tea_knowledge_score,
    calculate_tea_scores,
    clamp_score,
    extract_registry_scores,
    safe_float,
)


def _complete_product() -> dict[str, object]:
    return {
        "product_name": (
            "제주 야부키타 증제 "
            "비산화 감칠맛 녹차"
        ),
        "tea_type": "green tea",
        "origin": "Jeju",
        "cultivar": "Yabukita",
        "processing_method": "steamed tea",
        "oxidation_level": "unoxidized",
        "flavor_notes": "umami",
        "quality_score": 80,
        "price_score": 70,
        "trust_score": 90,
    }


def test_default_scoring_weights() -> None:
    assert set(
        TEA_KNOWLEDGE_WEIGHTS
    ) == {
        "tea_type",
        "origin",
        "variety",
        "processing",
        "oxidation",
        "flavor",
    }

    assert round(
        sum(
            TEA_KNOWLEDGE_WEIGHTS.values()
        ),
        10,
    ) == 1.0

    assert TEA_FINAL_SCORE_WEIGHTS == {
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
    parse_result = TeaParser().parse_product(
        _complete_product()
    )

    scores = extract_registry_scores(
        parse_result
    )

    assert scores == {
        "tea_type": 0.0,
        "origin": 0.0,
        "variety": 0.0,
        "processing": 0.0,
        "oxidation": 0.0,
        "flavor": 0.0,
    }


def test_extract_partial_registry_scores() -> None:
    parse_result = TeaParser().parse(
        "다즐링 꽃향 차"
    )

    scores = extract_registry_scores(
        parse_result
    )

    assert scores["origin"] == 0.0
    assert scores["flavor"] == 0.0
    assert scores["tea_type"] == 0.0
    assert scores["variety"] == 0.0


def test_extract_unknown_registry_scores() -> None:
    parse_result = TeaParser().parse(
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
            "TeaParseResult"
        ),
    ):
        extract_registry_scores(
            object()  # type: ignore[arg-type]
        )


def test_calculate_complete_knowledge_score() -> None:
    score = calculate_tea_knowledge_score(
        tea_type_score=90,
        origin_score=80,
        variety_score=70,
        processing_score=100,
        oxidation_score=80,
        flavor_score=90,
    )

    assert score == 85.0


def test_knowledge_score_uses_available_fields() -> None:
    score = calculate_tea_knowledge_score(
        origin_score=80,
        processing_score=100,
    )

    assert score == 90.0

    assert calculate_tea_knowledge_score() == 0.0


def test_knowledge_score_custom_weights() -> None:
    score = calculate_tea_knowledge_score(
        tea_type_score=80,
        flavor_score=100,
        weights={
            "tea_type": 0.0,
            "flavor": 1.0,
        },
    )

    assert score == 100.0


def test_calculate_tea_scores() -> None:
    product = _complete_product()

    parse_result = TeaParser().parse_product(
        product
    )

    scores = calculate_tea_scores(
        product=product,
        parse_result=parse_result,
    )

    assert scores["quality"] == 80.0
    assert scores["price"] == 70.0
    assert scores["trust"] == 90.0

    # 현재 Tea Registry YAML의 score는 모두 0이다.
    assert scores["knowledge"] == 0.0

    assert scores["tea_type"] == 0.0
    assert scores["origin"] == 0.0
    assert scores["variety"] == 0.0
    assert scores["processing"] == 0.0
    assert scores["oxidation"] == 0.0
    assert scores["flavor"] == 0.0


def test_calculate_tea_scores_clamps_external_scores() -> None:
    product = {
        "product_name": "녹차",
        "quality_score": 150,
        "price_score": -20,
        "trust_score": "85",
    }

    parse_result = TeaParser().parse_product(
        product
    )

    scores = calculate_tea_scores(
        product=product,
        parse_result=parse_result,
    )

    assert scores["quality"] == 100.0
    assert scores["price"] == 0.0
    assert scores["trust"] == 85.0
    assert scores["knowledge"] == 0.0


def test_calculate_tea_scores_rejects_invalid_product() -> None:
    parse_result = TeaParser().parse(
        "녹차"
    )

    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        calculate_tea_scores(
            product="녹차",  # type: ignore[arg-type]
            parse_result=parse_result,
        )


def test_calculate_tea_scores_rejects_wrong_parse_result() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "parse_result must be "
            "TeaParseResult"
        ),
    ):
        calculate_tea_scores(
            product={
                "product_name": "녹차",
            },
            parse_result=object(),  # type: ignore[arg-type]
        )


def test_calculate_tea_final_score() -> None:
    score = calculate_tea_final_score(
        {
            "quality": 80,
            "price": 70,
            "trust": 90,
            "knowledge": 85,
        }
    )

    assert score == 82.5


def test_final_score_missing_external_values() -> None:
    score = calculate_tea_final_score(
        {
            "knowledge": 90,
        }
    )

    assert score == 45.0


def test_final_score_custom_weights() -> None:
    score = calculate_tea_final_score(
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


def test_final_score_rejects_non_mapping() -> None:
    with pytest.raises(
        TypeError,
        match="scores must be a Mapping",
    ):
        calculate_tea_final_score(
            [80, 70, 90]  # type: ignore[arg-type]
        )


def test_scoring_does_not_mutate_inputs() -> None:
    product = _complete_product()
    product_before = deepcopy(product)

    parse_result = TeaParser().parse_product(
        product
    )
    parse_result_before = (
        parse_result.to_dict()
    )

    calculate_tea_scores(
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

    parse_result = TeaParser().parse_product(
        product
    )

    first = calculate_tea_scores(
        product=product,
        parse_result=parse_result,
    )
    second = calculate_tea_scores(
        product=product,
        parse_result=parse_result,
    )

    assert first == second
    assert first is not second
