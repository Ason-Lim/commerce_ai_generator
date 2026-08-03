from __future__ import annotations

from copy import deepcopy

import pytest

from app.services.food.knowledge.cheese import (
    CheeseParser,
    apply_cheese_rules,
    build_cheese_attributes,
    calculate_cheese_scores,
    deduplicate_strings,
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
        "country_code": "FR",
        "texture": "soft cheese",
        "aging": "12개월 숙성",
        "storage_type": "냉장",
        "packaging_type": "wheel",
        "pasteurized": True,
        "certifications": [
            "AOP",
            "유기농",
        ],
        "rind_type": "bloomy rind",
        "quality_score": 80,
        "price_score": 70,
        "trust_score": 90,
    }


def _apply(
    product: dict[str, object],
) -> tuple[list[str], list[str]]:
    parse_result = (
        CheeseParser().parse_product(
            product
        )
    )

    attributes = build_cheese_attributes(
        product=product,
        parse_result=parse_result,
    )

    scores = calculate_cheese_scores(
        product=product,
        parse_result=parse_result,
    )

    return apply_cheese_rules(
        attributes=attributes,
        scores=scores,
        parse_result=parse_result,
    )


def test_complete_product_generates_reasons() -> None:
    reasons, warnings = _apply(
        _complete_product()
    )

    assert "치즈 종류는 브리입니다." in reasons
    assert "사용 원유는 산양유입니다." in reasons
    assert "원산지는 프랑스입니다." in reasons
    assert "치즈 질감은 연성입니다." in reasons
    assert "숙성 유형은 장기숙성입니다." in reasons
    assert "보관 상태는 냉장입니다." in reasons
    assert "상품 형태는 wheel입니다." in reasons
    assert (
        "원유 처리 표시는 "
        "pasteurized입니다."
        in reasons
    )
    assert (
        "외피 표시는 bloomy rind입니다."
        in reasons
    )
    assert (
        "표시된 인증 정보는 "
        "AOP, 유기농입니다."
        in reasons
    )

    assert warnings == []


def test_registry_guidance_is_included() -> None:
    reasons, _ = _apply(
        _complete_product()
    )

    assert any(
        reason.startswith(
            "Registry 기준 대표 활용 방식은 "
        )
        for reason in reasons
    )

    assert (
        "Registry에서 프리미엄 속성이 "
        "확인되었습니다."
        in reasons
    )


def test_high_knowledge_generates_reason() -> None:
    reasons, _ = _apply(
        _complete_product()
    )

    assert (
        "Cheese Knowledge 평가가 "
        "매우 높은 수준입니다."
        in reasons
    )


def test_partial_product_generates_warnings() -> None:
    reasons, warnings = _apply(
        {
            "product_name": (
                "24개월 숙성 "
                "파르미자노 레지아노"
            ),
        }
    )

    assert (
        "치즈 종류는 파르미자노 "
        "레지아노입니다."
        in reasons
    )
    assert (
        "숙성 유형은 초장기숙성입니다."
        in reasons
    )

    assert (
        "원유 종류 정보가 "
        "확인되지 않았습니다."
        in warnings
    )
    assert (
        "원산지 정보가 확인되지 않았습니다."
        in warnings
    )
    assert (
        "치즈 질감 정보가 "
        "확인되지 않았습니다."
        in warnings
    )


def test_unknown_product_generates_zero_score_warning() -> None:
    reasons, warnings = _apply(
        {
            "product_name": "일반 식품 상품",
        }
    )

    assert reasons == []

    assert (
        "치즈 Registry 기반 평가 점수를 "
        "계산할 수 없습니다."
        in warnings
    )

    assert (
        "치즈 도메인 분석에 필요한 정보가 "
        "충분하지 않습니다."
        in warnings
    )


def test_explicit_country_is_used_in_reason() -> None:
    reasons, _ = _apply(
        {
            "product_name": "프랑스 브리 치즈",
            "country": "France",
        }
    )

    assert "원산지는 France입니다." in reasons


def test_rules_preserve_parser_warnings() -> None:
    product = {
        "product_name": "플레인 크림치즈",
    }

    parse_result = (
        CheeseParser().parse_product(
            product
        )
    )

    attributes = build_cheese_attributes(
        product=product,
        parse_result=parse_result,
    )

    scores = calculate_cheese_scores(
        product=product,
        parse_result=parse_result,
    )

    _, warnings = apply_cheese_rules(
        attributes=attributes,
        scores=scores,
        parse_result=parse_result,
    )

    for warning in parse_result.warnings:
        assert warning in warnings


def test_rules_do_not_duplicate_warnings() -> None:
    _, warnings = _apply(
        {
            "product_name": "플레인 크림치즈",
        }
    )

    assert len(warnings) == len(set(warnings))


def test_rules_do_not_mutate_inputs() -> None:
    product = _complete_product()

    parse_result = (
        CheeseParser().parse_product(
            product
        )
    )

    attributes = build_cheese_attributes(
        product=product,
        parse_result=parse_result,
    )

    scores = calculate_cheese_scores(
        product=product,
        parse_result=parse_result,
    )

    attributes_before = deepcopy(attributes)
    scores_before = deepcopy(scores)
    parse_result_before = (
        parse_result.to_dict()
    )

    apply_cheese_rules(
        attributes=attributes,
        scores=scores,
        parse_result=parse_result,
    )

    assert attributes == attributes_before
    assert scores == scores_before
    assert (
        parse_result.to_dict()
        == parse_result_before
    )


def test_deduplicate_strings() -> None:
    assert deduplicate_strings(
        [
            "",
            "첫 번째",
            "두 번째",
            "첫 번째",
            "  세 번째  ",
            None,
        ]
    ) == [
        "첫 번째",
        "두 번째",
        "세 번째",
        "None",
    ]


def test_deduplicate_strings_accepts_generator() -> None:
    values = (
        value
        for value in [
            "A",
            "B",
            "A",
        ]
    )

    assert deduplicate_strings(
        values
    ) == [
        "A",
        "B",
    ]


def test_rules_reject_invalid_attributes() -> None:
    parse_result = CheeseParser().parse(
        "브리 치즈"
    )

    with pytest.raises(
        TypeError,
        match="attributes must be a Mapping",
    ):
        apply_cheese_rules(
            attributes=[],  # type: ignore[arg-type]
            scores={},
            parse_result=parse_result,
        )


def test_rules_reject_invalid_scores() -> None:
    parse_result = CheeseParser().parse(
        "브리 치즈"
    )

    with pytest.raises(
        TypeError,
        match="scores must be a Mapping",
    ):
        apply_cheese_rules(
            attributes={},
            scores=[],  # type: ignore[arg-type]
            parse_result=parse_result,
        )


def test_rules_reject_invalid_parse_result() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "parse_result must be "
            "CheeseParseResult"
        ),
    ):
        apply_cheese_rules(
            attributes={},
            scores={},
            parse_result=object(),  # type: ignore[arg-type]
        )


def test_rules_do_not_calculate_scores() -> None:
    parse_result = CheeseParser().parse(
        "브리 치즈"
    )

    reasons, warnings = apply_cheese_rules(
        attributes={
            "cheese_type": "브리",
        },
        scores={
            "knowledge": 50.0,
        },
        parse_result=parse_result,
    )

    assert reasons
    assert warnings
