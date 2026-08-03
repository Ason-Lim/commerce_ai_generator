from __future__ import annotations

import html
import re
from typing import Any, Dict, Iterable, List, Optional

from app.services.market.delivery_policy import (
    build_platform_delivery_policy,
)
from app.services.market.platform_matcher import (
    detect_platform_from_mall_name,
)
from app.services.market.registry import (
    get_platform_config,
)


def _first_value(
    item: Dict[str, Any],
    *keys: str,
    default: Any = None,
) -> Any:
    """여러 후보 키 중 처음 발견되는 유효 값을 반환한다."""

    for key in keys:
        value = item.get(key)

        if value not in (None, ""):
            return value

    return default


def _safe_int(
    value: Any,
) -> Optional[int]:
    """가격·리뷰 수 등을 안전하게 정수로 변환한다."""

    if value in (None, ""):
        return None

    if isinstance(value, bool):
        return int(value)

    try:
        cleaned = re.sub(
            r"[^0-9.-]",
            "",
            str(value),
        )

        if cleaned in ("", ".", "-", "-."):
            return None

        return int(float(cleaned))

    except (TypeError, ValueError):
        return None


def _safe_float(
    value: Any,
) -> Optional[float]:
    """평점·할인율 등을 안전하게 실수로 변환한다."""

    if value in (None, ""):
        return None

    try:
        cleaned = re.sub(
            r"[^0-9.-]",
            "",
            str(value),
        )

        if cleaned in ("", ".", "-", "-."):
            return None

        return float(cleaned)

    except (TypeError, ValueError):
        return None


def _clean_text(
    value: Any,
) -> str:
    """
    네이버 쇼핑 제목의 <b> 태그 등 HTML과
    불필요한 공백을 제거한다.
    """

    if value in (None, ""):
        return ""

    text = html.unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def _normalize_platform_id(
    item: Dict[str, Any],
    platform_hint: Optional[str] = None,
) -> str:
    """
    플랫폼 ID를 결정한다.

    우선순위:
        1. platform_hint
        2. item.platform
        3. 쇼핑몰명 별칭 판별
        4. unknown
    """

    if platform_hint:
        normalized_hint = platform_hint.strip().lower()

        if get_platform_config(normalized_hint):
            return normalized_hint

    raw_platform = _first_value(
        item,
        "platform",
        "platform_id",
        "source",
    )

    if raw_platform:
        normalized_platform = str(
            raw_platform
        ).strip().lower()

        if get_platform_config(normalized_platform):
            return normalized_platform

    mall_name = _first_value(
        item,
        "mall_name",
        "mallName",
        "seller_name",
        "seller",
        "vendorName",
    )

    detected = detect_platform_from_mall_name(
        str(mall_name or "")
    )

    return detected or "unknown"


def _calculate_discount_rate(
    original_price: Optional[int],
    price: Optional[int],
    explicit_discount_rate: Optional[float] = None,
) -> Optional[float]:
    if explicit_discount_rate is not None:
        return max(
            0.0,
            min(100.0, explicit_discount_rate),
        )

    if (
        original_price is None
        or price is None
        or original_price <= 0
        or price >= original_price
    ):
        return None

    discount_rate = (
        (original_price - price)
        / original_price
        * 100.0
    )

    return round(discount_rate, 1)


def _normalize_delivery_type(
    value: Any,
) -> List[str]:
    if value in (None, ""):
        return []

    if isinstance(value, str):
        parts = re.split(
            r"[,|/]",
            value,
        )

        return [
            part.strip()
            for part in parts
            if part.strip()
        ]

    if isinstance(value, (list, tuple, set)):
        return [
            str(part).strip()
            for part in value
            if str(part).strip()
        ]

    return [str(value).strip()]


def normalize_market_item(
    item: Dict[str, Any],
    platform_hint: Optional[str] = None,
    preserve_raw: bool = True,
) -> Dict[str, Any]:
    """
    플랫폼별 상품 데이터를 Commerce AI 공통 구조로 변환한다.

    지원 대상:
        - 네이버쇼핑
        - 쿠팡
        - SSG.COM
        - 오아시스마켓
        - 향후 Registry 등록 플랫폼
        - 알 수 없는 일반 상품 구조
    """

    source_item = dict(item or {})

    platform_id = _normalize_platform_id(
        source_item,
        platform_hint=platform_hint,
    )

    platform_config = get_platform_config(
        platform_id
    )

    product_name = _clean_text(
        _first_value(
            source_item,
            "product_name",
            "productName",
            "title",
            "name",
            "itemName",
            default="",
        )
    )

    price = _safe_int(
        _first_value(
            source_item,
            "price",
            "salePrice",
            "sale_price",
            "lprice",
            "low_price",
            "discountPrice",
            "final_price",
        )
    )

    original_price = _safe_int(
        _first_value(
            source_item,
            "original_price",
            "originalPrice",
            "regularPrice",
            "listPrice",
            "hprice",
            "base_price",
        )
    )

    explicit_discount_rate = _safe_float(
        _first_value(
            source_item,
            "discount_rate",
            "discountRate",
            "discount_percent",
        )
    )

    discount_rate = _calculate_discount_rate(
        original_price=original_price,
        price=price,
        explicit_discount_rate=explicit_discount_rate,
    )

    mall_name = _clean_text(
        _first_value(
            source_item,
            "mall_name",
            "mallName",
            "seller_name",
            "seller",
            "vendorName",
            default=(
                platform_config.display_name
                if platform_config
                else ""
            ),
        )
    )

    product_url = str(
        _first_value(
            source_item,
            "product_url",
            "productUrl",
            "product_link",
            "link",
            "url",
            default="",
        )
        or ""
    ).strip()

    image_url = str(
        _first_value(
            source_item,
            "image_url",
            "imageUrl",
            "productImage",
            "image",
            "thumbnail",
            default="",
        )
        or ""
    ).strip()

    rating = _safe_float(
        _first_value(
            source_item,
            "rating",
            "review_rating",
            "reviewRating",
            "star_score",
            "starScore",
        )
    )

    review_count = _safe_int(
        _first_value(
            source_item,
            "review_count",
            "reviewCount",
            "reviews",
            "purchase_count",
            "purchaseCount",
        )
    )

    category_name = _clean_text(
        _first_value(
            source_item,
            "category_name",
            "categoryName",
            "category",
            "category1",
            default="",
        )
    )

    brand_name = _clean_text(
        _first_value(
            source_item,
            "brand_name",
            "brandName",
            "brand",
            "maker",
            default="",
        )
    )

    source_platform = str(
        _first_value(
            source_item,
            "source_platform",
            default=(
                platform_config.source_platform
                if platform_config
                and platform_config.source_platform
                else platform_id
            ),
        )
        or ""
    ).strip().lower()

    collection_method = str(
        _first_value(
            source_item,
            "collection_method",
            default=(
                platform_config.collector_name
                if platform_config
                and platform_config.collector_name
                else "unknown"
            ),
        )
        or "unknown"
    ).strip()

    delivery_policy = build_platform_delivery_policy(
        platform_id
    )

    source_delivery_type = _normalize_delivery_type(
        _first_value(
            source_item,
            "delivery_type",
            "deliveryType",
        )
    )

    delivery_type = (
        source_delivery_type
        or delivery_policy["delivery_type"]
    )

    normalized: Dict[str, Any] = {
        "platform": platform_id,
        "platform_display_name": (
            platform_config.display_name
            if platform_config
            else mall_name
            or "알 수 없는 판매처"
        ),
        "platform_type": (
            platform_config.platform_type
            if platform_config
            else "unknown"
        ),
        "source_platform": source_platform,
        "collection_method": collection_method,

        "product_name": product_name,
        "brand_name": brand_name,
        "category_name": category_name,
        "mall_name": mall_name,

        "price": price,
        "original_price": original_price,
        "discount_rate": discount_rate,

        "product_url": product_url,
        "image_url": image_url,

        "rating": rating,
        "review_count": review_count,

        "delivery_type": delivery_type,
        "delivery_availability": _first_value(
            source_item,
            "delivery_availability",
            default=delivery_policy[
                "delivery_availability"
            ],
        ),
        "delivery_region_summary": _first_value(
            source_item,
            "delivery_region_summary",
            default=delivery_policy[
                "delivery_region_summary"
            ],
        ),
        "delivery_requires_address_check": bool(
            _first_value(
                source_item,
                "delivery_requires_address_check",
                default=delivery_policy[
                    "delivery_requires_address_check"
                ],
            )
        ),
        "delivery_notice": _first_value(
            source_item,
            "delivery_notice",
            default=delivery_policy[
                "delivery_notice"
            ],
        ),
    }

    if preserve_raw:
        normalized["raw"] = source_item

    return normalized


def normalize_market_items(
    items: Iterable[Dict[str, Any]],
    platform_hint: Optional[str] = None,
    preserve_raw: bool = True,
    skip_empty_name: bool = True,
) -> List[Dict[str, Any]]:
    """복수 상품을 일괄 정규화한다."""

    normalized_items: List[Dict[str, Any]] = []

    for item in items or []:
        normalized = normalize_market_item(
            item,
            platform_hint=platform_hint,
            preserve_raw=preserve_raw,
        )

        if (
            skip_empty_name
            and not normalized.get("product_name")
        ):
            continue

        normalized_items.append(normalized)

    return normalized_items
