from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.cheese.parser_models import (
    CheeseParseResult,
)


def extract_cheese_product_name(
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


def extract_cheese_country_text(
    *,
    product: Mapping[str, Any],
    parse_result: CheeseParseResult,
) -> str | None:
    """
    상품에 원산지가 명시되어 있으면 원문을 우선 사용한다.

    구조화된 원산지가 없으면 Cheese Origin Registry에서
    탐지된 표준 국가명을 사용한다.
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

    if parse_result.origin_match is None:
        return None

    return (
        parse_result
        .origin_match
        .entry
        .canonical_name
    )


def extract_cheese_country_code(
    *,
    product: Mapping[str, Any],
    parse_result: CheeseParseResult,
) -> str | None:
    """
    상품에 명시된 국가 코드를 우선 사용한다.

    명시값이 없으면 Origin Registry의 country_code를 사용한다.
    """
    raw_country_code = (
        product.get("country_code")
        or product.get("origin_country_code")
    )

    if raw_country_code is not None:
        country_code = str(
            raw_country_code
        ).strip().upper()

        if country_code:
            return country_code

    if parse_result.origin_match is None:
        return None

    country_code = (
        parse_result
        .origin_match
        .entry
        .country_code
    )

    if country_code is None:
        return None

    normalized = str(
        country_code
    ).strip().upper()

    return normalized or None


def extract_cheese_weight(
    product: Mapping[str, Any],
) -> Any:
    """
    상품 중량 또는 수량 정보를 추출한다.
    """
    return (
        product.get("weight")
        or product.get("net_weight")
        or product.get("weight_text")
        or product.get("quantity")
        or product.get("size")
    )


def extract_cheese_storage_type(
    product: Mapping[str, Any],
) -> str | None:
    """
    냉장·냉동 등 구조화된 보관 상태를 추출한다.
    """
    raw_value = (
        product.get("storage_type")
        or product.get("storage")
        or product.get("temperature_type")
        or product.get("freshness_type")
    )

    if raw_value is None:
        return None

    normalized = str(
        raw_value
    ).strip()

    return normalized or None


def extract_cheese_packaging_type(
    product: Mapping[str, Any],
) -> str | None:
    """
    블록·슬라이스·슈레드 등 포장 또는 가공 형태를 추출한다.
    """
    raw_value = (
        product.get("packaging_type")
        or product.get("package_type")
        or product.get("format")
        or product.get("product_form")
        or product.get("processing_type")
    )

    if raw_value is None:
        return None

    normalized = str(
        raw_value
    ).strip()

    return normalized or None


def extract_cheese_pasteurization(
    product: Mapping[str, Any],
) -> str | None:
    """
    살균·비살균 등 원유 처리 정보를 추출한다.
    """
    raw_value = None

    for field_name in (
        "pasteurization",
        "pasteurized",
        "milk_treatment",
        "raw_milk_status",
    ):
        if field_name in product:
            raw_value = product[field_name]
            break

    if raw_value is None:
        return None

    if isinstance(raw_value, bool):
        return (
            "pasteurized"
            if raw_value
            else "unpasteurized"
        )

    normalized = str(
        raw_value
    ).strip()

    return normalized or None


def extract_cheese_certifications(
    product: Mapping[str, Any],
) -> list[str]:
    """
    인증 및 품질 표시를 문자열 목록으로 변환한다.
    """
    raw_value = (
        product.get("certifications")
        or product.get("certification")
        or product.get("certificates")
        or product.get("labels")
        or product.get("quality_labels")
    )

    if raw_value is None:
        return []

    if isinstance(raw_value, str):
        normalized = raw_value.strip()

        return (
            [normalized]
            if normalized
            else []
        )

    if isinstance(
        raw_value,
        (list, tuple, set, frozenset),
    ):
        return _deduplicate_strings(
            [
                str(value).strip()
                for value in raw_value
                if str(value).strip()
            ]
        )

    normalized = str(
        raw_value
    ).strip()

    return (
        [normalized]
        if normalized
        else []
    )


def extract_cheese_fat_content(
    product: Mapping[str, Any],
) -> Any:
    """
    구조화된 지방 함량 정보를 추출한다.
    """
    return (
        product.get("fat_content")
        or product.get("fat_percentage")
        or product.get("milk_fat")
        or product.get("fat")
    )


def extract_cheese_rind_type(
    product: Mapping[str, Any],
) -> str | None:
    """
    외피 또는 Rind 정보를 추출한다.
    """
    raw_value = (
        product.get("rind_type")
        or product.get("rind")
        or product.get("cheese_rind")
    )

    if raw_value is None:
        return None

    normalized = str(
        raw_value
    ).strip()

    return normalized or None


def build_cheese_attributes(
    *,
    product: Mapping[str, Any],
    parse_result: CheeseParseResult,
) -> dict[str, Any]:
    """
    Cheese Parser 결과와 Registry 정보를
    FoodKnowledgeResult.attributes용 dict로 변환한다.

    이 함수는 데이터 변환만 수행하며 점수, 추천 이유,
    경고 정책 또는 최종 결과를 계산하지 않는다.
    """
    if not isinstance(
        product,
        Mapping,
    ):
        raise TypeError(
            "product must be a Mapping"
        )

    if not isinstance(
        parse_result,
        CheeseParseResult,
    ):
        raise TypeError(
            "parse_result must be CheeseParseResult"
        )

    attributes: dict[str, Any] = {
        "product_name": (
            extract_cheese_product_name(
                product
            )
        ),
        "cheese_type": parse_result.cheese_type,
        "milk_source": parse_result.milk_source,
        "origin": parse_result.origin,
        "country": extract_cheese_country_text(
            product=product,
            parse_result=parse_result,
        ),
        "country_code": (
            extract_cheese_country_code(
                product=product,
                parse_result=parse_result,
            )
        ),
        "texture": parse_result.texture,
        "aging": parse_result.aging,
        "weight": extract_cheese_weight(
            product
        ),
        "storage_type": (
            extract_cheese_storage_type(
                product
            )
        ),
        "packaging_type": (
            extract_cheese_packaging_type(
                product
            )
        ),
        "pasteurization": (
            extract_cheese_pasteurization(
                product
            )
        ),
        "certifications": (
            extract_cheese_certifications(
                product
            )
        ),
        "fat_content": (
            extract_cheese_fat_content(
                product
            )
        ),
        "rind_type": extract_cheese_rind_type(
            product
        ),
        "confidence": parse_result.confidence,
        "cheese_type_confidence": (
            parse_result
            .cheese_type_confidence
        ),
        "milk_source_confidence": (
            parse_result
            .milk_source_confidence
        ),
        "origin_confidence": (
            parse_result.origin_confidence
        ),
        "texture_confidence": (
            parse_result.texture_confidence
        ),
        "aging_confidence": (
            parse_result.aging_confidence
        ),
        "detected_keywords": list(
            parse_result.detected_keywords
        ),
        "parser_warnings": list(
            parse_result.warnings
        ),
        "matched_field_count": (
            parse_result.matched_field_count
        ),
        "is_complete": (
            parse_result.is_complete
        ),
        "is_usable": parse_result.is_usable,
    }

    if (
        parse_result.cheese_type_match
        is not None
    ):
        cheese_type = (
            parse_result
            .cheese_type_match
            .entry
        )

        attributes.update(
            {
                "cheese_type_registry_key": (
                    cheese_type.registry_key
                ),
                "cheese_type_category": (
                    cheese_type.type_category
                ),
                "cheese_type_score": (
                    cheese_type.score
                ),
                "cheese_type_premium": (
                    cheese_type.premium
                ),
                "cheese_type_flavor_score": (
                    cheese_type.flavor_score
                ),
                "cheese_type_versatility_score": (
                    cheese_type
                    .versatility_score
                ),
                "cheese_type_typical_uses": list(
                    cheese_type.typical_uses
                ),
                "cheese_type_description": (
                    cheese_type.description
                ),
            }
        )

    if (
        parse_result.milk_source_match
        is not None
    ):
        milk_source = (
            parse_result
            .milk_source_match
            .entry
        )

        attributes.update(
            {
                "milk_source_registry_key": (
                    milk_source.registry_key
                ),
                "milk_source_category": (
                    milk_source.source_category
                ),
                "milk_source_score": (
                    milk_source.score
                ),
                "milk_source_premium": (
                    milk_source.premium
                ),
                "milk_source_richness_score": (
                    milk_source.richness_score
                ),
                "milk_source_availability_score": (
                    milk_source
                    .availability_score
                ),
                "milk_source_description": (
                    milk_source.description
                ),
            }
        )

    if parse_result.origin_match is not None:
        origin = (
            parse_result
            .origin_match
            .entry
        )

        attributes.update(
            {
                "origin_registry_key": (
                    origin.registry_key
                ),
                "origin_country_code": (
                    origin.country_code
                ),
                "origin_score": origin.score,
                "origin_premium": origin.premium,
                "origin_tradition_score": (
                    origin.tradition_score
                ),
                "origin_description": (
                    origin.description
                ),
            }
        )

    if parse_result.texture_match is not None:
        texture = (
            parse_result
            .texture_match
            .entry
        )

        attributes.update(
            {
                "texture_registry_key": (
                    texture.registry_key
                ),
                "texture_category": (
                    texture.texture_category
                ),
                "texture_score": texture.score,
                "texture_premium": (
                    texture.premium
                ),
                "texture_firmness_score": (
                    texture.firmness_score
                ),
                "texture_moisture_score": (
                    texture.moisture_score
                ),
                "texture_description": (
                    texture.description
                ),
            }
        )

    if parse_result.aging_match is not None:
        aging = (
            parse_result
            .aging_match
            .entry
        )

        attributes.update(
            {
                "aging_registry_key": (
                    aging.registry_key
                ),
                "aging_category": (
                    aging.aging_category
                ),
                "aging_score": aging.score,
                "aging_premium": aging.premium,
                "aging_minimum_months": (
                    aging.minimum_months
                ),
                "aging_maximum_months": (
                    aging.maximum_months
                ),
                "aging_flavor_intensity": (
                    aging.flavor_intensity
                ),
                "aging_description": (
                    aging.description
                ),
            }
        )

    return attributes


def _deduplicate_strings(
    values: list[str],
) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        normalized = str(
            value
        ).strip()

        if (
            not normalized
            or normalized in seen
        ):
            continue

        seen.add(normalized)
        result.append(normalized)

    return result


__all__ = [
    "build_cheese_attributes",
    "extract_cheese_product_name",
    "extract_cheese_country_text",
    "extract_cheese_country_code",
    "extract_cheese_weight",
    "extract_cheese_storage_type",
    "extract_cheese_packaging_type",
    "extract_cheese_pasteurization",
    "extract_cheese_certifications",
    "extract_cheese_fat_content",
    "extract_cheese_rind_type",
]
