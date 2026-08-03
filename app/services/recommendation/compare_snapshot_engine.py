from __future__ import annotations

from copy import deepcopy

from app.services.common.weight_utils import (
    get_weight_text_from_item,
    normalize_weight_to_grams,
)

from .price_signal_engine import (
    extract_price_signals,
)

from .score_engine import (
    get_brix_value,
)


def _first_positive(
    *values,
) -> float:
    for value in values:
        try:
            number = float(
                value or 0
            )

            if number > 0:
                return number
        except (TypeError, ValueError):
            continue

    return 0.0


def build_compare_snapshot(
    item: dict | None,
    display: dict | None = None,
) -> dict:
    """
    비교담기용 정규화 스냅샷.

    우선순위:
    1. 상품 카드에서 이미 계산된 display
    2. price_signal_engine 결과
    3. 원본 item
    """

    source = deepcopy(
        item or {}
    )

    display = dict(
        display or {}
    )

    price_signals = extract_price_signals(
        source
    )

    snapshot = dict(
        source
    )

    price = _first_positive(
        display.get("price"),
        display.get("ai_estimated_price"),
        display.get("coupon_applied_price"),
        price_signals.get("price"),
        source.get("final_price"),
        source.get("sale_price"),
        source.get("lprice"),
        source.get("price"),
    )

    original_price = _first_positive(
        display.get("original_price"),
        display.get("regular_price"),
        display.get("list_price"),

        price_signals.get("original_price"),
        price_signals.get("regular_price"),
        price_signals.get("list_price"),

        source.get("original_price"),
        source.get("regular_price"),
        source.get("list_price"),
        source.get("retail_price"),
        source.get("base_price"),
        source.get("market_price"),
    )

    discount_rate = _first_positive(
        display.get("discount_rate"),
        price_signals.get("discount_rate"),
        source.get("final_discount_rate"),
        source.get("discount_rate"),
    )
    
    # 할인율이 직접 제공되지 않았지만
    # 정상가와 판매가가 있으면 안전하게 역산합니다.
    if (
        discount_rate <= 0
        and original_price > 0
        and price > 0
        and original_price > price
    ):
        discount_rate = round(
            (
                original_price - price
            )
            / original_price
            * 100,
            1,
        )

    coupon_amount = _first_positive(
        display.get("coupon_amount"),
        price_signals.get("coupon_amount"),
        source.get("coupon_amount"),
    )

    coupon_applied_price = _first_positive(
        display.get("coupon_applied_price"),
        price_signals.get("coupon_applied_price"),
        source.get("coupon_applied_price"),
    )

    price_per_100g = _first_positive(
        display.get("price_per_100g"),
        price_signals.get("price_per_100g"),
        source.get("unit_price_100g"),
        source.get("unit_price_per_100g"),
        source.get("price_100g"),
        source.get("price_per_100g"),
    )

    weight_text = (
        display.get("weight_text")
        or get_weight_text_from_item(source)
    )

    # 단가가 없지만 가격과 중량이 있으면 역산
    if not price_per_100g:
        weight_g = normalize_weight_to_grams(
            weight_text
        )

        if price > 0 and weight_g > 0:
            price_per_100g = round(
                price / (weight_g / 100),
                2,
            )

    snapshot.update({
        "_product_identity_key": source.get(
            "_product_identity_key",
            "",
        ),

        "product_name": (
            display.get("name")
            or source.get("product_name")
            or source.get("title")
            or ""
        ),

        "product_url": (
            source.get("product_url")
            or source.get("url")
            or source.get("link")
            or source.get("product_link")
            or source.get("detail_url")
            or ""
        ),

        "platform": (
            source.get("platform")
            or source.get("source")
            or ""
        ),

        "platform_name": (
            display.get("platform_name")
            or source.get("platform_name")
            or source.get("mall_name")
            or source.get("platform")
            or ""
        ),

        "seller_name": (
            display.get("seller_name")
            or source.get("seller_name")
            or source.get("seller")
            or ""
        ),

        "price": price,

        "sale_price": _first_positive(
            source.get("sale_price"),
            display.get("price"),
            price,
        ),

        "original_price": original_price,

        "member_price": _first_positive(
            display.get("member_price"),
            price_signals.get("member_price"),
            source.get("member_price"),
        ),

        "discount_rate": discount_rate,
        "coupon_amount": coupon_amount,
        "coupon_applied_price": coupon_applied_price,
        "price_per_100g": price_per_100g,

        "has_coupon": bool(
            display.get("has_coupon")
            or price_signals.get("has_coupon")
            or source.get("has_coupon")
            or source.get("coupon_name")
            or source.get("coupon_text")
        ),

        "coupon_name": (
            source.get("coupon_name")
            or source.get("coupon_text")
            or ""
        ),

        "brix": _first_positive(
            display.get("brix"),
            display.get("brix_value"),
            get_brix_value(source),
        ),

        "fruit_brix": _first_positive(
            source.get("fruit_brix"),
            source.get("brix"),
            get_brix_value(source),
        ),

        "weight_text": weight_text,

        "food_certification_labels": (
            source.get("food_certification_labels")
            or source.get("certification_labels")
            or source.get("certifications")
            or []
        ),
    })

    return snapshot