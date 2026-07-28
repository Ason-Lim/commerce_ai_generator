from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.meat.lamb.parser_models import (
    LambParseResult,
)


def extract_lamb_product_name(
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


def extract_lamb_country_text(
    product: Mapping[str, Any],
) -> str | None:
    """
    상품 Mapping에서 원산지 정보를 추출한다.

    원산지를 추론하지 않고 명시된 값만 사용한다.
    """
    raw_country = (
        product.get("country")
        or product.get("origin_country")
        or product.get("country_of_origin")
        or product.get("origin")
    )

    if raw_country is None:
        return None

    country_text = str(
        raw_country
    ).strip()

    return country_text or None


def extract_lamb_country_code(
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


def extract_lamb_weight(
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


def extract_lamb_storage_type(
    product: Mapping[str, Any],
) -> str | None:
    """
    냉장·냉동 등 보관 상태를 추출한다.

    구조화된 상품 필드에 명시된 값만 사용한다.
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


def extract_lamb_certifications(
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

        return (
            [normalized]
            if normalized
            else []
        )

    if isinstance(
        raw_value,
        (list, tuple, set, frozenset),
    ):
        return [
            str(value).strip()
            for value in raw_value
            if str(value).strip()
        ]

    normalized = str(
        raw_value
    ).strip()

    return (
        [normalized]
        if normalized
        else []
    )


def build_lamb_attributes(
    *,
    product: Mapping[str, Any],
    parse_result: LambParseResult,
) -> dict[str, Any]:
    """
    Parser의 표준화 결과와 Registry 정보를
    FoodKnowledgeResult용 attributes로 변환한다.

    이 함수는 값을 변환·정리할 뿐,
    추천 점수나 비즈니스 규칙을 계산하지 않는다.
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
        LambParseResult,
    ):
        raise TypeError(
            "parse_result must be LambParseResult"
        )

    attributes: dict[str, Any] = {
        "product_name": extract_lamb_product_name(
            product
        ),
        "country": extract_lamb_country_text(
            product
        ),
        "country_code": extract_lamb_country_code(
            product
        ),
        "weight": extract_lamb_weight(
            product
        ),
        "storage_type": extract_lamb_storage_type(
            product
        ),
        "certifications": (
            extract_lamb_certifications(
                product
            )
        ),
        "age": parse_result.age,
        "breed": parse_result.breed,
        "cut": parse_result.cut,
        "confidence": parse_result.confidence,
        "age_confidence": (
            parse_result.age_confidence
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
        "is_complete": parse_result.is_complete,
    }

    if parse_result.age_match is not None:
        age = parse_result.age_match.age

        attributes.update(
            {
                "age_registry_key": (
                    age.registry_key
                ),
                "age_category": (
                    age.age_category
                ),
                "age_score": age.score,
                "age_premium": age.premium,
                "age_min_months": (
                    age.min_age_months
                ),
                "age_max_months": (
                    age.max_age_months
                ),
                "age_permanent_incisor_min": (
                    age.permanent_incisor_min
                ),
                "age_permanent_incisor_max": (
                    age.permanent_incisor_max
                ),
                "age_flavor_intensity": (
                    age.flavor_intensity
                ),
                "age_tenderness_level": (
                    age.tenderness_level
                ),
                "age_policy_region": (
                    age.policy_region
                ),
                "age_source_version": (
                    age.source_version
                ),
                "age_description": (
                    age.description
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
                "breed_marbling_score": (
                    breed.marbling_score
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
    "build_lamb_attributes",
    "extract_lamb_product_name",
    "extract_lamb_country_text",
    "extract_lamb_country_code",
    "extract_lamb_weight",
    "extract_lamb_storage_type",
    "extract_lamb_certifications",
]
