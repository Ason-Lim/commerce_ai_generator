from __future__ import annotations

import pytest

from app.services.food.knowledge.meat.chicken.attributes import (
    build_chicken_attributes,
)
from app.services.food.knowledge.meat.chicken.parser import (
    ChickenParser,
)
from app.services.food.knowledge.meat.chicken.rules import (
    apply_chicken_rules,
    deduplicate_strings,
)
from app.services.food.knowledge.meat.chicken.scoring import (
    calculate_chicken_scores,
)


def _analyze_rules(
    product: dict[str, object],
) -> tuple[list[str], list[str]]:
    parse_result = ChickenParser().parse_product(
        product
    )
    attributes = build_chicken_attributes(
        product=product,
        parse_result=parse_result,
    )
    scores = calculate_chicken_scores(
        product=product,
        parse_result=parse_result,
    )

    return apply_chicken_rules(
        attributes=attributes,
        scores=scores,
        parse_result=parse_result,
    )


def test_complete_product_generates_reasons() -> None:
    reasons, warnings = _analyze_rules(
        {
            "product_name": (
                "국내산 토종닭 Ross 308 "
                "닭다리살 500g"
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

    assert "닭 유형은 토종닭입니다." in reasons
    assert "품종은 로스 308입니다." in reasons
    assert "원산지는 대한민국입니다." in reasons
    assert "닭다리살 부위 상품입니다." in reasons
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
                "국내산 토종닭 Ross 308 "
                "닭다리살"
            ),
            "country": "대한민국",
        }
    )

    assert (
        "Registry 기준 권장 조리 방식은 "
        "grilling, frying, braising, "
        "roasting입니다."
        in reasons
    )
    assert (
        "Registry 기준 대표 활용 방식은 "
        "soup, braising, boiling입니다."
        in reasons
    )
    assert (
        "닭 유형 Registry 기준 상품성이 "
        "높은 유형입니다."
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


def test_missing_origin_generates_warning() -> None:
    _, warnings = _analyze_rules(
        {
            "product_name": "닭가슴살",
        }
    )

    assert (
        "원산지 정보가 확인되지 않았습니다."
        in warnings
    )


def test_incomplete_parse_generates_warning() -> None:
    _, warnings = _analyze_rules(
        {
            "product_name": "닭가슴살",
            "country": "대한민국",
        }
    )

    assert (
        "닭 유형, 품종, 부위 정보가 "
        "모두 확인되지 않았습니다."
        in warnings
    )


def test_zero_knowledge_generates_warning() -> None:
    parse_result = ChickenParser().parse(
        "일반 식품 상품"
    )

    attributes = {
        "country": "대한민국",
        "chicken_type": None,
        "breed": None,
        "cut": None,
    }
    scores = {
        "knowledge": 0.0,
    }

    _, warnings = apply_chicken_rules(
        attributes=attributes,
        scores=scores,
        parse_result=parse_result,
    )

    assert (
        "닭고기 Registry 기반 평가 점수를 "
        "계산할 수 없습니다."
        in warnings
    )


def test_parser_warnings_are_preserved() -> None:
    parse_result = ChickenParser().parse_product(
        {
            "product_name": "닭가슴살",
        }
    )

    reasons, warnings = apply_chicken_rules(
        attributes={
            "country": None,
            "chicken_type": None,
            "breed": None,
            "cut": "닭가슴살",
        },
        scores={
            "knowledge": 82.0,
            "cut": 82.0,
        },
        parse_result=parse_result,
    )

    assert reasons == [
        "닭가슴살 부위 상품입니다.",
    ]
    for warning in parse_result.warnings:
        assert warning in warnings


def test_rules_do_not_mutate_inputs() -> None:
    parse_result = ChickenParser().parse_product(
        {
            "product_name": "닭가슴살",
        }
    )

    attributes = {
        "country": None,
        "chicken_type": None,
        "breed": None,
        "cut": "닭가슴살",
        "certifications": [],
    }
    scores = {
        "knowledge": 82.0,
        "cut": 82.0,
    }

    original_attributes = dict(attributes)
    original_scores = dict(scores)

    apply_chicken_rules(
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
    parse_result = ChickenParser().parse(
        "닭가슴살"
    )

    with pytest.raises(
        TypeError,
        match="attributes must be a Mapping",
    ):
        apply_chicken_rules(
            attributes=[],  # type: ignore[arg-type]
            scores={},
            parse_result=parse_result,
        )


def test_rules_reject_invalid_scores() -> None:
    parse_result = ChickenParser().parse(
        "닭가슴살"
    )

    with pytest.raises(
        TypeError,
        match="scores must be a Mapping",
    ):
        apply_chicken_rules(
            attributes={},
            scores=[],  # type: ignore[arg-type]
            parse_result=parse_result,
        )


def test_rules_reject_invalid_parse_result() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "parse_result must be "
            "ChickenParseResult"
        ),
    ):
        apply_chicken_rules(
            attributes={},
            scores={},
            parse_result=object(),  # type: ignore[arg-type]
        )
