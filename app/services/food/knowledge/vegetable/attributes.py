from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.vegetable.parser_models import (
    VegetableParseResult,
)


def extract_vegetable_product_name(
    product: Mapping[str, Any],
) -> str:
    """
    상품 Mapping에서 대표 상품명을 추출한다.
    """
    return str(
        product.get("product_name")
        or product.get("title")
        or product.get("name")
        or product.get("raw_name")
        or product.get("display_name")
        or ""
    ).strip()


def extract_vegetable_weight(
    product: Mapping[str, Any],
) -> Any:
    """
    상품의 명시적 중량/수량 원문을 반환한다.

    단위 파싱이나 점수 계산은 수행하지 않는다.
    """
    for field_name in (
        "weight",
        "quantity",
        "package_weight",
        "net_weight",
        "weight_text",
    ):
        if field_name not in product:
            continue

        value = product.get(field_name)

        if value is not None:
            return value

    return None


def build_vegetable_attributes(
    *,
    product: Mapping[str, Any],
    parse_result: VegetableParseResult,
) -> dict[str, Any]:
    """
    Vegetable ParseResult와 구조화 상품 데이터를
    FoodKnowledgeResult용 attributes로 변환한다.

    점수 계산 및 비즈니스 Rule 평가는 수행하지 않는다.
    """
    if not isinstance(product, Mapping):
        raise TypeError(
            "product must be a Mapping"
        )

    if not isinstance(
        parse_result,
        VegetableParseResult,
    ):
        raise TypeError(
            "parse_result must be VegetableParseResult"
        )

    return {
        "product_name": (
            extract_vegetable_product_name(
                product
            )
        ),
        "origin": parse_result.origin,
        "variety": parse_result.variety,
        "grade": parse_result.grade,
        "weight": extract_vegetable_weight(
            product
        ),
        "weight_grams": (
            parse_result.weight_grams
        ),
        "confidence": (
            parse_result.confidence
        ),
        "detected_keywords": list(
            parse_result.detected_keywords
        ),
        "warnings": list(
            parse_result.warnings
        ),
        "matched_field_count": (
            parse_result.matched_field_count
        ),
        "is_complete": (
            parse_result.is_complete
        ),
        "is_usable": (
            parse_result.is_usable
        ),
    }


__all__ = [
    "build_vegetable_attributes",
    "extract_vegetable_product_name",
    "extract_vegetable_weight",
]
