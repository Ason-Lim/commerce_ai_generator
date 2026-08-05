from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.olive_oil.parser_models import (
    OliveOilParseResult,
)


def extract_olive_oil_product_name(
    product: Mapping[str, Any],
) -> str:
    """
    상품 Mapping에서 대표 상품명을 추출한다.

    우선순위:
    product_name
    → title
    → name
    → raw_name
    → display_name
    → 빈 문자열
    """
    return str(
        product.get("product_name")
        or product.get("title")
        or product.get("name")
        or product.get("raw_name")
        or product.get("display_name")
        or ""
    ).strip()


def extract_olive_oil_country_text(
    *,
    product: Mapping[str, Any],
    parse_result: "OliveOilParseResult",
) -> str | None:
    """
    구조화된 국가 또는 원산지 텍스트를 우선 사용한다.

    명시값이 없으면 Origin Registry의 canonical_name을 사용한다.
    """
    raw_value = (
        product.get("country")
        or product.get("origin_country")
        or product.get("country_of_origin")
        or product.get("country_name")
    )

    if raw_value is not None:
        normalized = str(raw_value).strip()

        if normalized:
            return normalized

    if parse_result.origin_match is None:
        return None

    canonical_name = (
        parse_result
        .origin_match
        .entry
        .canonical_name
    )

    normalized = str(canonical_name).strip()

    return normalized or None


def extract_olive_oil_country_code(
    *,
    product: Mapping[str, Any],
    parse_result: "OliveOilParseResult",
) -> str | None:
    """
    구조화된 국가 코드를 우선 사용한다.

    명시값이 없으면 Origin Registry의 country_code를 사용한다.
    """
    raw_value = (
        product.get("country_code")
        or product.get("origin_country_code")
    )

    if raw_value is not None:
        normalized = str(
            raw_value
        ).strip().upper()

        if normalized:
            return normalized

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


def extract_olive_oil_volume(
    product: Mapping[str, Any],
) -> Any:
    """
    상품 용량 또는 수량 정보를 추출한다.

    이 단계에서는 단위 변환을 수행하지 않고
    구조화된 원본 값을 보존한다.
    """
    return (
        product.get("volume")
        or product.get("volume_ml")
        or product.get("capacity")
        or product.get("bottle_size")
        or product.get("size")
        or product.get("quantity")
    )


def extract_olive_oil_packaging_type(
    product: Mapping[str, Any],
) -> str | None:
    """
    병, 캔, 틴, 파우치 등 포장 형태를 추출한다.
    """
    raw_value = (
        product.get("packaging_type")
        or product.get("package_type")
        or product.get("container_type")
        or product.get("bottle_type")
        or product.get("format")
    )

    if raw_value is None:
        return None

    normalized = str(raw_value).strip()

    return normalized or None


def extract_olive_oil_certifications(
    product: Mapping[str, Any],
) -> list[str]:
    """
    인증 및 품질 표시를 중복 없는 문자열 목록으로 변환한다.
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
        (
            list,
            tuple,
            set,
            frozenset,
        ),
    ):
        return _deduplicate_strings(
            [
                str(value).strip()
                for value in raw_value
                if str(value).strip()
            ]
        )

    normalized = str(raw_value).strip()

    return (
        [normalized]
        if normalized
        else []
    )


def extract_olive_oil_organic_status(
    product: Mapping[str, Any],
) -> bool | None:
    """
    Organic 여부를 구조화 필드에서 추출한다.

    상품명이나 인증 목록으로 추론하지 않고,
    명시된 구조화 필드만 사용한다.
    """
    for field_name in (
        "organic",
        "is_organic",
        "organic_status",
    ):
        if field_name not in product:
            continue

        raw_value = product[field_name]

        if isinstance(raw_value, bool):
            return raw_value

        normalized = str(
            raw_value
        ).strip().casefold()

        if normalized in {
            "true",
            "yes",
            "y",
            "1",
            "organic",
            "유기농",
        }:
            return True

        if normalized in {
            "false",
            "no",
            "n",
            "0",
            "non-organic",
            "non organic",
            "일반",
        }:
            return False

    return None


def build_olive_oil_attributes(
    *,
    product: Mapping[str, Any],
    parse_result: OliveOilParseResult,
) -> dict[str, Any]:
    """
    OliveOilParseResult와 구조화 상품 정보를 결합하여
    FoodKnowledgeResult.attributes용 dict를 생성한다.

    담당 책임:
    - ParseResult 값 복사
    - 구조화 상품 필드 추출
    - Registry Entry metadata 복사
    - Parser evidence 보존

    담당하지 않는 책임:
    - 상품명 재파싱
    - Registry 재조회
    - Knowledge Score 계산
    - Final Score 계산
    - Rule 생성
    - Provider orchestration
    """
    if not isinstance(product, Mapping):
        raise TypeError(
            "product must be a Mapping"
        )

    if not isinstance(
        parse_result,
        OliveOilParseResult,
    ):
        raise TypeError(
            "parse_result must be OliveOilParseResult"
        )

    attributes: dict[str, Any] = {
        "product_name": (
            extract_olive_oil_product_name(
                product
            )
        ),
        "olive_oil_type": (
            parse_result.olive_oil_type
        ),
        "variety": parse_result.variety,
        "origin": parse_result.origin,
        "processing": parse_result.processing,
        "grade": parse_result.grade,
        "country": (
            extract_olive_oil_country_text(
                product=product,
                parse_result=parse_result,
            )
        ),
        "country_code": (
            extract_olive_oil_country_code(
                product=product,
                parse_result=parse_result,
            )
        ),
        "volume": extract_olive_oil_volume(
            product
        ),
        "packaging_type": (
            extract_olive_oil_packaging_type(
                product
            )
        ),
        "certifications": (
            extract_olive_oil_certifications(
                product
            )
        ),
        "organic": (
            extract_olive_oil_organic_status(
                product
            )
        ),
        "confidence": parse_result.confidence,
        "olive_oil_type_confidence": (
            parse_result
            .olive_oil_type_confidence
        ),
        "variety_confidence": (
            parse_result.variety_confidence
        ),
        "origin_confidence": (
            parse_result.origin_confidence
        ),
        "processing_confidence": (
            parse_result.processing_confidence
        ),
        "grade_confidence": (
            parse_result.grade_confidence
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
        "is_usable": (
            parse_result.is_usable
        ),
    }

    _add_olive_oil_registry_metadata(
        attributes=attributes,
        parse_result=parse_result,
    )

    return attributes


def _add_olive_oil_registry_metadata(
    *,
    attributes: dict[str, Any],
    parse_result: OliveOilParseResult,
) -> None:
    """
    탐지된 Olive Oil Registry Entry metadata를
    attributes에 복사한다.
    """
    if (
        parse_result.olive_oil_type_match
        is not None
    ):
        entry = (
            parse_result
            .olive_oil_type_match
            .entry
        )

        attributes.update(
            {
                "olive_oil_type_registry_key": (
                    entry.registry_key
                ),
                "olive_oil_type_score": (
                    entry.score
                ),
                "olive_oil_type_premium": (
                    entry.premium
                ),
                "olive_oil_type_description": (
                    entry.description
                ),
            }
        )

    if parse_result.variety_match is not None:
        entry = (
            parse_result
            .variety_match
            .entry
        )

        attributes.update(
            {
                "variety_registry_key": (
                    entry.registry_key
                ),
                "variety_score": entry.score,
                "variety_premium": (
                    entry.premium
                ),
                "variety_cultivar_origin": (
                    entry.cultivar_origin
                ),
                "variety_flavor_profile": (
                    entry.flavor_profile
                ),
                "variety_description": (
                    entry.description
                ),
            }
        )

    if parse_result.origin_match is not None:
        entry = (
            parse_result
            .origin_match
            .entry
        )

        attributes.update(
            {
                "origin_registry_key": (
                    entry.registry_key
                ),
                "origin_score": entry.score,
                "origin_premium": (
                    entry.premium
                ),
                "origin_country_code": (
                    entry.country_code
                ),
                "origin_region": entry.region,
                "origin_description": (
                    entry.description
                ),
            }
        )

    if (
        parse_result.processing_match
        is not None
    ):
        entry = (
            parse_result
            .processing_match
            .entry
        )

        attributes.update(
            {
                "processing_registry_key": (
                    entry.registry_key
                ),
                "processing_score": (
                    entry.score
                ),
                "processing_premium": (
                    entry.premium
                ),
                "processing_category": (
                    entry.process_category
                ),
                "processing_mechanical_only": (
                    entry.mechanical_only
                ),
                "processing_cold_extracted": (
                    entry.cold_extracted
                ),
                "processing_refined": (
                    entry.refined
                ),
                "processing_description": (
                    entry.description
                ),
            }
        )

    if parse_result.grade_match is not None:
        entry = (
            parse_result
            .grade_match
            .entry
        )

        attributes.update(
            {
                "grade_registry_key": (
                    entry.registry_key
                ),
                "grade_score": entry.score,
                "grade_premium": (
                    entry.premium
                ),
                "grade_class": (
                    entry.grade_class
                ),
                "grade_virgin": entry.virgin,
                "grade_refined": entry.refined,
                "grade_pomace": entry.pomace,
                "grade_description": (
                    entry.description
                ),
            }
        )


def _deduplicate_strings(
    values: list[str],
) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        normalized = str(value).strip()
        key = normalized.casefold()

        if (
            not normalized
            or key in seen
        ):
            continue

        seen.add(key)
        result.append(normalized)

    return result


__all__ = [
    "extract_olive_oil_product_name",
    "extract_olive_oil_country_text",
    "extract_olive_oil_country_code",
    "extract_olive_oil_volume",
    "extract_olive_oil_packaging_type",
    "extract_olive_oil_certifications",
    "extract_olive_oil_organic_status",
    "build_olive_oil_attributes",
]
