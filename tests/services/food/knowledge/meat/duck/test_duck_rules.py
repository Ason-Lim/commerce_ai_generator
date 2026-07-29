from __future__ import annotations

import pytest

from app.services.food.knowledge.meat.duck.attributes import (
    build_duck_attributes,
)
from app.services.food.knowledge.meat.duck.parser import (
    DuckParser,
)
from app.services.food.knowledge.meat.duck.rules import (
    apply_duck_rules,
    deduplicate_strings,
)
from app.services.food.knowledge.meat.duck.scoring import (
    calculate_duck_scores,
)


def _analyze_rules(
    product: dict[str, object],
) -> tuple[list[str], list[str]]:
    parse_result = DuckParser().parse_product(
        product
    )
    attributes = build_duck_attributes(
        product=product,
        parse_result=parse_result,
    )
    scores = calculate_duck_scores(
        product=product,
        parse_result=parse_result,
    )

    return apply_duck_rules(
        attributes=attributes,
        scores=scores,
        parse_result=parse_result,
    )


def test_complete_product_generates_reasons() -> None:
    reasons, warnings = _analyze_rules(
        {
            "product_name": (
                "국내산 훈제오리 체리밸리 "
                "오리가슴살 500g"
            ),
            "country": "대한민국",
            "storage_type": "냉장",
            "certifications": [
                "무항생제",
                "HACCP",
            ],
            "bone_status": "boneless",
            "skin_status": "skinless",
        }
    )

    assert "오리 유형은 훈제오리입니다." in reasons
    assert (
        "품종 또는 상업 계통은 "
        "체리밸리입니다."
        in reasons
    )
    assert "원산지는 대한민국입니다." in reasons
    assert "오리가슴살 부위 상품입니다." in reasons
    assert (
        "보관 상태는 냉장입니다."
        in reasons
    )
    assert (
        "표시된 인증 정보는 "
        "무항생제, HACCP입니다."
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


def test_complete_product_includes_registry_guidance() -> None:
    reasons, _ = _analyze_rules(
        {
            "product_name": (
                "국내산 훈제오리 체리밸리 "
                "오리가슴살"
            ),
            "country": "대한민국",
        }
    )

    assert any(
        reason.startswith(
            "Registry 기준 권장 조리 방식은 "
        )
        for reason in reasons
    )

    assert (
        "품종 Registry 기준 평가가 "
        "높은 품종 또는 계통입니다."
        in reasons
    )
    assert (
        "상품성이 높은 부위로 "
        "분류됩니다."
        in reasons
    )
    assert (
        "품종과 부위 기준 부드러운 식감을 "
        "기대할 수 있습니다."
        in reasons
    )
    assert (
        "품종과 부위 기준 풍미 평가가 "
        "높은 상품입니다."
        in reasons
    )
    assert (
        "Registry에서 프리미엄 속성이 "
        "확인되었습니다."
        in reasons
    )


def test_missing_origin_generates_warning() -> None:
    _, warnings = _analyze_rules(
        {
            "product_name": "오리가슴살",
        }
    )

    assert (
        "원산지 정보가 확인되지 않았습니다."
        in warnings
    )


def test_incomplete_parse_generates_warning() -> None:
    _, warnings = _analyze_rules(
        {
            "product_name": "오리가슴살",
            "country": "대한민국",
        }
    )

    assert (
        "오리 유형, 품종, 부위 정보가 "
        "모두 확인되지 않았습니다."
        in warnings
    )


def test_zero_knowledge_generates_warning() -> None:
    parse_result = DuckParser().parse(
        "일반 식품 상품"
    )

    attributes = {
        "country": "대한민국",
        "duck_type": None,
        "breed": None,
        "cut": None,
    }
    scores = {
        "knowledge": 0.0,
    }

    _, warnings = apply_duck_rules(
        attributes=attributes,
        scores=scores,
        parse_result=parse_result,
    )

    assert (
        "오리고기 Registry 기반 평가 점수를 "
        "계산할 수 없습니다."
        in warnings
    )


def test_parser_warnings_are_preserved() -> None:
    parse_result = DuckParser().parse_product(
        {
            "product_name": "오리가슴살",
        }
    )

    reasons, warnings = apply_duck_rules(
        attributes={
            "country": None,
            "duck_type": None,
            "breed": None,
            "cut": "오리가슴살",
        },
        scores={
            "knowledge": 90.0,
            "cut": 90.0,
        },
        parse_result=parse_result,
    )

    assert reasons == [
        "오리가슴살 부위 상품입니다.",
        "상품성이 높은 부위로 분류됩니다.",
    ]

    for warning in parse_result.warnings:
        assert warning in warnings


def test_rules_do_not_mutate_inputs() -> None:
    parse_result = DuckParser().parse_product(
        {
            "product_name": "오리가슴살",
        }
    )

    attributes = {
        "country": None,
        "duck_type": None,
        "breed": None,
        "cut": "오리가슴살",
        "certifications": [],
    }
    scores = {
        "knowledge": 90.0,
        "cut": 90.0,
    }

    original_attributes = dict(attributes)
    original_scores = dict(scores)

    apply_duck_rules(
        attributes=attributes,
        scores=scores,
        parse_result=parse_result,
    )

    assert attributes == original_attributes
    assert scores == original_scores


def test_deduplicate_strings_preserves_order() -> None:
    assert deduplicate_strings(
        [
            "첫 번째",
            "",
            "두 번째",
            "첫 번째",
            " 두 번째 ",
            "세 번째",
        ]
    ) == [
        "첫 번째",
        "두 번째",
        "세 번째",
    ]


def test_rules_reject_invalid_attributes() -> None:
    parse_result = DuckParser().parse(
        "오리가슴살"
    )

    with pytest.raises(
        TypeError,
        match="attributes must be a Mapping",
    ):
        apply_duck_rules(
            attributes=[],  # type: ignore[arg-type]
            scores={},
            parse_result=parse_result,
        )


def test_rules_reject_invalid_scores() -> None:
    parse_result = DuckParser().parse(
        "오리가슴살"
    )

    with pytest.raises(
        TypeError,
        match="scores must be a Mapping",
    ):
        apply_duck_rules(
            attributes={},
            scores=[],  # type: ignore[arg-type]
            parse_result=parse_result,
        )


def test_rules_reject_invalid_parse_result() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "parse_result must be "
            "DuckParseResult"
        ),
    ):
        apply_duck_rules(
            attributes={},
            scores={},
            parse_result=object(),  # type: ignore[arg-type]
        )
