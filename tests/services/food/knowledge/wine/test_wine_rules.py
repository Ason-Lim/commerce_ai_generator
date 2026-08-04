from __future__ import annotations

import pytest

from app.services.food.knowledge.wine.attributes import (
    build_wine_attributes,
)
from app.services.food.knowledge.wine.parser import (
    WineParser,
)
from app.services.food.knowledge.wine.rules import (
    apply_wine_rules,
)
from app.services.food.knowledge.wine.scoring import (
    calculate_wine_scores,
)


def _build_analysis(
    product: dict[str, object],
) -> tuple[
    dict[str, object],
    dict[str, float],
    object,
]:
    parse_result = WineParser().parse_product(
        product
    )

    attributes = build_wine_attributes(
        product=product,
        parse_result=parse_result,
    )

    scores = calculate_wine_scores(
        product=product,
        parse_result=parse_result,
    )

    return (
        attributes,
        scores,
        parse_result,
    )


def test_apply_wine_rules_for_complete_product() -> None:
    product = {
        "product_name": (
            "2020 보르도 카베르네 소비뇽 "
            "레드 와인 드라이 풀 바디 "
            "높은 산도 13.5%"
        ),
        "producer": "Example Winery",
        "volume": "750ml",
        "certifications": ["AOC"],
        "price_score": 75,
    }

    attributes, scores, parse_result = (
        _build_analysis(product)
    )

    reasons, warnings = apply_wine_rules(
        attributes=attributes,
        scores=scores,
        parse_result=parse_result,
    )

    assert reasons
    assert (
        "와인 타입, 품종, 산지, 당도, 바디, "
        "산도 정보가 모두 확인되었습니다."
        in reasons
    )
    assert (
        "2020 빈티지 정보가 제공되었습니다."
        in reasons
    )
    assert (
        "알코올 도수 13.5%가 확인되었습니다."
        in reasons
    )
    assert (
        "드라이 스타일의 와인입니다."
        in reasons
    )
    assert not warnings


def test_apply_wine_rules_warns_for_missing_information() -> None:
    product = {
        "product_name": "보르도 레드 와인",
    }

    attributes, scores, parse_result = (
        _build_analysis(product)
    )

    reasons, warnings = apply_wine_rules(
        attributes=attributes,
        scores=scores,
        parse_result=parse_result,
    )

    assert reasons
    assert (
        "빈티지 정보가 확인되지 않았습니다."
        in warnings
    )
    assert (
        "알코올 도수 정보가 확인되지 않았습니다."
        in warnings
    )
    assert (
        "생산자 또는 와이너리 정보가 "
        "확인되지 않았습니다."
        in warnings
    )
    assert (
        "상품 용량 정보가 확인되지 않았습니다."
        in warnings
    )


def test_apply_wine_rules_for_unknown_product() -> None:
    product = {
        "product_name": (
            "등록되지 않은 임의의 상품"
        ),
    }

    attributes, scores, parse_result = (
        _build_analysis(product)
    )

    reasons, warnings = apply_wine_rules(
        attributes=attributes,
        scores=scores,
        parse_result=parse_result,
    )

    assert (
        "추천에 필요한 와인 핵심 정보가 부족합니다."
        in warnings
    )
    assert (
        "Wine Registry 기반 지식 점수를 "
        "계산할 수 없습니다."
        in warnings
    )


def test_apply_wine_rules_detects_premium_registry_data() -> None:
    product = {
        "product_name": (
            "부르고뉴 샤르도네 화이트 와인"
        ),
        "producer": "Example Winery",
        "volume": "750ml",
    }

    attributes, scores, parse_result = (
        _build_analysis(product)
    )

    reasons, _ = apply_wine_rules(
        attributes=attributes,
        scores=scores,
        parse_result=parse_result,
    )

    assert (
        "프리미엄 산지 또는 품종 정보가 "
        "확인되었습니다."
        in reasons
    )


def test_apply_wine_rules_detects_style_information() -> None:
    product = {
        "product_name": (
            "리슬링 화이트 와인 드라이 "
            "높은 산도"
        ),
        "producer": "Example Winery",
        "volume": "750ml",
    }

    attributes, scores, parse_result = (
        _build_analysis(product)
    )

    reasons, _ = apply_wine_rules(
        attributes=attributes,
        scores=scores,
        parse_result=parse_result,
    )

    assert (
        "드라이 스타일의 와인입니다."
        in reasons
    )
    assert (
        "높은 산도로 선명한 산미가 기대됩니다."
        in reasons
    )
    assert (
        "아로마틱 품종 특성이 확인되었습니다."
        in reasons
    )


def test_apply_wine_rules_detects_certifications() -> None:
    product = {
        "product_name": "보르도 레드 와인",
        "producer": "Example Winery",
        "volume": "750ml",
        "certifications": [
            "AOC",
            "Organic",
        ],
        "organic": True,
        "biodynamic": True,
    }

    attributes, scores, parse_result = (
        _build_analysis(product)
    )

    reasons, _ = apply_wine_rules(
        attributes=attributes,
        scores=scores,
        parse_result=parse_result,
    )

    assert (
        "인증 또는 품질 표시 정보가 제공되었습니다."
        in reasons
    )
    assert (
        "유기농 와인 정보가 확인되었습니다."
        in reasons
    )
    assert (
        "바이오다이나믹 와인 정보가 확인되었습니다."
        in reasons
    )


def test_apply_wine_rules_preserves_parser_warnings() -> None:
    product = {
        "product_name": (
            "등록되지 않은 임의의 상품"
        ),
    }

    attributes, scores, parse_result = (
        _build_analysis(product)
    )

    _, warnings = apply_wine_rules(
        attributes=attributes,
        scores=scores,
        parse_result=parse_result,
    )

    assert (
        "Wine Registry에서 일치하는 "
        "속성을 찾지 못했습니다."
        in warnings
    )


def test_apply_wine_rules_deduplicates_results() -> None:
    product = {
        "product_name": "보르도 레드 와인",
    }

    attributes, scores, parse_result = (
        _build_analysis(product)
    )

    first = apply_wine_rules(
        attributes=attributes,
        scores=scores,
        parse_result=parse_result,
    )
    second = apply_wine_rules(
        attributes=attributes,
        scores=scores,
        parse_result=parse_result,
    )

    assert first == second
    assert len(first[0]) == len(set(first[0]))
    assert len(first[1]) == len(set(first[1]))


def test_apply_wine_rules_does_not_modify_inputs() -> None:
    product = {
        "product_name": (
            "2020 보르도 레드 와인 13%"
        ),
    }

    attributes, scores, parse_result = (
        _build_analysis(product)
    )

    attributes_before = dict(attributes)
    scores_before = dict(scores)

    apply_wine_rules(
        attributes=attributes,
        scores=scores,
        parse_result=parse_result,
    )

    assert attributes == attributes_before
    assert scores == scores_before


def test_apply_wine_rules_rejects_invalid_inputs() -> None:
    product = {
        "product_name": "보르도 레드 와인",
    }

    attributes, scores, parse_result = (
        _build_analysis(product)
    )

    with pytest.raises(TypeError):
        apply_wine_rules(
            attributes=[],  # type: ignore[arg-type]
            scores=scores,
            parse_result=parse_result,
        )

    with pytest.raises(TypeError):
        apply_wine_rules(
            attributes=attributes,
            scores=[],  # type: ignore[arg-type]
            parse_result=parse_result,
        )

    with pytest.raises(TypeError):
        apply_wine_rules(
            attributes=attributes,
            scores=scores,
            parse_result=None,  # type: ignore[arg-type]
        )
