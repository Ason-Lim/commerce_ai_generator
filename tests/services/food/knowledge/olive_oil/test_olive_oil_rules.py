from __future__ import annotations

from copy import deepcopy

import pytest

from app.services.food.knowledge.olive_oil.attributes import (
    build_olive_oil_attributes,
)
from app.services.food.knowledge.olive_oil.parser import (
    OliveOilParser,
)
from app.services.food.knowledge.olive_oil.rules import (
    apply_olive_oil_rules,
    deduplicate_strings,
)
from app.services.food.knowledge.olive_oil.scoring import (
    calculate_olive_oil_scores,
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
        "country": "Spain",
        "country_code": "ES",
        "extraction_method": "cold pressed",
        "grade": "extra virgin olive oil",
        "volume": "500ml",
        "packaging_type": "dark glass bottle",
        "organic": True,
        "certifications": [
            "Organic",
            "PDO",
        ],
        "quality_score": 80,
        "price_score": 70,
        "trust_score": 90,
    }


def _apply(
    product: dict[str, object],
) -> tuple[list[str], list[str]]:
    parse_result = OliveOilParser().parse_product(
        product
    )

    attributes = build_olive_oil_attributes(
        product=product,
        parse_result=parse_result,
    )

    scores = calculate_olive_oil_scores(
        product=product,
        parse_result=parse_result,
    )

    return apply_olive_oil_rules(
        attributes=attributes,
        scores=scores,
        parse_result=parse_result,
    )


def test_complete_product_generates_reasons() -> None:
    reasons, warnings = _apply(
        _complete_product()
    )

    assert (
        "올리브오일 종류, 품종, 원산지, "
        "가공 방식, 등급 정보가 모두 확인되었습니다."
        in reasons
    )

    assert (
        "올리브오일 종류는 "
        "single_varietal입니다."
        in reasons
    )
    assert "올리브 품종은 arbequina입니다." in reasons
    assert "원산지는 Spain입니다." in reasons
    assert "가공 방식은 cold_pressed입니다." in reasons
    assert (
        "올리브오일 등급은 extra_virgin입니다."
        in reasons
    )

    assert "표시 용량은 500ml입니다." in reasons
    assert (
        "포장 형태는 dark glass bottle입니다."
        in reasons
    )
    assert (
        "표시된 인증 정보는 Organic, PDO입니다."
        in reasons
    )
    assert (
        "유기농 상품으로 표시되어 있습니다."
        in reasons
    )

    assert warnings == []


def test_registry_characteristics_are_included() -> None:
    reasons, _ = _apply(
        _complete_product()
    )

    assert (
        "Registry에서 프리미엄 속성이 "
        "확인되었습니다."
        in reasons
    )
    assert (
        "저온 추출 또는 냉압착 가공 특성이 "
        "확인되었습니다."
        in reasons
    )
    assert (
        "기계적 추출 방식이 확인되었습니다."
        in reasons
    )
    assert (
        "버진 등급 특성이 확인되었습니다."
        in reasons
    )
    assert (
        "엑스트라 버진 등급의 올리브오일입니다."
        in reasons
    )


def test_score_reasons_are_included() -> None:
    reasons, _ = _apply(
        _complete_product()
    )

    assert (
        "Olive Oil 품질 평가가 우수합니다."
        in reasons
    )
    assert (
        "구조화된 상품 정보의 신뢰도 평가가 "
        "충분합니다."
        in reasons
    )
    assert (
        "Olive Oil Knowledge 평가가 "
        "매우 높은 수준입니다."
        in reasons
    )


def test_partial_product_generates_warnings() -> None:
    reasons, warnings = _apply(
        {
            "product_name": (
                "스페인 아르베키나 올리브오일"
            ),
        }
    )

    assert (
        "Olive Oil 분석에 활용할 수 있는 "
        "핵심 정보가 확인되었습니다."
        in reasons
    )
    assert "올리브 품종은 arbequina입니다." in reasons
    assert "원산지는 spain입니다." in reasons

    assert (
        "올리브오일 가공 방식 정보가 "
        "확인되지 않았습니다."
        in warnings
    )
    assert (
        "올리브오일 등급 정보가 "
        "확인되지 않았습니다."
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
        "Olive Oil 도메인 분석에 필요한 정보가 "
        "충분하지 않습니다."
        in warnings
    )
    assert (
        "Olive Oil Registry 기반 평가 점수를 "
        "계산할 수 없습니다."
        in warnings
    )


def test_explicit_country_is_used() -> None:
    reasons, _ = _apply(
        {
            "product_name": (
                "스페인 엑스트라 버진 올리브오일"
            ),
            "country": "Kingdom of Spain",
        }
    )

    assert (
        "원산지는 Kingdom of Spain입니다."
        in reasons
    )


def test_non_organic_reason() -> None:
    reasons, _ = _apply(
        {
            "product_name": (
                "엑스트라 버진 올리브오일"
            ),
            "organic": False,
        }
    )

    assert (
        "일반 재배 상품으로 표시되어 있습니다."
        in reasons
    )


def test_low_quality_and_trust_warnings() -> None:
    parse_result = OliveOilParser().parse(
        "엑스트라 버진 올리브오일"
    )

    _, warnings = apply_olive_oil_rules(
        attributes={
            "grade": "extra_virgin",
        },
        scores={
            "quality": 40.0,
            "trust": 30.0,
            "knowledge": 50.0,
        },
        parse_result=parse_result,
    )

    assert (
        "Olive Oil 품질 평가 점수가 낮습니다."
        in warnings
    )
    assert (
        "상품 정보의 신뢰도 평가가 낮습니다."
        in warnings
    )


def test_invalid_country_code_warning() -> None:
    parse_result = OliveOilParser().parse(
        "엑스트라 버진 올리브오일"
    )

    _, warnings = apply_olive_oil_rules(
        attributes={
            "grade": "extra_virgin",
            "country_code": "ESP",
        },
        scores={
            "knowledge": 95.0,
        },
        parse_result=parse_result,
    )

    assert (
        "원산지 국가 코드가 ISO 2자리 "
        "형식이 아닙니다."
        in warnings
    )


def test_invalid_grade_score_warning() -> None:
    parse_result = OliveOilParser().parse(
        "엑스트라 버진 올리브오일"
    )

    _, warnings = apply_olive_oil_rules(
        attributes={
            "grade": "extra_virgin",
            "grade_score": 150,
        },
        scores={
            "knowledge": 95.0,
        },
        parse_result=parse_result,
    )

    assert (
        "등급 Registry 점수가 허용 범위를 "
        "벗어났습니다."
        in warnings
    )


def test_conflicting_refined_and_virgin_warning() -> None:
    parse_result = OliveOilParser().parse(
        "엑스트라 버진 올리브오일"
    )

    _, warnings = apply_olive_oil_rules(
        attributes={
            "grade": "extra_virgin",
            "processing_refined": True,
            "grade_virgin": True,
        },
        scores={
            "knowledge": 95.0,
        },
        parse_result=parse_result,
    )

    assert (
        "정제 가공 표시와 버진 등급 표시가 "
        "동시에 존재하여 확인이 필요합니다."
        in warnings
    )


def test_rules_preserve_parser_warnings() -> None:
    product = {
        "product_name": "스페인 상품",
    }

    parse_result = OliveOilParser().parse_product(
        product
    )

    attributes = build_olive_oil_attributes(
        product=product,
        parse_result=parse_result,
    )

    scores = calculate_olive_oil_scores(
        product=product,
        parse_result=parse_result,
    )

    _, warnings = apply_olive_oil_rules(
        attributes=attributes,
        scores=scores,
        parse_result=parse_result,
    )

    for warning in parse_result.warnings:
        assert warning in warnings


def test_rules_do_not_duplicate_messages() -> None:
    reasons, warnings = _apply(
        {
            "product_name": (
                "엑스트라 버진 올리브오일"
            ),
        }
    )

    assert len(reasons) == len(set(reasons))
    assert len(warnings) == len(set(warnings))


def test_rules_do_not_mutate_inputs() -> None:
    product = _complete_product()

    parse_result = OliveOilParser().parse_product(
        product
    )

    attributes = build_olive_oil_attributes(
        product=product,
        parse_result=parse_result,
    )

    scores = calculate_olive_oil_scores(
        product=product,
        parse_result=parse_result,
    )

    attributes_before = deepcopy(attributes)
    scores_before = deepcopy(scores)
    parse_result_before = parse_result.to_dict()

    apply_olive_oil_rules(
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
    parse_result = OliveOilParser().parse(
        "엑스트라 버진 올리브오일"
    )

    with pytest.raises(
        TypeError,
        match="attributes must be a Mapping",
    ):
        apply_olive_oil_rules(
            attributes=[],  # type: ignore[arg-type]
            scores={},
            parse_result=parse_result,
        )


def test_rules_reject_invalid_scores() -> None:
    parse_result = OliveOilParser().parse(
        "엑스트라 버진 올리브오일"
    )

    with pytest.raises(
        TypeError,
        match="scores must be a Mapping",
    ):
        apply_olive_oil_rules(
            attributes={},
            scores=[],  # type: ignore[arg-type]
            parse_result=parse_result,
        )


def test_rules_reject_invalid_parse_result() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "parse_result must be "
            "OliveOilParseResult"
        ),
    ):
        apply_olive_oil_rules(
            attributes={},
            scores={},
            parse_result=object(),  # type: ignore[arg-type]
        )


def test_rules_return_string_lists() -> None:
    parse_result = OliveOilParser().parse(
        "일반 식품 상품"
    )

    reasons, warnings = apply_olive_oil_rules(
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
    parse_result = OliveOilParser().parse(
        "엑스트라 버진 올리브오일"
    )

    reasons, _ = apply_olive_oil_rules(
        attributes={
            "grade": "extra_virgin",
        },
        scores={
            "knowledge": 50.0,
        },
        parse_result=parse_result,
    )

    assert (
        "Olive Oil Knowledge 평가가 "
        "확인되었습니다."
        in reasons
    )


def test_rules_are_deterministic() -> None:
    product = _complete_product()

    parse_result = OliveOilParser().parse_product(
        product
    )

    attributes = build_olive_oil_attributes(
        product=product,
        parse_result=parse_result,
    )

    scores = calculate_olive_oil_scores(
        product=product,
        parse_result=parse_result,
    )

    first = apply_olive_oil_rules(
        attributes=attributes,
        scores=scores,
        parse_result=parse_result,
    )
    second = apply_olive_oil_rules(
        attributes=attributes,
        scores=scores,
        parse_result=parse_result,
    )

    assert first == second
    assert first[0] is not second[0]
    assert first[1] is not second[1]
