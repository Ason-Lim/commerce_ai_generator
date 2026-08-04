from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.wine.parser_models import (
    WineParseResult,
)


def extract_wine_product_name(
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


def extract_wine_country_text(
    *,
    product: Mapping[str, Any],
    parse_result: WineParseResult,
) -> str | None:
    """
    구조화된 국가 정보가 있으면 우선 사용하고,
    없으면 Region Registry의 국가명을 사용한다.
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

    if parse_result.region_match is None:
        return None

    country_name = (
        parse_result
        .region_match
        .entry
        .country_name
    )

    if country_name is None:
        return None

    normalized = str(country_name).strip()

    return normalized or None


def extract_wine_country_code(
    *,
    product: Mapping[str, Any],
    parse_result: WineParseResult,
) -> str | None:
    """
    구조화된 국가 코드를 우선 사용하고,
    없으면 Region Registry의 국가 코드를 사용한다.
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

    if parse_result.region_match is None:
        return None

    country_code = (
        parse_result
        .region_match
        .entry
        .country_code
    )

    if country_code is None:
        return None

    normalized = str(
        country_code
    ).strip().upper()

    return normalized or None


def extract_wine_volume(
    product: Mapping[str, Any],
) -> Any:
    """
    병 용량 또는 상품 용량을 추출한다.
    """
    return (
        product.get("volume")
        or product.get("volume_ml")
        or product.get("bottle_size")
        or product.get("size")
        or product.get("capacity")
        or product.get("quantity")
    )


def extract_wine_packaging_type(
    product: Mapping[str, Any],
) -> str | None:
    """
    병, 캔, 박스 등 포장 형태를 추출한다.
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

    normalized = str(
        raw_value
    ).strip()

    return normalized or None


def extract_wine_closure_type(
    product: Mapping[str, Any],
) -> str | None:
    """
    코르크, 스크루캡 등 마개 형태를 추출한다.
    """
    raw_value = (
        product.get("closure_type")
        or product.get("closure")
        or product.get("cap_type")
        or product.get("cork_type")
    )

    if raw_value is None:
        return None

    normalized = str(
        raw_value
    ).strip()

    return normalized or None


def extract_wine_producer(
    product: Mapping[str, Any],
) -> str | None:
    """
    와이너리 또는 생산자 정보를 추출한다.
    """
    raw_value = (
        product.get("producer")
        or product.get("winery")
        or product.get("brand")
        or product.get("estate")
    )

    if raw_value is None:
        return None

    normalized = str(
        raw_value
    ).strip()

    return normalized or None


def extract_wine_certifications(
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

    normalized = str(
        raw_value
    ).strip()

    return [normalized] if normalized else []


def extract_wine_organic_status(
    product: Mapping[str, Any],
) -> bool | None:
    """
    Organic 여부를 구조화 필드에서 추출한다.
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
            "일반",
        }:
            return False

    return None


def extract_wine_biodynamic_status(
    product: Mapping[str, Any],
) -> bool | None:
    """
    Biodynamic 여부를 구조화 필드에서 추출한다.
    """
    for field_name in (
        "biodynamic",
        "is_biodynamic",
        "biodynamic_status",
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
            "biodynamic",
            "바이오다이나믹",
        }:
            return True

        if normalized in {
            "false",
            "no",
            "n",
            "0",
        }:
            return False

    return None


def build_wine_attributes(
    *,
    product: Mapping[str, Any],
    parse_result: WineParseResult,
) -> dict[str, Any]:
    """
    WineParseResult와 구조화 상품 정보를 결합하여
    Wine Attributes를 구성한다.

    Parser를 다시 실행하거나 점수를 계산하지 않는다.
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
        WineParseResult,
    ):
        raise TypeError(
            "parse_result must be WineParseResult"
        )

    attributes: dict[str, Any] = {
        "product_name": extract_wine_product_name(
            product
        ),
        "wine_type": parse_result.wine_type,
        "grape": parse_result.grape,
        "region": parse_result.region,
        "country": extract_wine_country_text(
            product=product,
            parse_result=parse_result,
        ),
        "country_code": extract_wine_country_code(
            product=product,
            parse_result=parse_result,
        ),
        "sweetness": parse_result.sweetness,
        "body": parse_result.body,
        "acidity": parse_result.acidity,
        "vintage": parse_result.vintage,
        "alcohol_percent": (
            parse_result.alcohol_percent
        ),
        "producer": extract_wine_producer(
            product
        ),
        "volume": extract_wine_volume(
            product
        ),
        "packaging_type": (
            extract_wine_packaging_type(
                product
            )
        ),
        "closure_type": (
            extract_wine_closure_type(
                product
            )
        ),
        "certifications": (
            extract_wine_certifications(
                product
            )
        ),
        "organic": (
            extract_wine_organic_status(
                product
            )
        ),
        "biodynamic": (
            extract_wine_biodynamic_status(
                product
            )
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
        "parse_confidence": (
            parse_result.confidence
        ),
    }

    _add_registry_metadata(
        attributes=attributes,
        parse_result=parse_result,
    )

    return attributes


def _add_registry_metadata(
    *,
    attributes: dict[str, Any],
    parse_result: WineParseResult,
) -> None:
    if parse_result.wine_type_match is not None:
        entry = (
            parse_result
            .wine_type_match
            .entry
        )

        attributes.update(
            {
                "wine_type_category": (
                    entry.type_category
                ),
                "wine_type_color_family": (
                    entry.color_family
                ),
                "wine_type_sparkling": (
                    entry.sparkling
                ),
                "wine_type_fortified": (
                    entry.fortified
                ),
                "wine_type_premium": (
                    entry.premium
                ),
            }
        )

    if parse_result.grape_match is not None:
        entry = (
            parse_result
            .grape_match
            .entry
        )

        attributes.update(
            {
                "grape_color": entry.color,
                "grape_species": entry.species,
                "grape_aromatic": (
                    entry.aromatic
                ),
                "grape_premium": entry.premium,
            }
        )

    if parse_result.region_match is not None:
        entry = (
            parse_result
            .region_match
            .entry
        )

        attributes.update(
            {
                "region_appellation": (
                    entry.appellation
                ),
                "region_premium": entry.premium,
            }
        )

    if (
        parse_result.sweetness_match
        is not None
    ):
        entry = (
            parse_result
            .sweetness_match
            .entry
        )

        attributes.update(
            {
                "sweetness_level": (
                    entry.sweetness_level
                ),
                "residual_sugar_min": (
                    entry.residual_sugar_min
                ),
                "residual_sugar_max": (
                    entry.residual_sugar_max
                ),
                "sweetness_premium": (
                    entry.premium
                ),
            }
        )

    if parse_result.body_match is not None:
        entry = (
            parse_result
            .body_match
            .entry
        )

        attributes.update(
            {
                "body_level": entry.body_level,
                "body_premium": entry.premium,
            }
        )

    if parse_result.acidity_match is not None:
        entry = (
            parse_result
            .acidity_match
            .entry
        )

        attributes.update(
            {
                "acidity_level": (
                    entry.acidity_level
                ),
                "acidity_premium": (
                    entry.premium
                ),
            }
        )


def _deduplicate_strings(
    values: list[str],
) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        normalized = str(
            value
        ).strip()

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
    "build_wine_attributes",
    "extract_wine_product_name",
]
