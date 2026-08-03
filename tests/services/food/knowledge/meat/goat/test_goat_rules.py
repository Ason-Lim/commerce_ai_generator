from __future__ import annotations

from copy import deepcopy

import pytest

from app.services.food.knowledge.meat.goat import (
    GoatParser,
    apply_goat_rules,
    build_goat_attributes,
    calculate_goat_scores,
    deduplicate_strings,
)


def _analyze_rules(
    product: dict[str, object],
) -> tuple[list[str], list[str]]:
    parse_result = GoatParser().parse_product(
        product
    )

    attributes = build_goat_attributes(
        product=product,
        parse_result=parse_result,
    )

    scores = calculate_goat_scores(
        product=product,
        parse_result=parse_result,
    )

    return apply_goat_rules(
        attributes=attributes,
        scores=scores,
        parse_result=parse_result,
    )


def test_complete_product_generates_reasons() -> None:
    reasons, warnings = _analyze_rules(
        {
            "product_name": (
                "국내산 어린염소 보어 "
                "염소안심 500g"
            ),
            "goat_type": "어린 염소",
            "goat_breed": "Boer",
            "cut": "goat tenderloin",
            "country": "대한민국",
            "storage_type": "냉장",
            "certifications": ["HACCP"],
            "bone_status": "boneless",
            "skin_status": "skinless",
            "quality_score": 80,
            "price_score": 70,
            "trust_score": 90,
        }
    )

    assert (
        "염소고기 유형은 어린염소입니다."
        in reasons
    )
    assert "염소 품종은 보어입니다." in reasons
    assert "원산지는 대한민국입니다." in reasons
    assert "염소안심 부위 상품입니다." in reasons
    assert "보관 상태는 냉장입니다." in reasons
    assert (
        "표시된 인증 정보는 HACCP입니다."
        in reasons
    )
    assert (
        "뼈 상태 표시는 boneless입니다."
        in reasons
    )
    assert (
        "껍질 상태 표시는 skinless입니다."
        in reasons
    )
    assert warnings == []


def test_registry_guidance_is_included() -> None:
    reasons, _ = _analyze_rules(
        {
            "product_name": (
                "어린염소 보어 염소안심"
            ),
            "goat_type": "어린 염소",
            "goat_breed": "Boer",
            "cut": "goat tenderloin",
            "country": "대한민국",
        }
    )

    assert any(
        reason.startswith(
            "Registry 기준 권장 조리 방식은 "
        )
        for reason in reasons
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


def test_missing_origin_generates_warning() -> None:
    _, warnings = _analyze_rules(
        {
            "product_name": "염소안심",
        }
    )

    assert (
        "원산지 정보가 확인되지 않았습니다."
        in warnings
    )


def test_zero_knowledge_generates_warning() -> None:
    parse_result = GoatParser().parse(
        "일반 식품 상품"
    )

    reasons, warnings = apply_goat_rules(
        attributes={
            "country": "대한민국",
            "goat_type": None,
            "breed": None,
            "cut": None,
        },
        scores={
            "knowledge": 0.0,
        },
        parse_result=parse_result,
    )

    assert reasons == [
        "원산지는 대한민국입니다.",
    ]
    assert (
        "염소고기 Registry 기반 평가 점수를 "
        "계산할 수 없습니다."
        in warnings
    )


def test_rules_do_not_mutate_inputs() -> None:
    product = {
        "product_name": "염소안심",
    }

    parse_result = GoatParser().parse_product(
        product
    )
    attributes = build_goat_attributes(
        product=product,
        parse_result=parse_result,
    )
    scores = calculate_goat_scores(
        product=product,
        parse_result=parse_result,
    )

    attributes_before = deepcopy(attributes)
    scores_before = deepcopy(scores)
    warnings_before = list(
        parse_result.warnings
    )

    apply_goat_rules(
        attributes=attributes,
        scores=scores,
        parse_result=parse_result,
    )

    assert attributes == attributes_before
    assert scores == scores_before
    assert (
        parse_result.warnings
        == warnings_before
    )


def test_deduplicate_strings() -> None:
    assert deduplicate_strings(
        [
            "",
            "첫 번째",
            "두 번째",
            "첫 번째",
            "  세 번째  ",
        ]
    ) == [
        "첫 번째",
        "두 번째",
        "세 번째",
    ]


def test_rules_reject_invalid_inputs() -> None:
    parse_result = GoatParser().parse(
        "염소안심"
    )

    with pytest.raises(
        TypeError,
        match="attributes must be a Mapping",
    ):
        apply_goat_rules(
            attributes=[],  # type: ignore[arg-type]
            scores={},
            parse_result=parse_result,
        )

    with pytest.raises(
        TypeError,
        match="scores must be a Mapping",
    ):
        apply_goat_rules(
            attributes={},
            scores=[],  # type: ignore[arg-type]
            parse_result=parse_result,
        )

    with pytest.raises(
        TypeError,
        match=(
            "parse_result must be "
            "GoatParseResult"
        ),
    ):
        apply_goat_rules(
            attributes={},
            scores={},
            parse_result=object(),  # type: ignore[arg-type]
        )
