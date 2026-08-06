from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.herb_spice.parser_models import (
    HerbSpiceParseResult,
)


def extract_herb_spice_product_name(
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


def extract_herb_spice_country_text(
    *,
    product: Mapping[str, Any],
    parse_result: HerbSpiceParseResult,
) -> str | None:
    """
    구조화된 국가 또는 원산지 텍스트를 우선 사용한다.

    명시값이 없으면 Origin Registry의 country_name을 사용한다.
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


def extract_herb_spice_country_code(
    *,
    product: Mapping[str, Any],
    parse_result: HerbSpiceParseResult,
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


def extract_herb_spice_weight(
    product: Mapping[str, Any],
) -> Any:
    """중량, 용량 또는 수량 정보를 원본 형태로 보존한다."""
    return (
        product.get("weight")
        or product.get("net_weight")
        or product.get("weight_text")
        or product.get("volume")
        or product.get("quantity")
        or product.get("size")
    )


def extract_herb_spice_packaging_type(
    product: Mapping[str, Any],
) -> str | None:
    """병, 파우치, 지퍼백 등 포장 형태를 추출한다."""
    raw_value = (
        product.get("packaging_type")
        or product.get("package_type")
        or product.get("container_type")
        or product.get("packaging")
    )

    if raw_value is None:
        return None

    normalized = str(raw_value).strip()

    return normalized or None


def extract_herb_spice_certifications(
    product: Mapping[str, Any],
) -> list[str]:
    """인증 및 품질 표시를 중복 없는 문자열 목록으로 변환한다."""
    raw_value = (
        product.get("certifications")
        or product.get("certification")
        or product.get("certificates")
        or product.get("labels")
        or product.get("quality_labels")
    )

    return _normalize_string_list(raw_value)


def extract_herb_spice_flavor_notes(
    product: Mapping[str, Any],
) -> list[str]:
    """
    구조화된 향미 또는 아로마 노트를 문자열 목록으로 변환한다.

    Registry의 canonical flavor_profile과 별도로
    상품에 표시된 원문 정보를 보존한다.
    """
    raw_value = (
        product.get("flavor_notes")
        or product.get("flavour_notes")
        or product.get("aroma_notes")
        or product.get("tasting_notes")
        or product.get("flavors")
    )

    return _normalize_string_list(
        raw_value,
        split_separators=(
            ",",
            "/",
            "|",
        ),
    )


def extract_herb_spice_additives(
    product: Mapping[str, Any],
) -> list[str]:
    """첨가물 또는 혼합 성분 표시를 문자열 목록으로 변환한다."""
    raw_value = (
        product.get("additives")
        or product.get("additive")
        or product.get("added_ingredients")
        or product.get("additional_ingredients")
    )

    return _normalize_string_list(
        raw_value,
        split_separators=(
            ",",
            "/",
            "|",
        ),
    )


def extract_herb_spice_organic_status(
    product: Mapping[str, Any],
) -> bool | None:
    """
    유기농 여부를 구조화 필드에서만 추출한다.

    상품명이나 인증 목록으로 추론하지 않는다.
    """
    return _extract_optional_boolean(
        product=product,
        field_names=(
            "organic",
            "is_organic",
            "organic_status",
        ),
        true_values={
            "true",
            "yes",
            "y",
            "1",
            "organic",
            "유기농",
        },
        false_values={
            "false",
            "no",
            "n",
            "0",
            "non-organic",
            "non organic",
            "일반",
        },
    )


def extract_herb_spice_salt_added(
    product: Mapping[str, Any],
) -> bool | None:
    """소금 첨가 여부를 구조화 필드에서 추출한다."""
    return _extract_optional_boolean(
        product=product,
        field_names=(
            "salt_added",
            "contains_salt",
            "with_salt",
            "is_salted",
        ),
        true_values={
            "true",
            "yes",
            "y",
            "1",
            "salted",
            "with salt",
            "소금첨가",
            "가염",
        },
        false_values={
            "false",
            "no",
            "n",
            "0",
            "unsalted",
            "without salt",
            "무염",
        },
    )


def build_herb_spice_attributes(
    *,
    product: Mapping[str, Any],
    parse_result: HerbSpiceParseResult,
) -> dict[str, Any]:
    """
    HerbSpiceParseResult와 구조화된 상품 정보를 결합하여
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
    - Rule 또는 추천 이유 생성
    - Provider orchestration
    """
    if not isinstance(product, Mapping):
        raise TypeError(
            "product must be a Mapping"
        )

    if not isinstance(
        parse_result,
        HerbSpiceParseResult,
    ):
        raise TypeError(
            "parse_result must be "
            "HerbSpiceParseResult"
        )

    attributes: dict[str, Any] = {
        "product_name": (
            extract_herb_spice_product_name(
                product
            )
        ),
        "classification": (
            parse_result.classification
        ),
        "ingredient": parse_result.ingredient,
        "origin": parse_result.origin,
        "form": parse_result.form,
        "usage": parse_result.usage,
        "country": (
            extract_herb_spice_country_text(
                product=product,
                parse_result=parse_result,
            )
        ),
        "country_code": (
            extract_herb_spice_country_code(
                product=product,
                parse_result=parse_result,
            )
        ),
        "weight": extract_herb_spice_weight(
            product
        ),
        "packaging_type": (
            extract_herb_spice_packaging_type(
                product
            )
        ),
        "certifications": (
            extract_herb_spice_certifications(
                product
            )
        ),
        "flavor_notes": (
            extract_herb_spice_flavor_notes(
                product
            )
        ),
        "additives": (
            extract_herb_spice_additives(
                product
            )
        ),
        "organic": (
            extract_herb_spice_organic_status(
                product
            )
        ),
        "salt_added": (
            extract_herb_spice_salt_added(
                product
            )
        ),
        "confidence": parse_result.confidence,
        "classification_confidence": (
            parse_result
            .classification_confidence
        ),
        "ingredient_confidence": (
            parse_result
            .ingredient_confidence
        ),
        "origin_confidence": (
            parse_result.origin_confidence
        ),
        "form_confidence": (
            parse_result.form_confidence
        ),
        "usage_confidence": (
            parse_result.usage_confidence
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
        "is_complete": parse_result.is_complete,
        "is_usable": parse_result.is_usable,
        "has_ingredient_conflict": (
            parse_result
            .has_ingredient_conflict
        ),
    }

    _add_herb_spice_registry_metadata(
        attributes=attributes,
        parse_result=parse_result,
    )

    return attributes


def _add_herb_spice_registry_metadata(
    *,
    attributes: dict[str, Any],
    parse_result: HerbSpiceParseResult,
) -> None:
    """탐지된 Registry Entry metadata를 attributes에 복사한다."""
    selected_ingredient_match: Any = None

    if parse_result.classification == "herb":
        selected_ingredient_match = (
            parse_result.herb_match
        )
    elif parse_result.classification == "spice":
        selected_ingredient_match = (
            parse_result.spice_match
        )

    if selected_ingredient_match is not None:
        entry = selected_ingredient_match.entry

        attributes.update(
            {
                "ingredient_registry_key": (
                    entry.registry_key
                ),
                "ingredient_score": entry.score,
                "ingredient_premium": (
                    entry.premium
                ),
                "ingredient_botanical_name": (
                    entry.botanical_name
                ),
                "ingredient_plant_part": (
                    entry.plant_part
                ),
                "ingredient_flavor_profile": (
                    entry.flavor_profile
                ),
                "ingredient_description": (
                    entry.description
                ),
            }
        )

        if parse_result.classification == "herb":
            attributes.update(
                {
                    "herb_fresh_available": (
                        entry.fresh_available
                    ),
                    "herb_dried_available": (
                        entry.dried_available
                    ),
                }
            )

        if parse_result.classification == "spice":
            attributes.update(
                {
                    "spice_heat_level": (
                        entry.heat_level
                    ),
                    "spice_pungent": (
                        entry.pungent
                    ),
                }
            )

    if parse_result.origin_match is not None:
        entry = parse_result.origin_match.entry

        attributes.update(
            {
                "origin_registry_key": (
                    entry.registry_key
                ),
                "origin_score": entry.score,
                "origin_premium": entry.premium,
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

    if parse_result.form_match is not None:
        entry = parse_result.form_match.entry

        attributes.update(
            {
                "form_registry_key": (
                    entry.registry_key
                ),
                "form_score": entry.score,
                "form_premium": entry.premium,
                "form_category": (
                    entry.form_category
                ),
                "form_dried": entry.dried,
                "form_ground": entry.ground,
                "form_whole": entry.whole,
                "form_fresh": entry.fresh,
                "form_description": (
                    entry.description
                ),
            }
        )

    if parse_result.usage_match is not None:
        entry = parse_result.usage_match.entry

        attributes.update(
            {
                "usage_registry_key": (
                    entry.registry_key
                ),
                "usage_score": entry.score,
                "usage_premium": entry.premium,
                "usage_category": (
                    entry.usage_category
                ),
                "usage_dry_heat": (
                    entry.dry_heat
                ),
                "usage_wet_cooking": (
                    entry.wet_cooking
                ),
                "usage_finishing": (
                    entry.finishing
                ),
                "usage_beverage": (
                    entry.beverage
                ),
                "usage_description": (
                    entry.description
                ),
            }
        )


def _extract_optional_boolean(
    *,
    product: Mapping[str, Any],
    field_names: tuple[str, ...],
    true_values: set[str],
    false_values: set[str],
) -> bool | None:
    for field_name in field_names:
        if field_name not in product:
            continue

        raw_value = product[field_name]

        if raw_value is None:
            return None

        if isinstance(raw_value, bool):
            return raw_value

        normalized = str(
            raw_value
        ).strip().casefold()

        if normalized in true_values:
            return True

        if normalized in false_values:
            return False

    return None


def _normalize_string_list(
    raw_value: Any,
    *,
    split_separators: tuple[str, ...] = (),
) -> list[str]:
    if raw_value is None:
        return []

    if isinstance(raw_value, str):
        values = [raw_value]

        for separator in split_separators:
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


def _deduplicate_strings(
    values: list[str],
) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        normalized = str(value).strip()
        key = normalized.casefold()

        if not normalized or key in seen:
            continue

        seen.add(key)
        result.append(normalized)

    return result


__all__ = [
    "build_herb_spice_attributes",
    "extract_herb_spice_additives",
    "extract_herb_spice_certifications",
    "extract_herb_spice_country_code",
    "extract_herb_spice_country_text",
    "extract_herb_spice_flavor_notes",
    "extract_herb_spice_organic_status",
    "extract_herb_spice_packaging_type",
    "extract_herb_spice_product_name",
    "extract_herb_spice_salt_added",
    "extract_herb_spice_weight",
]
