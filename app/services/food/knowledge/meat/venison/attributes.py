from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.meat.venison.parser_models import (
    VenisonParseResult,
)


def extract_venison_product_name(
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


def extract_venison_country_text(
    product: Mapping[str, Any],
) -> str | None:
    """
    상품 Mapping에서 명시된 원산지 정보를 추출한다.

    상품명에서 원산지를 추론하지 않는다.
    """
    raw_country = (
        product.get("country")
        or product.get("origin_country")
        or product.get("country_of_origin")
        or product.get("origin")
    )

    if raw_country is None:
        return None

    country_text = str(raw_country).strip()

    return country_text or None


def extract_venison_country_code(
    product: Mapping[str, Any],
) -> str | None:
    """
    상품 Mapping에서 명시된 국가 코드를 추출한다.
    """
    raw_country_code = (
        product.get("country_code")
        or product.get("origin_country_code")
    )

    if raw_country_code is None:
        return None

    country_code = str(
        raw_country_code
    ).strip().upper()

    return country_code or None


def extract_venison_weight(
    product: Mapping[str, Any],
) -> Any:
    """
    상품 Mapping에서 중량 또는 수량 값을 추출한다.

    단위 변환이나 상품명 기반 추론은 수행하지 않는다.
    """
    for field_name in (
        "weight",
        "quantity",
        "weight_text",
        "net_weight",
    ):
        if field_name in product:
            value = product.get(field_name)

            if value is not None:
                return value

    return None


def extract_venison_storage_type(
    product: Mapping[str, Any],
) -> str | None:
    """
    구조화된 상품 필드에서 냉장·냉동 등 보관 상태를 추출한다.
    """
    raw_storage_type = (
        product.get("storage_type")
        or product.get("storage")
        or product.get("temperature_type")
        or product.get("freshness_type")
    )

    if raw_storage_type is None:
        return None

    storage_type = str(
        raw_storage_type
    ).strip()

    return storage_type or None


def extract_venison_certifications(
    product: Mapping[str, Any],
) -> list[str]:
    """
    인증 및 표시 정보를 문자열 목록으로 변환한다.
    """
    raw_value = (
        product.get("certifications")
        or product.get("certification")
        or product.get("labels")
        or product.get("certificates")
    )

    if raw_value is None:
        return []

    if isinstance(raw_value, str):
        normalized = raw_value.strip()

        return [normalized] if normalized else []

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

    normalized = str(raw_value).strip()

    return [normalized] if normalized else []


def extract_venison_bone_status(
    product: Mapping[str, Any],
) -> str | None:
    """
    구조화된 상품 필드에서 뼈 포함 여부를 추출한다.

    반환값은 명시된 원문을 정리한 문자열이며,
    상품명으로부터 boneless/bone-in을 추론하지 않는다.
    """
    raw_value = (
        product.get("bone_status")
        or product.get("bone_type")
        or product.get("bone")
    )

    if raw_value is None:
        return None

    normalized = str(raw_value).strip()

    return normalized or None


def extract_venison_skin_status(
    product: Mapping[str, Any],
) -> str | None:
    """
    구조화된 상품 필드에서 껍질 포함 여부를 추출한다.
    """
    raw_value = (
        product.get("skin_status")
        or product.get("skin_type")
        or product.get("skin")
    )

    if raw_value is None:
        return None

    normalized = str(raw_value).strip()

    return normalized or None


def _deduplicate_strings(
    values: list[str],
) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        text = str(value).strip()
        normalized = text.casefold()

        if not text or normalized in seen:
            continue

        seen.add(normalized)
        result.append(text)

    return result


def build_venison_attributes(
    *,
    product: Mapping[str, Any],
    parse_result: VenisonParseResult,
) -> dict[str, Any]:
    """
    Venison Parser의 표준화 결과와 Registry 정보를
    FoodKnowledgeResult용 attributes로 변환한다.

    이 함수는 값을 추출하고 정리할 뿐,
    추천 점수나 비즈니스 규칙을 계산하지 않는다.
    """
    if not isinstance(product, Mapping):
        raise TypeError(
            "product must be a Mapping"
        )

    if not isinstance(
        parse_result,
        VenisonParseResult,
    ):
        raise TypeError(
            "parse_result must be VenisonParseResult"
        )

    attributes: dict[str, Any] = {
        "product_name": (
            extract_venison_product_name(
                product
            )
        ),
        "country": (
            extract_venison_country_text(
                product
            )
        ),
        "country_code": (
            extract_venison_country_code(
                product
            )
        ),
        "weight": extract_venison_weight(
            product
        ),
        "storage_type": (
            extract_venison_storage_type(
                product
            )
        ),
        "certifications": (
            extract_venison_certifications(
                product
            )
        ),
        "bone_status": (
            extract_venison_bone_status(
                product
            )
        ),
        "skin_status": (
            extract_venison_skin_status(
                product
            )
        ),
        "venison_type": (
            parse_result.venison_type
        ),
        "breed": parse_result.breed,
        "cut": parse_result.cut,
        "confidence": parse_result.confidence,
        "venison_type_confidence": (
            parse_result.venison_type_confidence
        ),
        "breed_confidence": (
            parse_result.breed_confidence
        ),
        "cut_confidence": (
            parse_result.cut_confidence
        ),
        "detected_keywords": list(
            parse_result.detected_keywords
        ),
        "warnings": list(
            parse_result.warnings
        ),
        "is_complete": (
            parse_result.is_complete
        ),
        "is_usable": parse_result.is_usable,
    }

    if (
        parse_result.venison_type_match
        is not None
    ):
        venison_type = (
            parse_result
            .venison_type_match
            .venison_type
        )

        attributes.update(
            {
                "venison_type_registry_key": (
                    venison_type.registry_key
                ),
                "venison_type_category": (
                    venison_type.type_category
                ),
                "venison_type_score": (
                    venison_type.score
                ),
                "venison_type_premium": (
                    venison_type.premium
                ),
                "venison_type_flavor_intensity": (
                    venison_type.flavor_intensity
                ),
                "venison_type_tenderness_level": (
                    venison_type.tenderness_level
                ),
                "venison_type_typical_uses": list(
                    venison_type.typical_uses
                ),
                "venison_type_description": (
                    venison_type.description
                ),
            }
        )

    if parse_result.breed_match is not None:
        breed = parse_result.breed_match.breed

        attributes.update(
            {
                "breed_registry_key": (
                    breed.registry_key
                ),
                "breed_english_name": (
                    breed.english_name
                ),
                "breed_origin_country": (
                    breed.origin_country
                ),
                "breed_type": breed.breed_type,
                "breed_score": breed.score,
                "breed_premium": breed.premium,
                "breed_flavor_score": (
                    breed.flavor_score
                ),
                "breed_tenderness_score": (
                    breed.tenderness_score
                ),
                "breed_growth_score": (
                    breed.growth_score
                ),
                "breed_rarity_score": (
                    breed.rarity_score
                ),
                "breed_description": (
                    breed.description
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
                "cut_english_name": (
                    cut.english_name
                ),
                "cut_group": cut.cut_group,
                "cut_score": cut.score,
                "cut_premium": cut.premium,
                "cut_tenderness_score": (
                    cut.tenderness_score
                ),
                "cut_flavor_score": (
                    cut.flavor_score
                ),
                "cut_fat_score": (
                    cut.fat_score
                ),
                "cut_yield_score": (
                    cut.yield_score
                ),
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
    "build_venison_attributes",
    "extract_venison_product_name",
    "extract_venison_country_text",
    "extract_venison_country_code",
    "extract_venison_weight",
    "extract_venison_storage_type",
    "extract_venison_certifications",
    "extract_venison_bone_status",
    "extract_venison_skin_status",
]
