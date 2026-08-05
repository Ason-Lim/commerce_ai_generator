from __future__ import annotations

from copy import deepcopy

import pytest

from app.services.food.knowledge.tea.attributes import (
    build_tea_attributes,
)
from app.services.food.knowledge.tea.parser import (
    TeaParser,
)
from app.services.food.knowledge.tea.rules import (
    apply_tea_rules,
    deduplicate_strings,
)
from app.services.food.knowledge.tea.scoring import (
    calculate_tea_scores,
)


def _complete_product() -> dict[str, object]:
    return {
        "product_name": (
            "제주 야부키타 증제 "
            "비산화 감칠맛 녹차"
        ),
        "tea_type": "green tea",
        "origin": "Jeju",
        "country": "South Korea",
        "country_code": "KR",
        "cultivar": "Yabukita",
        "processing_method": "steamed tea",
        "oxidation_level": "unoxidized",
        "flavor_notes": [
            "감칠맛",
            "풀향",
        ],
        "weight": "100g",
        "packaging_type": "loose leaf",
        "harvest_year": 2026,
        "grade": "premium",
        "leaf_style": "whole leaf",
        "caffeine_status": "regular",
        "certifications": [
            "Organic",
            "HACCP",
        ],
        "quality_score": 80,
        "price_score": 70,
        "trust_score": 90,
    }


def _apply(
    product: dict[str, object],
) -> tuple[list[str], list[str]]:
    parse_result = TeaParser().parse_product(
        product
    )

    attributes = build_tea_attributes(
        product=product,
        parse_result=parse_result,
    )

    scores = calculate_tea_scores(
        product=product,
        parse_result=parse_result,
    )

    return apply_tea_rules(
        attributes=attributes,
        scores=scores,
        parse_result=parse_result,
    )


def test_complete_product_generates_reasons() -> None:
    reasons, warnings = _apply(
        _complete_product()
    )

    assert (
        "차 종류, 산지, 품종, 가공 방식, "
        "산화도, 향미 정보가 모두 확인되었습니다."
        in reasons
    )
    assert "차 종류는 green입니다." in reasons
    assert "원산지는 South Korea입니다." in reasons
    assert "차 품종은 yabukita입니다." in reasons
    assert "가공 방식은 steamed입니다." in reasons
    assert "산화 단계는 unoxidized입니다." in reasons
    assert "대표 향미는 umami입니다." in reasons

    assert "표시 중량은 100g입니다." in reasons
    assert (
        "상품 형태는 loose leaf입니다."
        in reasons
    )
    assert "수확 연도 표시는 2026입니다." in reasons
    assert "표시 등급은 premium입니다." in reasons
    assert "잎 형태는 whole leaf입니다." in reasons

    assert (
        "일반 카페인 상품으로 "
        "표시되어 있습니다."
        in reasons
    )
    assert (
        "표시된 인증 정보는 "
        "Organic, HACCP입니다."
        in reasons
    )
    assert (
        "표시된 향미 노트는 "
        "감칠맛, 풀향입니다."
        in reasons
    )

    assert (
        "Tea 품질 평가가 우수합니다."
        in reasons
    )
    assert (
        "구조화된 상품 정보의 신뢰도 평가가 "
        "충분합니다."
        in reasons
    )

    assert (
        "Tea Registry 기반 평가 점수가 "
        "아직 설정되지 않았거나 "
        "계산할 수 없습니다."
        in warnings
    )


def test_registry_characteristics_are_included() -> None:
    reasons, _ = _apply(
        _complete_product()
    )

    assert (
        "열 고정 가공 특성이 확인되었습니다."
        in reasons
    )
    assert (
        "맛 중심의 감각 특성이 확인되었습니다."
        in reasons
    )


def test_partial_product_generates_reasons_and_warnings() -> None:
    reasons, warnings = _apply(
        {
            "product_name": (
                "다즐링 꽃향 차 100g"
            ),
            "weight": "100g",
        }
    )

    assert (
        "Tea 분석에 활용할 수 있는 "
        "핵심 정보가 확인되었습니다."
        in reasons
    )
    assert "원산지는 India입니다." in reasons
    assert "대표 향미는 floral입니다." in reasons
    assert "표시 중량은 100g입니다." in reasons

    assert (
        "차 종류 정보가 확인되지 않았습니다."
        in warnings
    )
    assert (
        "차 품종 정보가 확인되지 않았습니다."
        in warnings
    )
    assert (
        "차 가공 방식 정보가 "
        "확인되지 않았습니다."
        in warnings
    )
    assert (
        "차 산화도 정보가 확인되지 않았습니다."
        in warnings
    )


def test_unknown_product_generates_warnings() -> None:
    reasons, warnings = _apply(
        {
            "product_name": "일반 식품 상품",
        }
    )

    assert reasons == []

    assert (
        "Tea 도메인 분석에 필요한 정보가 "
        "충분하지 않습니다."
        in warnings
    )
    assert (
        "Tea Registry 기반 평가 점수가 "
        "아직 설정되지 않았거나 "
        "계산할 수 없습니다."
        in warnings
    )


def test_explicit_country_is_used() -> None:
    reasons, _ = _apply(
        {
            "product_name": "제주 녹차",
            "country": "Republic of Korea",
        }
    )

    assert (
        "원산지는 Republic of Korea입니다."
        in reasons
    )


@pytest.mark.parametrize(
    (
        "status",
        "expected_reason",
    ),
    [
        (
            "decaf",
            "디카페인 상품으로 표시되어 있습니다.",
        ),
        (
            "regular",
            "일반 카페인 상품으로 표시되어 있습니다.",
        ),
        (
            "low caffeine",
            "카페인 관련 표시는 low caffeine입니다.",
        ),
    ],
)
def test_caffeine_status_reasons(
    status: str,
    expected_reason: str,
) -> None:
    reasons, _ = _apply(
        {
            "product_name": "녹차",
            "caffeine_status": status,
        }
    )

    assert expected_reason in reasons


def test_high_knowledge_score_reason() -> None:
    parse_result = TeaParser().parse(
        "녹차"
    )

    reasons, _ = apply_tea_rules(
        attributes={
            "tea_type": "green",
        },
        scores={
            "knowledge": 95.0,
        },
        parse_result=parse_result,
    )

    assert (
        "Tea Knowledge 평가가 "
        "매우 높은 수준입니다."
        in reasons
    )


def test_low_quality_and_trust_warnings() -> None:
    parse_result = TeaParser().parse(
        "녹차"
    )

    _, warnings = apply_tea_rules(
        attributes={
            "tea_type": "green",
        },
        scores={
            "quality": 40.0,
            "trust": 30.0,
            "knowledge": 50.0,
        },
        parse_result=parse_result,
    )

    assert (
        "Tea 품질 평가 점수가 낮습니다."
        in warnings
    )
    assert (
        "상품 정보의 신뢰도 평가가 낮습니다."
        in warnings
    )


def test_invalid_harvest_year_warning() -> None:
    parse_result = TeaParser().parse(
        "녹차"
    )

    _, warnings = apply_tea_rules(
        attributes={
            "tea_type": "green",
            "harvest_year": "unknown",
        },
        scores={
            "knowledge": 50.0,
        },
        parse_result=parse_result,
    )

    assert (
        "수확 연도 값이 올바른 "
        "연도 형식이 아닙니다."
        in warnings
    )


def test_out_of_range_harvest_year_warning() -> None:
    parse_result = TeaParser().parse(
        "녹차"
    )

    _, warnings = apply_tea_rules(
        attributes={
            "tea_type": "green",
            "harvest_year": 1500,
        },
        scores={
            "knowledge": 50.0,
        },
        parse_result=parse_result,
    )

    assert (
        "수확 연도 값이 허용 범위를 "
        "벗어났습니다."
        in warnings
    )


def test_oxidation_range_warning() -> None:
    parse_result = TeaParser().parse(
        "녹차"
    )

    _, warnings = apply_tea_rules(
        attributes={
            "tea_type": "green",
            "oxidation_min_percent": 90,
            "oxidation_max_percent": 20,
        },
        scores={
            "knowledge": 50.0,
        },
        parse_result=parse_result,
    )

    assert (
        "산화도 범위 값이 허용 범위를 "
        "벗어났습니다."
        in warnings
    )


def test_rules_preserve_parser_warnings() -> None:
    product = {
        "product_name": "제주 상품",
    }

    parse_result = TeaParser().parse_product(
        product
    )

    attributes = build_tea_attributes(
        product=product,
        parse_result=parse_result,
    )
    scores = calculate_tea_scores(
        product=product,
        parse_result=parse_result,
    )

    _, warnings = apply_tea_rules(
        attributes=attributes,
        scores=scores,
        parse_result=parse_result,
    )

    for warning in parse_result.warnings:
        assert warning in warnings


def test_rules_do_not_duplicate_messages() -> None:
    reasons, warnings = _apply(
        {
            "product_name": "녹차",
        }
    )

    assert len(reasons) == len(set(reasons))
    assert len(warnings) == len(set(warnings))


def test_rules_do_not_mutate_inputs() -> None:
    product = _complete_product()

    parse_result = TeaParser().parse_product(
        product
    )
    attributes = build_tea_attributes(
        product=product,
        parse_result=parse_result,
    )
    scores = calculate_tea_scores(
        product=product,
        parse_result=parse_result,
    )

    attributes_before = deepcopy(attributes)
    scores_before = deepcopy(scores)
    parse_result_before = parse_result.to_dict()

    apply_tea_rules(
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
    parse_result = TeaParser().parse(
        "녹차"
    )

    with pytest.raises(
        TypeError,
        match="attributes must be a Mapping",
    ):
        apply_tea_rules(
            attributes=[],  # type: ignore[arg-type]
            scores={},
            parse_result=parse_result,
        )


def test_rules_reject_invalid_scores() -> None:
    parse_result = TeaParser().parse(
        "녹차"
    )

    with pytest.raises(
        TypeError,
        match="scores must be a Mapping",
    ):
        apply_tea_rules(
            attributes={},
            scores=[],  # type: ignore[arg-type]
            parse_result=parse_result,
        )


def test_rules_reject_invalid_parse_result() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "parse_result must be "
            "TeaParseResult"
        ),
    ):
        apply_tea_rules(
            attributes={},
            scores={},
            parse_result=object(),  # type: ignore[arg-type]
        )


def test_rules_return_string_lists() -> None:
    parse_result = TeaParser().parse(
        "일반 식품 상품"
    )

    reasons, warnings = apply_tea_rules(
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


def test_rules_do_not_calculate_scores() -> None:
    parse_result = TeaParser().parse(
        "녹차"
    )

    reasons, _ = apply_tea_rules(
        attributes={
            "tea_type": "green",
        },
        scores={
            "knowledge": 50.0,
        },
        parse_result=parse_result,
    )

    assert (
        "Tea Knowledge 평가가 "
        "확인되었습니다."
        in reasons
    )


def test_rules_are_deterministic() -> None:
    product = _complete_product()

    parse_result = TeaParser().parse_product(
        product
    )
    attributes = build_tea_attributes(
        product=product,
        parse_result=parse_result,
    )
    scores = calculate_tea_scores(
        product=product,
        parse_result=parse_result,
    )

    first = apply_tea_rules(
        attributes=attributes,
        scores=scores,
        parse_result=parse_result,
    )
    second = apply_tea_rules(
        attributes=attributes,
        scores=scores,
        parse_result=parse_result,
    )

    assert first == second
    assert first[0] is not second[0]
    assert first[1] is not second[1]
