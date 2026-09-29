from .score_engine import get_brix_value
from .claim_source import brix_claim_source

from .price_signal_engine import (
    extract_price_signals,
    safe_number,
)

def build_compare_message(item, priority="trust"):
    """비슷한 상품 대비 장점 문구"""

    base_priority = str(priority or "trust").replace("_adaptive", "")

    if base_priority == "exploration":
        return "품질과 가격을 함께 고려한 숨은 후보 상품이에요"

    if base_priority == "discovery":
        return "품질과 가격을 반영한 발견 추천 후보예요"

    messages = []

    brix = get_brix_value(item)

    if brix >= 15:
        messages.append(f"상품명·상세 설명에 {brix:.0f}brix로 표기된 상품이에요" if brix_claim_source(item, brix) == "seller_page_claim" else f"Brix 입력값은 {brix:.0f}이에요. 출처는 확인되지 않았어요")

    elif brix >= 13:
        messages.append(f"상품명·상세 설명에 {brix:.0f}brix로 표기된 상품이에요" if brix_claim_source(item, brix) == "seller_page_claim" else f"Brix 입력값은 {brix:.0f}이에요. 출처는 확인되지 않았어요")

    elif item.get("is_high_brix"):
        messages.append("상품명·상세 설명에 고당도로 표기된 상품이에요" if brix_claim_source(item) == "seller_page_claim" else "고당도 입력값의 출처는 확인되지 않았어요")

    discount_rate = (
        item.get("final_discount_rate")
        or item.get("discount_rate")
        or 0
    )

    try:
        if float(discount_rate) >= 10:
            messages.append("할인율도 함께 고려했어요")
    except Exception:
        pass

    if item.get("price_per_100g") or item.get("unit_price_per_kg"):
        messages.append("단가 기준 비교가 가능한 상품이에요")

    if not messages:
        messages.append("가격과 상품 정보를 함께 비교했어요")

    return " · ".join(messages[:2])

def build_info_chips(item):
    """상품 핵심 비교칩 생성"""

    item = item or {}

    highlight_chips = []
    normal_chips = []

    price_signals = extract_price_signals(
        item
    )

    # ==========================================================
    # 당도
    # ==========================================================
    brix = get_brix_value(
        item
    )

    if brix > 0:
        highlight_chips.append(
            f"🍬 {'상품명·상세 설명 표기' if brix_claim_source(item, brix) == 'seller_page_claim' else '출처 불명 입력'} {brix:g}brix"
        )
    elif item.get("is_high_brix"):
        highlight_chips.append(
            "🍬 상품명·상세 설명 고당도 표기" if brix_claim_source(item) == "seller_page_claim" else "🍬 고당도 입력 출처 불명"
        )

    # ==========================================================
    # 중량
    # ==========================================================
    weight_text = (
        item.get("weight_text")
        or item.get("display_weight")
        or item.get("weight")
        or item.get("product_weight")
        or ""
    )

    weight_text = str(
        weight_text or ""
    ).strip()

    if weight_text:
        normal_chips.append(
            f"📦 {weight_text}"
        )

    # ==========================================================
    # 판매처 / 배송
    # ==========================================================
    seller_name = str(
        item.get("seller_name")
        or ""
    )

    platform_name = str(
        item.get("platform_name")
        or item.get("platform")
        or ""
    )

    if (
        "마켓컬리" in platform_name
        or "컬리" in platform_name
        or "컬리" in seller_name
    ):
        highlight_chips.append(
            "🚚 새벽배송"
        )

    elif "쿠팡" in platform_name:
        highlight_chips.append(
            "🚀 빠른배송"
        )

    elif "네이버" in platform_name:
        normal_chips.append(
            "🏪 네이버 판매처"
        )

    elif seller_name:
        cleaned_seller = (
            seller_name
            .replace("주식회사", "")
            .replace("(주)", "")
            .strip()
        )

        if cleaned_seller:
            normal_chips.append(
                f"🏪 {cleaned_seller[:12]}"
            )

    # ==========================================================
    # 리뷰·평점은 이 상품·옵션·판매 제안과의 연결이 입증되지 않아 표시하지 않습니다.
    # ==========================================================
    # 100g당 가격
    # ==========================================================
    price_per_100g = safe_number(
        price_signals.get(
            "price_per_100g"
        ),
        0.0,
    )

    if price_per_100g > 0:
        normal_chips.append(
            f"⚖️ 100g당 {int(price_per_100g):,}원"
        )

    # ==========================================================
    # 할인율
    # ==========================================================
    discount_rate = safe_number(
        price_signals.get(
            "discount_rate"
        ),
        0.0,
    )

    if discount_rate >= 5:
        normal_chips.append(
            f"🏷️ {discount_rate:.0f}% 할인"
        )

    # ==========================================================
    # 쿠폰 / 특가
    # ==========================================================
    coupon_amount = safe_number(
        price_signals.get(
            "coupon_amount"
        ),
        0.0,
    )

    coupon_applied_price = safe_number(
        price_signals.get(
            "coupon_applied_price"
        ),
        0.0,
    )

    has_coupon = bool(
        price_signals.get(
            "has_coupon",
            False,
        )
    )

    if coupon_amount > 0:
        highlight_chips.append(
            f"🎟️ 쿠폰 {int(coupon_amount):,}원"
        )

    elif coupon_applied_price > 0:
        highlight_chips.append(
            f"🎟️ 쿠폰가 {int(coupon_applied_price):,}원"
        )

    elif has_coupon:
        highlight_chips.append(
            "🎟️ 쿠폰/특가"
        )

    # ==========================================================
    # 중복 제거
    # ==========================================================
    highlight_chips = list(
        dict.fromkeys(
            highlight_chips
        )
    )

    normal_chips = list(
        dict.fromkeys(
            normal_chips
        )
    )

    return (
        highlight_chips,
        normal_chips,
    )
