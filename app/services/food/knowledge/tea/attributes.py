from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.tea.parser_models import (
    TeaParseResult,
)


def extract_tea_product_name(
    product: Mapping[str, Any],
) -> str:
    """상품 Mapping에서 대표 상품명을 추출한다."""
    return str(
        product.get("product_name")
        or product.get("title")
        or product.get("name")
        or product.get("raw_name")
        or product.get("display_name")
        or ""
    ).strip()


def extract_tea_country_text(
    *,
    product: Mapping[str, Any],
    parse_result: TeaParseResult,
) -> str | None:
    """
    구조화된 국가 또는 원산지 텍스트를 우선 사용한다.

    명시값이 없으면 Tea Origin Registry의 국가명을 사용한다.
    """
    raw_value = (
        product.get("country")
        or product.get("origin_country")
        or product.get("country_of_origin")
    )

    if raw_value is not None:
        normalized = str(raw_value).strip()

        if normalized:
            return normalized

    if parse_result.origin_match is None:
        return None

    country_name = (
        parse_result
        .origin_match
        .entry
        .country_name
    )

    if country_name is None:
        return None

    normalized = str(country_name).strip()

    return normalized or None


def extract_tea_country_code(
    *,
    product: Mapping[str, Any],
    parse_result: TeaParseResult,
) -> str | None:
    """
    구조화된 국가 코드를 우선 사용한다.

    명시값이 없으면 Tea Origin Registry 값을 사용한다.
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


def extract_tea_weight(
    product: Mapping[str, Any],
) -> Any:
    """상품 중량·용량·수량 정보를 추출한다."""
    return (
        product.get("weight")
        or product.get("net_weight")
        or product.get("weight_text")
        or product.get("volume")
        or product.get("quantity")
        or product.get("size")
    )


def extract_tea_packaging_type(
    product: Mapping[str, Any],
) -> str | None:
    """티백·잎차·분말 등 포장 또는 상품 형태를 추출한다."""
    raw_value = (
        product.get("packaging_type")
        or product.get("package_type")
        or product.get("product_form")
        or product.get("tea_form")
        or product.get("format")
    )

    if raw_value is None:
        return None

    normalized = str(raw_value).strip()

    return normalized or None


def extract_tea_harvest_year(
    product: Mapping[str, Any],
) -> Any:
    """구조화된 수확 연도 또는 생산 연도를 추출한다."""
    return (
        product.get("harvest_year")
        or product.get("harvest")
        or product.get("production_year")
        or product.get("crop_year")
        or product.get("year")
    )


def extract_tea_grade(
    product: Mapping[str, Any],
) -> str | None:
    """구조화된 Tea grade 정보를 추출한다."""
    raw_value = (
        product.get("grade")
        or product.get("tea_grade")
        or product.get("leaf_grade")
        or product.get("quality_grade")
    )

    if raw_value is None:
        return None

    normalized = str(raw_value).strip()

    return normalized or None


def extract_tea_leaf_style(
    product: Mapping[str, Any],
) -> str | None:
    """Whole leaf, broken leaf, powder 등 잎 형태를 추출한다."""
    raw_value = (
        product.get("leaf_style")
        or product.get("leaf_type")
        or product.get("leaf_form")
        or product.get("cut_type")
    )

    if raw_value is None:
        return None

    normalized = str(raw_value).strip()

    return normalized or None


def extract_tea_caffeine_status(
    product: Mapping[str, Any],
) -> str | None:
    """
    디카페인·카페인 프리 등 구조화된 카페인 상태를 추출한다.

    Tea Type만으로 카페인 상태를 추론하지 않는다.
    False도 유효한 명시값이므로 필드 존재 여부로 탐색한다.
    """
    raw_value: Any = None
    found = False

    for field_name in (
        "caffeine_status",
        "caffeine_level",
        "caffeine",
        "decaf",
        "is_decaf",
        "caffeine_free",
    ):
        if field_name in product:
            raw_value = product[field_name]
            found = True
            break

    if not found or raw_value is None:
        return None

    if isinstance(raw_value, bool):
        return (
            "decaf"
            if raw_value
            else "regular"
        )

    normalized = str(raw_value).strip()

    return normalized or None

def extract_tea_certifications(
    product: Mapping[str, Any],
) -> list[str]:
    """인증과 품질 표시를 중복 없는 문자열 목록으로 변환한다."""
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


def extract_tea_flavor_notes(
    product: Mapping[str, Any],
) -> list[str]:
    """
    구조화된 Flavor/Aroma/Tasting Note를 목록으로 변환한다.

    Parser의 단일 canonical flavor와 별개로 상품 원문 note를 보존한다.
    """
    raw_value = (
        product.get("flavor_notes")
        or product.get("flavour_notes")
        or product.get("tasting_notes")
        or product.get("aroma_notes")
        or product.get("flavors")
    )

    if raw_value is None:
        return []

    if isinstance(raw_value, str):
        normalized = raw_value.strip()

        if not normalized:
            return []

        values = [normalized]

        for separator in (
            ",",
            "/",
            "|",
        ):
            split_values: list[str] = []

            for value in values:
                split_values.extend(
                    value.split(separator)
                )

            values = split_values

        return _deduplicate_strings(values)

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


def build_tea_attributes(
    *,
    product: Mapping[str, Any],
    parse_result: TeaParseResult,
) -> dict[str, Any]:
    """
    Tea Parser 결과와 상품 Mapping을 attributes dict로 변환한다.

    이 함수가 담당하는 책임:
    - ParseResult 필드 복사
    - 구조화된 상품 속성 추출
    - Registry Entry metadata 복사
    - Parser evidence 보존

    담당하지 않는 책임:
    - 상품명 재파싱
    - Registry 재조회
    - Knowledge Score 계산
    - Final Score 계산
    - Rule 또는 추천 이유 생성
    - Provider orchestration
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
        TeaParseResult,
    ):
        raise TypeError(
            "parse_result must be TeaParseResult"
        )

    attributes: dict[str, Any] = {
        "product_name": extract_tea_product_name(
            product
        ),
        "tea_type": parse_result.tea_type,
        "origin": parse_result.origin,
        "variety": parse_result.variety,
        "processing": parse_result.processing,
        "oxidation": parse_result.oxidation,
        "flavor": parse_result.flavor,
        "country": extract_tea_country_text(
            product=product,
            parse_result=parse_result,
        ),
        "country_code": extract_tea_country_code(
            product=product,
            parse_result=parse_result,
        ),
        "weight": extract_tea_weight(
            product
        ),
        "packaging_type": (
            extract_tea_packaging_type(
                product
            )
        ),
        "harvest_year": (
            extract_tea_harvest_year(
                product
            )
        ),
        "grade": extract_tea_grade(
            product
        ),
        "leaf_style": (
            extract_tea_leaf_style(
                product
            )
        ),
        "caffeine_status": (
            extract_tea_caffeine_status(
                product
            )
        ),
        "certifications": (
            extract_tea_certifications(
                product
            )
        ),
        "flavor_notes": (
            extract_tea_flavor_notes(
                product
            )
        ),
        "confidence": parse_result.confidence,
        "tea_type_confidence": (
            parse_result.tea_type_confidence
        ),
        "origin_confidence": (
            parse_result.origin_confidence
        ),
        "variety_confidence": (
            parse_result.variety_confidence
        ),
        "processing_confidence": (
            parse_result.processing_confidence
        ),
        "oxidation_confidence": (
            parse_result.oxidation_confidence
        ),
        "flavor_confidence": (
            parse_result.flavor_confidence
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

    _add_tea_registry_metadata(
        attributes=attributes,
        parse_result=parse_result,
    )

    return attributes


def _add_tea_registry_metadata(
    *,
    attributes: dict[str, Any],
    parse_result: TeaParseResult,
) -> None:
    """탐지된 Tea Registry Entry metadata를 attributes에 복사한다."""
    if parse_result.tea_type_match is not None:
        entry = (
            parse_result
            .tea_type_match
            .entry
        )

        attributes.update(
            {
                "tea_type_registry_key": (
                    entry.registry_key
                ),
                "tea_type_score": (
                    entry.score
                ),
                "tea_type_premium": (
                    entry.premium
                ),
                "tea_type_description": (
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
                "origin_score": (
                    entry.score
                ),
                "origin_premium": (
                    entry.premium
                ),
                "origin_country_code": (
                    entry.country_code
                ),
                "origin_country_name": (
                    entry.country_name
                ),
                "origin_region_name": (
                    entry.region_name
                ),
                "origin_description": (
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
                "variety_score": (
                    entry.score
                ),
                "variety_premium": (
                    entry.premium
                ),
                "variety_botanical_name": (
                    entry.botanical_name
                ),
                "variety_kind": (
                    entry.variety_kind
                ),
                "variety_country_code": (
                    entry.country_code
                ),
                "variety_description": (
                    entry.description
                ),
            }
        )

    if parse_result.processing_match is not None:
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
                "processing_heat_fixation": (
                    entry.heat_fixation
                ),
                "processing_microbial_fermentation": (
                    entry.microbial_fermentation
                ),
                "processing_smoke_applied": (
                    entry.smoke_applied
                ),
                "processing_description": (
                    entry.description
                ),
            }
        )

    if parse_result.oxidation_match is not None:
        entry = (
            parse_result
            .oxidation_match
            .entry
        )

        attributes.update(
            {
                "oxidation_registry_key": (
                    entry.registry_key
                ),
                "oxidation_score": (
                    entry.score
                ),
                "oxidation_premium": (
                    entry.premium
                ),
                "oxidation_level": (
                    entry.oxidation_level
                ),
                "oxidation_min_percent": (
                    entry.oxidation_min_percent
                ),
                "oxidation_max_percent": (
                    entry.oxidation_max_percent
                ),
                "oxidation_fully_oxidized": (
                    entry.fully_oxidized
                ),
                "oxidation_description": (
                    entry.description
                ),
            }
        )

    if parse_result.flavor_match is not None:
        entry = (
            parse_result
            .flavor_match
            .entry
        )

        attributes.update(
            {
                "flavor_registry_key": (
                    entry.registry_key
                ),
                "flavor_score": (
                    entry.score
                ),
                "flavor_premium": (
                    entry.premium
                ),
                "flavor_family": (
                    entry.flavor_family
                ),
                "flavor_sensory_dimension": (
                    entry.sensory_dimension
                ),
                "flavor_aroma_dominant": (
                    entry.aroma_dominant
                ),
                "flavor_taste_dominant": (
                    entry.taste_dominant
                ),
                "flavor_description": (
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

        if not normalized:
            continue

        key = normalized.casefold()

        if key in seen:
            continue

        seen.add(key)
        result.append(normalized)

    return result


__all__ = [
    "build_tea_attributes",
    "extract_tea_caffeine_status",
    "extract_tea_certifications",
    "extract_tea_country_code",
    "extract_tea_country_text",
    "extract_tea_flavor_notes",
    "extract_tea_grade",
    "extract_tea_harvest_year",
    "extract_tea_leaf_style",
    "extract_tea_packaging_type",
    "extract_tea_product_name",
    "extract_tea_weight",
]
