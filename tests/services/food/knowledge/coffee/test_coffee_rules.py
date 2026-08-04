from __future__ import annotations

from copy import deepcopy

import pytest

from app.services.food.knowledge.coffee import (
    CoffeeParser,
    apply_coffee_rules,
    build_coffee_attributes,
    calculate_coffee_scores,
    deduplicate_strings,
)


def _complete_product() -> dict[str, object]:
    return {
        "product_name": (
            "에티오피아 100% 아라비카 "
            "라이트 로스트 워시드 원두"
        ),
        "bean_type": "100% arabica",
        "origin_country": "Ethiopia",
        "country_code": "ET",
        "roast_level": "light roast",
        "processing_method": "washed process",
        "weight": "200g",
        "grind_type": "whole bean",
        "product_form": "원두",
        "decaf": False,
        "certifications": [
            "Organic",
            "Fair Trade",
        ],
        "flavor_notes": [
            "자스민",
            "레몬",
            "베르가못",
        ],
        "altitude": "1,900m",
        "roast_date": "2026-08-01",
        "quality_score": 80,
        "price_score": 70,
        "trust_score": 90,
    }


def _apply(
    product: dict[str, object],
) -> tuple[list[str], list[str]]:
    parse_result = (
        CoffeeParser().parse_product(
            product
        )
    )

    attributes = build_coffee_attributes(
        product=product,
        parse_result=parse_result,
    )

    scores = calculate_coffee_scores(
        product=product,
        parse_result=parse_result,
    )

    return apply_coffee_rules(
        attributes=attributes,
        scores=scores,
        parse_result=parse_result,
    )


def test_complete_product_generates_reasons() -> None:
    reasons, warnings = _apply(
        _complete_product()
    )

    assert (
        "원두 종류는 아라비카입니다."
        in reasons
    )
    assert (
        "원산지는 Ethiopia입니다."
        in reasons
    )
    assert (
        "로스팅 단계는 라이트 로스트입니다."
        in reasons
    )
    assert (
        "가공 방식은 워시드입니다."
        in reasons
    )
    assert (
        "분쇄 형태는 whole bean입니다."
        in reasons
    )
    assert (
        "상품 형태는 원두입니다."
        in reasons
    )
    assert (
        "표시 중량은 200g입니다."
        in reasons
    )
    assert (
        "재배 고도 표시는 1,900m입니다."
        in reasons
    )
    assert (
        "로스팅 날짜는 2026-08-01입니다."
        in reasons
    )
    assert (
        "일반 카페인 상품으로 "
        "표시되어 있습니다."
        in reasons
    )
    assert (
        "표시된 인증 정보는 "
        "Organic, Fair Trade입니다."
        in reasons
    )
    assert (
        "표시된 향미 노트는 "
        "자스민, 레몬, 베르가못입니다."
        in reasons
    )

    assert warnings == []


def test_registry_and_score_guidance_is_included() -> None:
    reasons, _ = _apply(
        _complete_product()
    )

    assert (
        "Registry에서 프리미엄 속성이 "
        "확인되었습니다."
        in reasons
    )

    assert (
        "Coffee Knowledge 평가가 "
        "매우 높은 수준입니다."
        in reasons
    )

    assert (
        "Registry 기준 산미 특성이 "
        "뚜렷한 상품입니다."
        in reasons
    )

    assert (
        "Registry 기준 향미 평가가 "
        "높은 상품입니다."
        in reasons
    )

    assert (
        "Registry 기준 향미 선명도가 "
        "높은 가공 방식입니다."
        in reasons
    )


def test_partial_product_generates_warnings() -> None:
    reasons, warnings = _apply(
        {
            "product_name": (
                "에티오피아 워시드 커피"
            ),
        }
    )

    assert (
        "원산지는 에티오피아입니다."
        in reasons
    )
    assert (
        "가공 방식은 워시드입니다."
        in reasons
    )

    assert (
        "원두 종류 정보가 "
        "확인되지 않았습니다."
        in warnings
    )
    assert (
        "로스팅 단계 정보가 "
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
        "Coffee Registry 기반 평가 점수를 "
        "계산할 수 없습니다."
        in warnings
    )

    assert (
        "Coffee 도메인 분석에 필요한 정보가 "
        "충분하지 않습니다."
        in warnings
    )


def test_explicit_country_is_used() -> None:
    reasons, _ = _apply(
        {
            "product_name": (
                "에티오피아 아라비카 원두"
            ),
            "country": "Ethiopia",
        }
    )

    assert (
        "원산지는 Ethiopia입니다."
        in reasons
    )


def test_decaf_reason() -> None:
    reasons, _ = _apply(
        {
            "product_name": "아라비카 원두",
            "decaf": True,
        }
    )

    assert (
        "디카페인 상품으로 "
        "표시되어 있습니다."
        in reasons
    )


def test_rules_preserve_parser_warnings() -> None:
    product = {
        "product_name": "아라비카 원두",
    }

    parse_result = (
        CoffeeParser().parse_product(
            product
        )
    )

    attributes = build_coffee_attributes(
        product=product,
        parse_result=parse_result,
    )

    scores = calculate_coffee_scores(
        product=product,
        parse_result=parse_result,
    )

    _, warnings = apply_coffee_rules(
        attributes=attributes,
        scores=scores,
        parse_result=parse_result,
    )

    for warning in parse_result.warnings:
        assert warning in warnings


def test_rules_do_not_duplicate_warnings() -> None:
    _, warnings = _apply(
        {
            "product_name": "아라비카 원두",
        }
    )

    assert len(warnings) == len(set(warnings))


def test_rules_do_not_mutate_inputs() -> None:
    product = _complete_product()

    parse_result = (
        CoffeeParser().parse_product(
            product
        )
    )

    attributes = build_coffee_attributes(
        product=product,
        parse_result=parse_result,
    )

    scores = calculate_coffee_scores(
        product=product,
        parse_result=parse_result,
    )

    attributes_before = deepcopy(attributes)
    scores_before = deepcopy(scores)
    parse_result_before = (
        parse_result.to_dict()
    )

    apply_coffee_rules(
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
    parse_result = CoffeeParser().parse(
        "아라비카 원두"
    )

    with pytest.raises(
        TypeError,
        match="attributes must be a Mapping",
    ):
        apply_coffee_rules(
            attributes=[],  # type: ignore[arg-type]
            scores={},
            parse_result=parse_result,
        )


def test_rules_reject_invalid_scores() -> None:
    parse_result = CoffeeParser().parse(
        "아라비카 원두"
    )

    with pytest.raises(
        TypeError,
        match="scores must be a Mapping",
    ):
        apply_coffee_rules(
            attributes={},
            scores=[],  # type: ignore[arg-type]
            parse_result=parse_result,
        )


def test_rules_reject_invalid_parse_result() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "parse_result must be "
            "CoffeeParseResult"
        ),
    ):
        apply_coffee_rules(
            attributes={},
            scores={},
            parse_result=object(),  # type: ignore[arg-type]
        )


def test_rules_return_string_lists() -> None:
    parse_result = CoffeeParser().parse(
        "일반 식품 상품"
    )

    reasons, warnings = apply_coffee_rules(
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
    parse_result = CoffeeParser().parse(
        "아라비카 원두"
    )

    reasons, warnings = apply_coffee_rules(
        attributes={
            "bean": "아라비카",
        },
        scores={
            "knowledge": 50.0,
        },
        parse_result=parse_result,
    )

    assert (
        "원두 종류는 아라비카입니다."
        in reasons
    )
    assert (
        "Coffee Knowledge 평가가 "
        "확인되었습니다."
        in reasons
    )
    assert warnings


def test_rules_are_deterministic() -> None:
    product = _complete_product()

    parse_result = (
        CoffeeParser().parse_product(
            product
        )
    )

    attributes = build_coffee_attributes(
        product=product,
        parse_result=parse_result,
    )

    scores = calculate_coffee_scores(
        product=product,
        parse_result=parse_result,
    )

    first = apply_coffee_rules(
        attributes=attributes,
        scores=scores,
        parse_result=parse_result,
    )

    second = apply_coffee_rules(
        attributes=attributes,
        scores=scores,
        parse_result=parse_result,
    )

    assert first == second
    assert first[0] is not second[0]
    assert first[1] is not second[1]
