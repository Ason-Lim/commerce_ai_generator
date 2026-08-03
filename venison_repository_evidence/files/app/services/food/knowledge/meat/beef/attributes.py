from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.meat.beef.parser_models import (
    BeefParseResult,
)


COUNTRY_NAMES: dict[str, str] = {
    "KR": "대한민국",
    "US": "미국",
    "AU": "호주",
    "JP": "일본",
}


def extract_beef_product_name(
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


def extract_beef_country_text(
    *,
    product: Mapping[str, Any],
    parse_result: BeefParseResult,
) -> str | None:
    """
    상품 원문에 원산지가 있으면 원문을 우선 사용한다.

    원문이 없으면 Parser가 탐지한 국가 코드를
    표준 국가명으로 변환한다.
    """
    raw_country = (
        product.get("country")
        or product.get("origin_country")
        or product.get("country_of_origin")
        or product.get("origin")
    )

    if raw_country is not None:
        country_text = str(
            raw_country
        ).strip()

        if country_text:
            return country_text

    country_code = parse_result.metadata.get(
        "country_code"
    )

    if not country_code:
        return None

    normalized_country_code = str(
        country_code
    )

    return COUNTRY_NAMES.get(
        normalized_country_code,
        normalized_country_code,
    )


def extract_beef_weight(
    product: Mapping[str, Any],
) -> Any:
    """
    상품 Mapping에서 중량 또는 수량 정보를 추출한다.
    """
    return (
        product.get("weight")
        or product.get("quantity")
        or product.get("weight_text")
        or product.get("net_weight")
    )


def extract_beef_marbling(
    product: Mapping[str, Any],
) -> Any:
    """
    상품 Mapping에서 마블링 정보를 추출한다.
    """
    return (
        product.get("marbling")
        or product.get("marbling_score")
        or product.get("bms")
    )


def build_beef_attributes(
    *,
    product: Mapping[str, Any],
    parse_result: BeefParseResult,
) -> dict[str, Any]:
    """
    Parser의 표준화 값과 Registry 정보를
    FoodKnowledgeResult용 attributes로 변환한다.
    """
    country_code = parse_result.metadata.get(
        "country_code"
    )

    attributes: dict[str, Any] = {
        "product_name": extract_beef_product_name(
            product
        ),
        "country": extract_beef_country_text(
            product=product,
            parse_result=parse_result,
        ),
        "country_code": country_code,
        "breed": parse_result.breed,
        "grade": parse_result.grade,
        "cut": parse_result.cut,
        "weight": extract_beef_weight(
            product
        ),
        "marbling": extract_beef_marbling(
            product
        ),
        "confidence": parse_result.confidence,
        "breed_confidence": (
            parse_result.breed_confidence
        ),
        "grade_confidence": (
            parse_result.grade_confidence
        ),
        "cut_confidence": (
            parse_result.cut_confidence
        ),
        "detected_keywords": list(
            parse_result.detected_keywords
        ),
        "is_complete": parse_result.is_complete,
    }

    if parse_result.breed_match is not None:
        breed = parse_result.breed_match.breed

        attributes.update(
            {
                "breed_registry_key": (
                    breed.registry_key
                ),
                "breed_score": breed.score,
                "breed_premium": breed.premium,
                "breed_origin_country": (
                    breed.origin_country
                ),
                "breed_type": breed.breed_type,
                "breed_description": (
                    breed.description
                ),
            }
        )

    if parse_result.grade_match is not None:
        grade = parse_result.grade_match.grade

        attributes.update(
            {
                "grade_registry_key": (
                    grade.registry_key
                ),
                "grade_country_code": (
                    grade.country_code
                ),
                "grade_country_name": (
                    grade.country_name
                ),
                "grade_system": grade.system,
                "grade_score": grade.score,
                "grade_premium": grade.premium,
                "grade_rank": grade.rank,
                "grade_description": (
                    grade.description
                ),
            }
        )

    if parse_result.cut_match is not None:
        cut = parse_result.cut_match.cut

        attributes.update(
            {
                "cut_registry_key": (
                    cut.registry_key
                ),
                "cut_score": cut.score,
                "cut_premium": cut.premium,
                "cut_tenderness_score": (
                    cut.tenderness_score
                ),
                "cut_fat_level": cut.fat_level,
                "cut_cooking_methods": list(
                    cut.cooking_methods
                ),
                "cut_description": (
                    cut.description
                ),
            }
        )

    return attributes


__all__ = [
    "COUNTRY_NAMES",
    "build_beef_attributes",
    "extract_beef_country_text",
    "extract_beef_marbling",
    "extract_beef_product_name",
    "extract_beef_weight",
]