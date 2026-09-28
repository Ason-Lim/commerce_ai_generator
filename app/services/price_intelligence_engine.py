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


def _positive_number_with_source(*candidates: tuple[str, Any]) -> tuple[float, str]:
    """Return the value and field from the same first-positive selection."""
    for field, value in candidates:
        number = _positive_number(value)
        if number > 0:
            return number, field
    return 0.0, "UNKNOWN"


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

    sale_price, sale_source = _positive_number_with_source(
        *((f"item.{key}", source.get(key)) for key in (
            "final_price", "sale_price", "discounted_price", "current_price",
            "selling_price", "salePrice", "lprice", "price", "effective_price")),
        ("extracted.price", signals.get("price")),
    )

    original_price, original_source = _positive_number_with_source(
        *((f"item.{key}", source.get(key)) for key in (
            "original_price", "regular_price", "list_price", "consumer_price",
            "retail_price", "before_discount_price", "high_price", "hprice",
            "highPrice", "originalPrice", "regularPrice", "listPrice",
            "base_price", "market_price")),
        ("extracted.original_price", signals.get("original_price")),
    )

    member_price, member_source = _positive_number_with_source(
        *((f"item.{key}", source.get(key)) for key in (
            "member_price", "membership_price", "member_sale_price", "member_discount_price")),
        ("extracted.member_price", signals.get("member_price")),
    )

    coupon_amount = _positive_number(
        source.get("coupon_amount"),
        source.get("coupon_discount_amount"),
        source.get("coupon_discount"),
        source.get("benefit_amount"),
        signals.get("coupon_amount"),
    )

    coupon_applied_price, coupon_source = _positive_number_with_source(
        *((f"item.{key}", source.get(key)) for key in (
            "coupon_applied_price", "coupon_price", "benefit_price",
            "max_benefit_price", "maximum_benefit_price", "final_coupon_price")),
        ("extracted.coupon_applied_price", signals.get("coupon_applied_price")),
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
            sale_source,
        ),
        (
            "멤버십 할인가",
            member_price,
            member_source,
        ),
        (
            "쿠폰 적용가",
            coupon_applied_price,
            coupon_source,
        ),
    ]

    price_candidates = [
        (
            label,
            value,
            field,
        )
        for label, value, field in price_candidates
        if value > 0
    ]

    if price_candidates:
        ai_price_label, ai_price, ai_source = min(
            price_candidates,
            key=lambda pair: pair[1],
        )

    else:
        ai_price_label = "가격 확인 필요"
        ai_price = 0.0
        ai_source = "UNKNOWN"

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

    source_fields = {
        "sale_price": sale_source,
        "original_price": original_source,
        "coupon_applied_price": coupon_source,
        "member_price": member_source,
    }
    source_fields["ai_price"] = ai_source

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
        "selected_source_fields": source_fields,
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
