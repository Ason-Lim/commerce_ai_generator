from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.coffee.parser_models import (
    CoffeeParseResult,
)


def extract_coffee_product_name(
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


def extract_coffee_country_text(
    *,
    product: Mapping[str, Any],
    parse_result: CoffeeParseResult,
) -> str | None:
    """
    구조화된 원산지 값이 있으면 원문을 우선 사용한다.

    명시값이 없으면 Coffee Origin Registry에서
    탐지한 표준 국가명을 사용한다.
    """
    raw_country = (
        product.get("country")
        or product.get("origin_country")
        or product.get("country_of_origin")
        or product.get("origin")
        or product.get("coffee_origin")
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


def extract_coffee_country_code(
    *,
    product: Mapping[str, Any],
    parse_result: CoffeeParseResult,
) -> str | None:
    """
    명시된 국가 코드를 우선 사용하고,
    없으면 Origin Registry 값을 사용한다.
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


def extract_coffee_weight(
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


def extract_coffee_grind_type(
    product: Mapping[str, Any],
) -> str | None:
    """
    홀빈·분쇄 등 구조화된 분쇄 형태를 추출한다.
    """
    raw_value = (
        product.get("grind_type")
        or product.get("grind")
        or product.get("grinding")
        or product.get("grind_level")
    )

    if raw_value is None:
        return None

    normalized = str(
        raw_value
    ).strip()

    return normalized or None


def extract_coffee_product_form(
    product: Mapping[str, Any],
) -> str | None:
    """
    원두·분쇄·드립백·캡슐 등 상품 형태를 추출한다.
    """
    raw_value = (
        product.get("product_form")
        or product.get("coffee_form")
        or product.get("format")
        or product.get("packaging_type")
        or product.get("package_type")
    )

    if raw_value is None:
        return None

    normalized = str(
        raw_value
    ).strip()

    return normalized or None


def extract_coffee_decaf(
    product: Mapping[str, Any],
) -> bool | None:
    """
    디카페인 여부를 구조화된 값에서 추출한다.
    """
    raw_value = None

    for field_name in (
        "decaf",
        "is_decaf",
        "decaffeinated",
        "caffeine_free",
    ):
        if field_name in product:
            raw_value = product[field_name]
            break

    if raw_value is None:
        return None

    if isinstance(raw_value, bool):
        return raw_value

    normalized = str(
        raw_value
    ).strip().casefold()

    if normalized in {
        "true",
        "1",
        "yes",
        "y",
        "decaf",
        "decaffeinated",
        "디카페인",
        "카페인 제거",
    }:
        return True

    if normalized in {
        "false",
        "0",
        "no",
        "n",
        "regular",
        "일반",
        "카페인",
    }:
        return False

    return None


def extract_coffee_certifications(
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


def extract_coffee_flavor_notes(
    product: Mapping[str, Any],
) -> list[str]:
    """
    구조화된 Flavor/Tasting Note를 문자열 목록으로 변환한다.
    """
    raw_value = (
        product.get("flavor_notes")
        or product.get("tasting_notes")
        or product.get("flavors")
        or product.get("flavour_notes")
    )

    if raw_value is None:
        return []

    if isinstance(raw_value, str):
        normalized = raw_value.strip()

        if not normalized:
            return []

        separators = (
            ",",
            "/",
            "|",
        )

        values = [normalized]

        for separator in separators:
            split_values: list[str] = []

            for value in values:
                split_values.extend(
                    value.split(separator)
                )

            values = split_values

        return _deduplicate_strings(values)

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


def extract_coffee_altitude(
    product: Mapping[str, Any],
) -> Any:
    """
    고도 또는 재배고도 정보를 추출한다.
    """
    return (
        product.get("altitude")
        or product.get("growing_altitude")
        or product.get("elevation")
        or product.get("altitude_m")
    )


def extract_coffee_roast_date(
    product: Mapping[str, Any],
) -> Any:
    """
    로스팅 날짜 정보를 추출한다.
    """
    return (
        product.get("roast_date")
        or product.get("roasted_at")
        or product.get("roasting_date")
        or product.get("manufactured_at")
    )


def build_coffee_attributes(
    *,
    product: Mapping[str, Any],
    parse_result: CoffeeParseResult,
) -> dict[str, Any]:
    """
    Coffee Parser 결과와 Registry 데이터를
    FoodKnowledgeResult.attributes용 dict로 변환한다.

    이 함수는 데이터 변환만 수행한다.

    수행하지 않는 책임:
    - 상품명 재파싱
    - Registry 재조회
    - Knowledge Score 계산
    - Final Score 계산
    - 추천 이유 및 경고 정책 생성
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
        CoffeeParseResult,
    ):
        raise TypeError(
            "parse_result must be CoffeeParseResult"
        )

    attributes: dict[str, Any] = {
        "product_name": (
            extract_coffee_product_name(
                product
            )
        ),
        "bean": parse_result.bean,
        "origin": parse_result.origin,
        "country": extract_coffee_country_text(
            product=product,
            parse_result=parse_result,
        ),
        "country_code": (
            extract_coffee_country_code(
                product=product,
                parse_result=parse_result,
            )
        ),
        "roast": parse_result.roast,
        "process": parse_result.process,
        "weight": extract_coffee_weight(
            product
        ),
        "grind_type": (
            extract_coffee_grind_type(
                product
            )
        ),
        "product_form": (
            extract_coffee_product_form(
                product
            )
        ),
        "decaf": extract_coffee_decaf(
            product
        ),
        "certifications": (
            extract_coffee_certifications(
                product
            )
        ),
        "flavor_notes": (
            extract_coffee_flavor_notes(
                product
            )
        ),
        "altitude": extract_coffee_altitude(
            product
        ),
        "roast_date": (
            extract_coffee_roast_date(
                product
            )
        ),
        "confidence": parse_result.confidence,
        "bean_confidence": (
            parse_result.bean_confidence
        ),
        "origin_confidence": (
            parse_result.origin_confidence
        ),
        "roast_confidence": (
            parse_result.roast_confidence
        ),
        "process_confidence": (
            parse_result.process_confidence
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

    if parse_result.bean_match is not None:
        bean = (
            parse_result
            .bean_match
            .entry
        )

        attributes.update(
            {
                "bean_registry_key": (
                    bean.registry_key
                ),
                "bean_species": bean.species,
                "bean_composition_type": (
                    bean.composition_type
                ),
                "bean_score": bean.score,
                "bean_premium": bean.premium,
                "bean_acidity_score": (
                    bean.acidity_score
                ),
                "bean_body_score": (
                    bean.body_score
                ),
                "bean_aroma_score": (
                    bean.aroma_score
                ),
                "bean_description": (
                    bean.description
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
                "origin_premium": (
                    origin.premium
                ),
                "origin_acidity_score": (
                    origin.acidity_score
                ),
                "origin_body_score": (
                    origin.body_score
                ),
                "origin_aroma_score": (
                    origin.aroma_score
                ),
                "origin_description": (
                    origin.description
                ),
            }
        )

    if parse_result.roast_match is not None:
        roast = (
            parse_result
            .roast_match
            .entry
        )

        attributes.update(
            {
                "roast_registry_key": (
                    roast.registry_key
                ),
                "roast_level": (
                    roast.roast_level
                ),
                "roast_score": roast.score,
                "roast_premium": (
                    roast.premium
                ),
                "roast_acidity_score": (
                    roast.acidity_score
                ),
                "roast_body_score": (
                    roast.body_score
                ),
                "roast_aroma_score": (
                    roast.aroma_score
                ),
                "roast_description": (
                    roast.description
                ),
            }
        )

    if parse_result.process_match is not None:
        process = (
            parse_result
            .process_match
            .entry
        )

        attributes.update(
            {
                "process_registry_key": (
                    process.registry_key
                ),
                "process_category": (
                    process.process_category
                ),
                "process_score": (
                    process.score
                ),
                "process_premium": (
                    process.premium
                ),
                "process_clarity_score": (
                    process.clarity_score
                ),
                "process_sweetness_score": (
                    process.sweetness_score
                ),
                "process_body_score": (
                    process.body_score
                ),
                "process_description": (
                    process.description
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
    "build_coffee_attributes",
    "extract_coffee_product_name",
    "extract_coffee_country_text",
    "extract_coffee_country_code",
    "extract_coffee_weight",
    "extract_coffee_grind_type",
    "extract_coffee_product_form",
    "extract_coffee_decaf",
    "extract_coffee_certifications",
    "extract_coffee_flavor_notes",
    "extract_coffee_altitude",
    "extract_coffee_roast_date",
]
