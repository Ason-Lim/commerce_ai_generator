from __future__ import annotations

import pytest

from app.services.food.knowledge.meat.goat import (
    GoatParser,
    calculate_available_average,
    calculate_goat_final_score,
    calculate_goat_knowledge_score,
    calculate_goat_scores,
    clamp_score,
    extract_registry_scores,
    safe_float,
)


def _complete_product() -> dict[str, object]:
    return {
        "product_name": (
            "국내산 어린염소 보어 "
            "염소안심 500g"
        ),
        "goat_type": "어린 염소",
        "goat_breed": "Boer",
        "cut": "goat tenderloin",
        "quality_score": 80,
        "price_score": 70,
        "trust_score": 90,
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
    assert (
        calculate_available_average(
            80,
            90,
            0,
            None,
        )
        == 85.0
    )

    assert calculate_available_average(
        0,
        None,
        "invalid",
    ) == 0.0


def test_extract_complete_registry_scores() -> None:
    parse_result = GoatParser().parse_product(
        _complete_product()
    )

    scores = extract_registry_scores(
        parse_result
    )

    assert scores["goat_type"] == 94.0
    assert scores["breed"] == 94.0
    assert scores["cut"] == 96.0

    assert scores["tenderness"] == 92.0
    assert scores["flavor"] == 88.0

    assert scores["growth"] == 96.0
    assert scores["rarity"] == 60.0
    assert scores["fat"] == 30.0
    assert scores["yield"] == 50.0


def test_extract_cut_only_registry_scores() -> None:
    parse_result = GoatParser().parse(
        "염소안심 500g"
    )

    scores = extract_registry_scores(
        parse_result
    )

    assert scores["goat_type"] == 0.0
    assert scores["breed"] == 0.0
    assert scores["cut"] == 96.0
    assert scores["tenderness"] == 96.0
    assert scores["flavor"] == 86.0
    assert scores["fat"] == 30.0
    assert scores["yield"] == 50.0


def test_extract_unknown_registry_scores() -> None:
    parse_result = GoatParser().parse(
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
        match="parse_result must be GoatParseResult",
    ):
        extract_registry_scores(
            object()  # type: ignore[arg-type]
        )


def test_calculate_complete_knowledge_score() -> None:
    score = calculate_goat_knowledge_score(
        goat_type_score=94,
        breed_score=94,
        cut_score=96,
    )

    # 94 × 0.30 + 94 × 0.20 + 96 × 0.50
    assert score == 95.0


def test_calculate_knowledge_score_uses_available_fields() -> None:
    assert calculate_goat_knowledge_score(
        goat_type_score=0,
        breed_score=0,
        cut_score=96,
    ) == 96.0

    assert calculate_goat_knowledge_score(
        goat_type_score=94,
        breed_score=0,
        cut_score=96,
    ) == 95.25

    assert calculate_goat_knowledge_score(
        goat_type_score=0,
        breed_score=0,
        cut_score=0,
    ) == 0.0


def test_calculate_goat_scores() -> None:
    product = _complete_product()

    parse_result = GoatParser().parse_product(
        product
    )

    scores = calculate_goat_scores(
        product=product,
        parse_result=parse_result,
    )

    assert scores["quality"] == 80.0
    assert scores["price"] == 70.0
    assert scores["trust"] == 90.0

    assert scores["goat_type"] == 94.0
    assert scores["breed"] == 94.0
    assert scores["cut"] == 96.0
    assert scores["knowledge"] == 95.0

    assert scores["tenderness"] == 92.0
    assert scores["flavor"] == 88.0


def test_calculate_goat_scores_clamps_external_scores() -> None:
    product = {
        "product_name": "염소안심",
        "quality_score": 150,
        "price_score": -20,
        "trust_score": "85",
    }

    parse_result = GoatParser().parse_product(
        product
    )

    scores = calculate_goat_scores(
        product=product,
        parse_result=parse_result,
    )

    assert scores["quality"] == 100.0
    assert scores["price"] == 0.0
    assert scores["trust"] == 85.0
    assert scores["knowledge"] == 96.0


def test_calculate_goat_scores_rejects_non_mapping() -> None:
    parse_result = GoatParser().parse(
        "염소안심"
    )

    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        calculate_goat_scores(
            product="염소안심",  # type: ignore[arg-type]
            parse_result=parse_result,
        )


def test_calculate_goat_scores_rejects_wrong_parse_result() -> None:
    with pytest.raises(
        TypeError,
        match="parse_result must be GoatParseResult",
    ):
        calculate_goat_scores(
            product={
                "product_name": "염소안심"
            },
            parse_result=object(),  # type: ignore[arg-type]
        )


def test_calculate_goat_final_score() -> None:
    final_score = calculate_goat_final_score(
        {
            "quality": 80,
            "price": 70,
            "trust": 90,
            "knowledge": 95,
        }
    )

    # 80×0.20 + 70×0.15 + 90×0.15 + 95×0.50
    assert final_score == 87.5


def test_calculate_goat_final_score_missing_values() -> None:
    final_score = calculate_goat_final_score(
        {
            "knowledge": 96,
        }
    )

    assert final_score == 48.0


def test_calculate_goat_final_score_custom_weights() -> None:
    final_score = calculate_goat_final_score(
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

    assert final_score == 95.0


def test_calculate_goat_final_score_rejects_non_mapping() -> None:
    with pytest.raises(
        TypeError,
        match="scores must be a Mapping",
    ):
        calculate_goat_final_score(
            [80, 70, 90]  # type: ignore[arg-type]
        )


def test_scoring_is_deterministic() -> None:
    product = _complete_product()
    parse_result = GoatParser().parse_product(
        product
    )

    first = calculate_goat_scores(
        product=product,
        parse_result=parse_result,
    )

    second = calculate_goat_scores(
        product=product,
        parse_result=parse_result,
    )

    assert first == second
    assert first is not second
