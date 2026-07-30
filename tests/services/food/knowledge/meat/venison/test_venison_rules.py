from __future__ import annotations

from copy import deepcopy

import pytest

from app.services.food.knowledge.meat.venison import (
    VenisonParser,
    apply_venison_rules,
    build_venison_attributes,
    calculate_venison_scores,
    deduplicate_strings,
)
from app.services.food.knowledge.meat.venison.parser_models import (
    VenisonParseResult,
)


def _analyze_rules(
    product: dict[str, object],
) -> tuple[list[str], list[str]]:
    parse_result = (
        VenisonParser().parse_product(product)
    )

    attributes = build_venison_attributes(
        product=product,
        parse_result=parse_result,
    )

    scores = calculate_venison_scores(
        product=product,
        parse_result=parse_result,
    )

    return apply_venison_rules(
        attributes=attributes,
        scores=scores,
        parse_result=parse_result,
    )


def test_complete_product_generates_reasons() -> None:
    reasons, warnings = _analyze_rules(
        {
            "product_name": (
                "뉴질랜드산 어린사슴 "
                "레드디어 사슴가슴살 500g"
            ),
            "venison_type": "어린 사슴",
            "deer_species": "Red Deer",
            "cut": "사슴 가슴살",
            "country": "뉴질랜드",
            "country_code": "NZ",
            "weight": "500g",
            "storage_type": "냉동",
            "certifications": [
                "HACCP",
            ],
            "bone_status": "boneless",
            "skin_status": "skinless",
            "quality_score": 80,
            "price_score": 70,
            "trust_score": 90,
        }
    )

    assert (
        "사슴고기 유형은 어린사슴입니다."
        in reasons
    )
    assert (
        "사슴 품종 또는 종은 레드디어입니다."
        in reasons
    )
    assert (
        "원산지는 뉴질랜드입니다."
        in reasons
    )
    assert (
        "사슴가슴살 부위 상품입니다."
        in reasons
    )
    assert (
        "보관 상태는 냉동입니다."
        in reasons
    )
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
                "뉴질랜드산 어린사슴 "
                "레드디어 사슴가슴살"
            ),
            "venison_type": "어린 사슴",
            "deer_species": "Red Deer",
            "cut": "사슴가슴살",
            "country": "뉴질랜드",
            "quality_score": 80,
            "price_score": 70,
            "trust_score": 90,
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
        "사슴고기 유형 Registry 기준 평가가 "
        "높은 유형입니다."
        in reasons
    )

    assert (
        "품종 Registry 기준 평가가 "
        "높은 품종 또는 종입니다."
        in reasons
    )

    assert (
        "Registry에서 프리미엄 속성이 "
        "확인되었습니다."
        in reasons
    )


def test_breast_contract_generates_cut_reason() -> None:
    reasons, warnings = _analyze_rules(
        {
            "product_name": "사슴가슴살",
            "cut": "venison breast",
            "country": "뉴질랜드",
        }
    )

    assert (
        "사슴가슴살 부위 상품입니다."
        in reasons
    )

    assert any(
        reason.startswith(
            "Registry 기준 권장 조리 방식은 "
        )
        for reason in reasons
    )

    assert (
        "사슴고기 유형, 품종, 부위 정보가 "
        "모두 확인되지 않았습니다."
        in warnings
    )

    assert not any(
        "평가 점수를 계산할 수 없습니다"
        in warning
        for warning in warnings
    )


def test_missing_origin_generates_warning() -> None:
    _, warnings = _analyze_rules(
        {
            "product_name": "사슴가슴살",
        }
    )

    assert (
        "원산지 정보가 확인되지 않았습니다."
        in warnings
    )


def test_incomplete_parse_generates_warning() -> None:
    _, warnings = _analyze_rules(
        {
            "product_name": "사슴가슴살",
            "country": "뉴질랜드",
        }
    )

    assert (
        "사슴고기 유형, 품종, 부위 정보가 "
        "모두 확인되지 않았습니다."
        in warnings
    )


def test_zero_knowledge_generates_warning() -> None:
    parse_result = VenisonParser().parse(
        "일반 식품 상품"
    )

    reasons, warnings = apply_venison_rules(
        attributes={
            "country": "대한민국",
            "venison_type": None,
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
        "사슴고기 Registry 기반 평가 점수를 "
        "계산할 수 없습니다."
        in warnings
    )


def test_parser_warnings_are_preserved() -> None:
    parse_result = VenisonParser().parse(
        "사슴가슴살"
    )

    assert parse_result.warnings

    _, warnings = apply_venison_rules(
        attributes={
            "country": None,
            "venison_type": None,
            "breed": None,
            "cut": "사슴가슴살",
        },
        scores={
            "knowledge": 83.0,
            "cut": 83.0,
        },
        parse_result=parse_result,
    )

    for warning in parse_result.warnings:
        assert warning in warnings


def test_rules_do_not_mutate_inputs() -> None:
    product = {
        "product_name": "사슴가슴살",
        "cut": "사슴가슴살",
    }

    parse_result = (
        VenisonParser().parse_product(product)
    )

    attributes = build_venison_attributes(
        product=product,
        parse_result=parse_result,
    )

    scores = calculate_venison_scores(
        product=product,
        parse_result=parse_result,
    )

    attributes_before = deepcopy(attributes)
    scores_before = deepcopy(scores)
    warnings_before = list(
        parse_result.warnings
    )

    apply_venison_rules(
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


def test_deduplicate_strings_preserves_order() -> None:
    assert deduplicate_strings(
        [
            "",
            "첫 번째",
            "두 번째",
            "첫 번째",
            "  세 번째  ",
            "두 번째",
        ]
    ) == [
        "첫 번째",
        "두 번째",
        "세 번째",
    ]


def test_rules_reject_invalid_attributes() -> None:
    parse_result = VenisonParser().parse(
        "사슴가슴살"
    )

    with pytest.raises(
        TypeError,
        match="attributes must be a Mapping",
    ):
        apply_venison_rules(
            attributes=[],  # type: ignore[arg-type]
            scores={},
            parse_result=parse_result,
        )


def test_rules_reject_invalid_scores() -> None:
    parse_result = VenisonParser().parse(
        "사슴가슴살"
    )

    with pytest.raises(
        TypeError,
        match="scores must be a Mapping",
    ):
        apply_venison_rules(
            attributes={},
            scores=[],  # type: ignore[arg-type]
            parse_result=parse_result,
        )


def test_rules_reject_invalid_parse_result() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "parse_result must be "
            "VenisonParseResult"
        ),
    ):
        apply_venison_rules(
            attributes={},
            scores={},
            parse_result=object(),  # type: ignore[arg-type]
        )


def test_rules_return_string_lists() -> None:
    parse_result = VenisonParseResult(
        original_text="사슴가슴살",
        normalized_text="사슴가슴살",
    )

    reasons, warnings = apply_venison_rules(
        attributes={},
        scores={},
        parse_result=parse_result,
    )

    assert isinstance(reasons, list)
    assert isinstance(warnings, list)
    assert all(
        isinstance(item, str)
        for item in reasons
    )
    assert all(
        isinstance(item, str)
        for item in warnings
    )
