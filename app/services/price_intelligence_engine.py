from __future__ import annotations

from typing import Any

from app.services.price_engine import (
    calculate_discount_rate,
)

from app.services.recommendation.price_signal_engine import (
    extract_price_signals,
)


def _positive_number(
    *values: Any,
) -> float:
    """첫 번째 양수 값을 float로 반환합니다."""

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


def build_price_intelligence(
    item: dict | None,
) -> dict:
    """
    Hero·상품 카드·비교담기·추천 사유가 함께 사용하는
    공통 가격 신호를 생성합니다.

    이 함수는 네트워크 요청이나 DB 갱신을 하지 않습니다.
    이미 수집·보강된 item 데이터만 정규화합니다.
    """

    source = item or {}

    signals = extract_price_signals(
        source
    )

    sale_price = _positive_number(
        source.get("final_price"),
        source.get("sale_price"),
        source.get("discounted_price"),
        source.get("current_price"),
        source.get("selling_price"),
        source.get("salePrice"),
        source.get("lprice"),
        source.get("price"),
        source.get("effective_price"),
        signals.get("price"),
    )

    original_price = _positive_number(
        source.get("original_price"),
        source.get("regular_price"),
        source.get("list_price"),
        source.get("consumer_price"),
        source.get("retail_price"),
        source.get("before_discount_price"),
        source.get("high_price"),
        source.get("hprice"),
        source.get("highPrice"),
        source.get("originalPrice"),
        source.get("regularPrice"),
        source.get("listPrice"),
        source.get("base_price"),
        source.get("market_price"),
        signals.get("original_price"),
    )

    member_price = _positive_number(
        source.get("member_price"),
        source.get("membership_price"),
        source.get("member_sale_price"),
        source.get("member_discount_price"),
        signals.get("member_price"),
    )

    coupon_amount = _positive_number(
        source.get("coupon_amount"),
        source.get("coupon_discount_amount"),
        source.get("coupon_discount"),
        source.get("benefit_amount"),
        signals.get("coupon_amount"),
    )

    coupon_applied_price = _positive_number(
        source.get("coupon_applied_price"),
        source.get("coupon_price"),
        source.get("benefit_price"),
        source.get("max_benefit_price"),
        source.get("maximum_benefit_price"),
        source.get("final_coupon_price"),
        signals.get("coupon_applied_price"),
    )

    price_per_100g = _positive_number(
        source.get("price_per_100g"),
        source.get("unit_price_100g"),
        source.get("unit_price_per_100g"),
        source.get("price_100g"),
        source.get("unit_price"),
        signals.get("price_per_100g"),
    )

    discount_rate = _positive_number(
        source.get("final_discount_rate"),
        source.get("discount_rate"),
        source.get("sale_rate"),
        source.get("discount_percent"),
        signals.get("discount_rate"),
    )

    if (
        discount_rate <= 0
        and original_price > 0
        and sale_price > 0
        and original_price > sale_price
    ):
        discount_rate = float(
            calculate_discount_rate(
                original_price,
                sale_price,
            )
            or 0
        )

    price_candidates = [
        (
            "판매가",
            sale_price,
        ),
        (
            "멤버십 할인가",
            member_price,
        ),
        (
            "쿠폰 적용가",
            coupon_applied_price,
        ),
    ]

    price_candidates = [
        (
            label,
            value,
        )
        for label, value in price_candidates
        if value > 0
    ]

    if price_candidates:
        ai_price_label, ai_price = min(
            price_candidates,
            key=lambda pair: pair[1],
        )

    else:
        ai_price_label = "가격 확인 필요"
        ai_price = 0.0

    has_coupon = bool(
        source.get("has_coupon")
        or source.get("coupon_available")
        or source.get("coupon_name")
        or source.get("coupon_text")
        or coupon_amount > 0
        or coupon_applied_price > 0
        or signals.get("has_coupon")
    )

    confidence = 0

    if sale_price > 0:
        confidence += 35

    if original_price > 0:
        confidence += 25

    if member_price > 0:
        confidence += 15

    if coupon_applied_price > 0:
        confidence += 15

    if discount_rate > 0:
        confidence += 10

    return {
        "original_price": original_price,
        "sale_price": sale_price,
        "member_price": member_price,
        "coupon_amount": coupon_amount,
        "coupon_applied_price": coupon_applied_price,
        "price_per_100g": price_per_100g,
        "discount_rate": round(
            discount_rate,
            1,
        ),
        "has_coupon": has_coupon,
        "ai_price": ai_price,
        "ai_price_label": ai_price_label,
        "confidence": min(
            confidence,
            100,
        ),
    }


def apply_price_intelligence(
    item: dict,
) -> dict:
    """
    공통 가격 신호를 item의 표준 필드에 저장합니다.
    반환값은 build_price_intelligence()의 결과입니다.
    """

    result = build_price_intelligence(
        item
    )

    field_mapping = {
        "original_price": "original_price",
        "sale_price": "sale_price",
        "member_price": "member_price",
        "coupon_amount": "coupon_amount",
        "coupon_applied_price": "coupon_applied_price",
        "price_per_100g": "price_per_100g",
        "discount_rate": "discount_rate",
        "has_coupon": "has_coupon",
        "ai_price": "ai_estimated_price",
    }

    for result_key, item_key in field_mapping.items():
        value = result.get(
            result_key
        )

        if isinstance(
            value,
            bool,
        ):
            if value:
                item[item_key] = value

        elif value:
            item[item_key] = value

    if result.get(
        "discount_rate"
    ):
        item["final_discount_rate"] = (
            result["discount_rate"]
        )

    item["_price_intelligence_v9"] = (
        result
    )

    return result
