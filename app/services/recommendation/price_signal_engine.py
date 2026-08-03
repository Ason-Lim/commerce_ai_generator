"""
Price Signal Engine

추천 이유와 비교 엔진이 사용할 최소 가격·혜택 신호를 추출합니다.

UI 전용 structure_product_display()에 의존하지 않고
상품 원본 필드에서 필요한 값만 안전하게 읽습니다.
"""

from __future__ import annotations

from typing import Any, Dict


def safe_number(
    value: Any,
    default: float = 0.0,
) -> float:
    """
    숫자, 숫자 문자열, 콤마 포함 문자열을 안전하게 float로 변환합니다.
    """
    try:
        if value is None:
            return float(default)

        if isinstance(value, str):
            value = (
                value.strip()
                .replace(",", "")
                .replace("%", "")
                .replace("원", "")
            )

            if not value:
                return float(default)

        return float(value)

    except (TypeError, ValueError):
        return float(default)


def first_positive_number(
    *values: Any,
    default: float = 0.0,
) -> float:
    """
    전달된 값 중 첫 번째 양수를 반환합니다.
    """
    for value in values:
        number = safe_number(
            value,
            0.0,
        )

        if number > 0:
            return number

    return float(default)


def has_coupon_text_signal(
    item: Dict[str, Any],
) -> bool:
    """
    상품 필드와 텍스트에서 쿠폰·할인·특가 신호를 확인합니다.
    """
    if not isinstance(item, dict):
        return False

    explicit_fields = [
        "coupon_name",
        "coupon_text",
        "promotion_text",
        "benefit_text",
        "discount_text",
    ]

    if any(
        item.get(field)
        for field in explicit_fields
    ):
        return True

    raw_text = " ".join(
        str(item.get(key) or "")
        for key in [
            "product_name",
            "raw_name",
            "title",
            "description",
            "summary",
            "benefit_text",
            "price_text",
            "discount_text",
        ]
    )

    return any(
        token in raw_text
        for token in [
            "쿠폰",
            "할인",
            "특가",
            "혜택가",
        ]
    )


def extract_price_signals(
    item: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """
    추천 이유와 비교 엔진에서 사용할 가격 신호를 반환합니다.

    반환 필드:
    - price
    - original_price
    - member_price
    - discount_rate
    - coupon_amount
    - coupon_applied_price
    - price_per_100g
    - has_coupon
    """
    item = item or {}

    price = first_positive_number(
        item.get("final_price"),
        item.get("sale_price"),
        item.get("discounted_price"),
        item.get("lprice"),
        item.get("price"),
        item.get("effective_price"),
        item.get("member_price"),
        item.get("ai_estimated_price"),
    )

    original_price = first_positive_number(
        item.get("original_price"),
        item.get("regular_price"),
        item.get("list_price"),
        item.get("high_price"),
    )

    member_price = first_positive_number(
        item.get("member_price"),
        item.get("membership_price"),
    )

    coupon_amount = first_positive_number(
        item.get("coupon_amount"),
        item.get("coupon_discount_amount"),
        item.get("coupon_discount"),
        item.get("benefit_amount"),
    )

    coupon_applied_price = first_positive_number(
        item.get("coupon_applied_price"),
        item.get("coupon_price"),
        item.get("benefit_price"),
    )

    price_per_100g = first_positive_number(
        item.get("price_per_100g"),
        item.get("unit_price_100g"),
        item.get("price_100g"),
    )

    discount_rate = first_positive_number(
        item.get("final_discount_rate"),
        item.get("discount_rate"),
        item.get("sale_rate"),
        item.get("discount_percent"),
    )

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
            2,
        )

    explicit_coupon_flag = bool(
        item.get("has_coupon")
        or item.get("coupon_available")
    )

    has_coupon = bool(
        explicit_coupon_flag
        or coupon_amount > 0
        or coupon_applied_price > 0
        or has_coupon_text_signal(item)
    )

    return {
        "price": price,
        "original_price": original_price,
        "member_price": member_price,
        "discount_rate": discount_rate,
        "coupon_amount": coupon_amount,
        "coupon_applied_price": coupon_applied_price,
        "price_per_100g": price_per_100g,
        "has_coupon": has_coupon,
    }
