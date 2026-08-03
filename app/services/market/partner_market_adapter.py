from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from app.services.market.delivery_policy import (
    build_platform_delivery_policy,
)
from app.services.market.platform_matcher import (
    detect_platform_from_mall_name,
)
from app.services.market.registry import (
    require_platform_config,
)


def _get_first(
    item: Dict[str, Any],
    *keys: str,
    default: Any = None,
) -> Any:
    for key in keys:
        value = item.get(key)

        if value not in (None, ""):
            return value

    return default


def _safe_int(value: Any) -> Optional[int]:
    if value in (None, ""):
        return None

    try:
        cleaned = str(value).replace(",", "").strip()
        return int(float(cleaned))
    except (TypeError, ValueError):
        return None


def extract_partner_market_items(
    naver_items: Iterable[Dict[str, Any]],
    target_platform: str,
) -> List[Dict[str, Any]]:
    """
    네이버 쇼핑 검색 결과에서 제휴형 플랫폼 상품만 분리한다.

    현재 지원:
        - ssg
        - oasis
    """

    platform_config = require_platform_config(
        target_platform
    )

    if platform_config.collector_type != "partner_filter":
        raise ValueError(
            "platform is not configured as partner_filter: "
            f"{target_platform}"
        )

    results: List[Dict[str, Any]] = []

    delivery_policy = build_platform_delivery_policy(
        platform_config.id
    )

    for source_item in naver_items:
        item = dict(source_item)

        mall_name = _get_first(
            item,
            "mallName",
            "mall_name",
            "platform_name",
            "seller",
        )

        detected_platform = detect_platform_from_mall_name(
            str(mall_name or "")
        )

        if detected_platform != platform_config.id:
            continue

        normalized = dict(item)

        normalized.update(
            {
                "platform": platform_config.id,
                "platform_display_name": (
                    platform_config.display_name
                ),
                "platform_type": (
                    platform_config.platform_type
                ),
                "source_platform": (
                    platform_config.source_platform
                    or "naver"
                ),
                "collection_method": (
                    platform_config.collector_name
                    or "partner_filter"
                ),
                "mall_name": mall_name,
                "product_name": _get_first(
                    item,
                    "product_name",
                    "title",
                    "name",
                    default="",
                ),
                "price": _safe_int(
                    _get_first(
                        item,
                        "price",
                        "lprice",
                        "low_price",
                    )
                ),
                "original_price": _safe_int(
                    _get_first(
                        item,
                        "original_price",
                        "hprice",
                    )
                ),
                "product_url": _get_first(
                    item,
                    "product_url",
                    "link",
                    "url",
                    default="",
                ),
                "image_url": _get_first(
                    item,
                    "image_url",
                    "image",
                    default="",
                ),
                **delivery_policy,
            }
        )

        results.append(normalized)

    return results
