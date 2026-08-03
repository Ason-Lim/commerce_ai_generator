from __future__ import annotations

import hashlib
from typing import Any


def _clean_text(
    value: Any,
) -> str:
    if value is None:
        return ""

    return str(
        value
    ).strip()


def get_compare_identity(
    item: dict | None,
    display: dict | None = None,
) -> str:
    """비교담기 전용 상품 Identity.

    우선순위:
    1. 실제 상품 URL
    2. 플랫폼 + 판매처 + 상품명 + 가격 + 중량
    """

    item = item or {}
    display = display or {}

    product_url = _clean_text(
        item.get("product_url")
        or item.get("url")
        or item.get("link")
        or item.get("product_link")
        or item.get("detail_url")
        or item.get("landing_url")
    )

    if product_url:
        return f"url::{product_url}"

    platform = _clean_text(
        item.get("platform_name")
        or item.get("platform")
        or item.get("mall_name")
        or item.get("source")
        or display.get("platform_name")
    ).lower()

    seller = _clean_text(
        item.get("seller_name")
        or item.get("seller")
        or display.get("seller_name")
        or display.get("seller_display")
        or display.get("seller_text")
    ).lower()

    product_name = _clean_text(
        item.get("product_name")
        or item.get("raw_name")
        or item.get("title")
        or display.get("name")
    ).lower()

    price = (
        item.get("coupon_applied_price")
        or item.get("member_price")
        or item.get("sale_price")
        or item.get("price")
        or item.get("lprice")
        or display.get("coupon_applied_price")
        or display.get("member_price")
        or display.get("price")
        or 0
    )

    weight = _clean_text(
        item.get("weight_text")
        or display.get("weight_text")
    ).lower()

    return (
        f"fallback::{platform}::{seller}::"
        f"{product_name}::{price}::{weight}"
    )


def build_compare_widget_key(
    item: dict | None,
    *,
    section: str = "main",
    generation: int = 0,
    display: dict | None = None,
) -> str:
    """Streamlit 비교 체크박스용 안정적인 key."""

    identity = get_compare_identity(
        item,
        display,
    )

    digest = hashlib.sha1(
        identity.encode("utf-8")
    ).hexdigest()[:12]

    return (
        f"compare_select_"
        f"{int(generation or 0)}_"
        f"{section}_"
        f"{digest}"
    )