from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any


_PRODUCT_NAME_KEYS = (
    "product_name",
    "name",
    "title",
    "product_title",
    "item_name",
    "display_name",
)

_ORIGIN_KEYS = (
    "origin",
    "country_of_origin",
    "origin_name",
    "production_area",
    "region",
)

_PRICE_KEYS = (
    "price",
    "sale_price",
    "discount_price",
    "final_price",
    "current_price",
)

_WEIGHT_KEYS = (
    "weight",
    "quantity",
    "package_weight",
    "net_weight",
)


def _is_empty(
    value: Any,
) -> bool:
    if value is None:
        return True

    if isinstance(value, str):
        return not value.strip()

    return False


def first_non_empty(
    data: Mapping[str, Any],
    keys: Iterable[str],
    default: Any = None,
) -> Any:
    """
    Mapping에서 지정한 키를 순서대로 확인하고
    첫 번째 유효 값을 반환한다.
    """
    for key in keys:
        value = data.get(key)

        if not _is_empty(value):
            return value

    return default


def extract_product_name(
    product: Mapping[str, Any],
) -> str:
    """
    상품명 후보 필드 중 첫 번째 유효 값을 문자열로 반환한다.
    """
    value = first_non_empty(
        product,
        _PRODUCT_NAME_KEYS,
        default="",
    )

    return str(value).strip()


def extract_origin(
    product: Mapping[str, Any],
) -> str | None:
    """
    원산지 관련 필드에서 값을 추출한다.
    """
    value = first_non_empty(
        product,
        _ORIGIN_KEYS,
    )

    if _is_empty(value):
        return None

    return str(value).strip()


def extract_first_number(
    value: Any,
    default: float | None = None,
) -> float | None:
    """
    문자열 또는 숫자에서 첫 번째 숫자를 추출한다.

    예:
        "당도 14.5 브릭스" -> 14.5
        "12,900원" -> 12900.0
        3500 -> 3500.0
    """
    if value is None:
        return default

    if isinstance(value, bool):
        return default

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).replace(",", "")

    matched = re.search(
        r"[-+]?\d+(?:\.\d+)?",
        text,
    )

    if not matched:
        return default

    try:
        return float(matched.group(0))
    except (TypeError, ValueError):
        return default


def extract_price(
    product: Mapping[str, Any] | Any,
) -> float | None:
    """
    Mapping 또는 단일 값에서 가격을 추출한다.
    """
    if isinstance(product, Mapping):
        value = first_non_empty(
            product,
            _PRICE_KEYS,
        )
    else:
        value = product

    return extract_first_number(value)


def extract_weight_text(
    product: Mapping[str, Any] | Any,
    *,
    fallback_to_product_name: bool = True,
) -> str | None:
    """
    무게 표현이 포함된 원문을 반환한다.
    """
    if not isinstance(product, Mapping):
        if _is_empty(product):
            return None

        return str(product).strip()

    value = first_non_empty(
        product,
        _WEIGHT_KEYS,
    )

    if not _is_empty(value):
        return str(value).strip()

    if fallback_to_product_name:
        product_name = extract_product_name(
            product
        )

        if product_name:
            return product_name

    return None


def extract_weight_grams(
    product: Mapping[str, Any] | Any,
    *,
    fallback_to_product_name: bool = True,
) -> float | None:
    """
    무게를 gram 단위로 변환한다.

    지원 예:
        500g
        1kg
        1.5 kg
        1000그램
        2킬로그램
    """
    text = extract_weight_text(
        product,
        fallback_to_product_name=(
            fallback_to_product_name
        ),
    )

    if not text:
        return None

    normalized = (
        str(text)
        .replace(",", "")
        .strip()
        .lower()
    )

    patterns = (
        (
            r"(?P<value>\d+(?:\.\d+)?)\s*"
            r"(?:kg|킬로그램|킬로)",
            1000.0,
        ),
        (
            r"(?P<value>\d+(?:\.\d+)?)\s*"
            r"(?:g|그램)",
            1.0,
        ),
    )

    for pattern, multiplier in patterns:
        matched = re.search(
            pattern,
            normalized,
            flags=re.IGNORECASE,
        )

        if not matched:
            continue

        try:
            return (
                float(matched.group("value"))
                * multiplier
            )
        except (TypeError, ValueError):
            return None

    return None


__all__ = [
    "extract_first_number",
    "extract_origin",
    "extract_price",
    "extract_product_name",
    "extract_weight_grams",
    "extract_weight_text",
    "first_non_empty",
]
