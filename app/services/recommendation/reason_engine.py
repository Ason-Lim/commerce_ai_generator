from .score_engine import (
    calculate_ai_scores,
    get_brix_value,
)

from .price_signal_engine import (
    extract_price_signals,
)

def add_ranked_reason(
    reasons,
    text,
    weight,
):
    """추천 사유를 중요도와 함께 추가"""
    if not text:
        return

    reasons.append({
        "text": text,
        "weight": weight,
    })

def adjust_reason_weight_by_priority(
    base_weight,
    reason_type,
    priority,
):
    """추천 모드에 따라 추천 사유 가중치를 조정합니다."""

    base_priority = str(
        priority or "trust"
    ).replace(
        "_adaptive",
        "",
    )

    boosts = {
        "price": {
            "discount": 18,
            "coupon": 16,
            "unit_price": 14,
            "delivery": 4,
        },
        "quality": {
            "brix": 20,
            "cert": 16,
            "premium": 14,
            "review": 6,
        },
        "mix": {
            "discount": 8,
            "brix": 8,
            "delivery": 6,
            "review": 6,
            "cert": 6,
        },
        "trust": {
            "review": 16,
            "cert": 14,
            "platform": 8,
        },
        "revisit": {
            "delivery": 10,
            "platform": 8,
            "discount": 6,
        },
    }

    return (
        base_weight
        + boosts.get(
            base_priority,
            {},
        ).get(
            reason_type,
            0,
        )
    )


def finalize_ranked_reasons(
    reasons,
    limit=5,
):
    """중복 제거 후 중요도순으로 추천 이유를 반환합니다."""

    unique = {}

    for reason in reasons:
        text = reason.get("text")
        weight = reason.get(
            "weight",
            0,
        )

        if not text:
            continue

        if (
            text not in unique
            or weight > unique[text]
        ):
            unique[text] = weight

    ranked = sorted(
        unique.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    return [
        text
        for text, _ in ranked[:limit]
    ]

def classify_recommendation_type(item, priority="trust"):

    if priority == "revisit":
        return (
            "🛍️ 함께 보면 좋은 상품",
            "이전에 관심을 보였던 상품과 함께 비교해볼 만한 상품이에요"
        )

    base_priority = str(priority or "trust").replace("_adaptive", "")

    if base_priority == "quality":
        return (
            "🍬 품질 추천",
            "당도와 품질 신호를 우선으로 본 상품이에요"
        )

    if base_priority == "trust":
        return (
            "✅ 신뢰 추천",
            "리뷰와 평점 등 검증 신호를 우선으로 본 상품이에요"
        )

    if base_priority == "price":
        return (
            "💰 가성비 추천",
            "가격 비교 기준이 좋은 상품이에요"
        )

    if base_priority == "exploration":
        return (
            "🧭 탐색 추천",
            "아직 잘 알려지지 않은 좋은 상품이에요"
        )

    if base_priority == "discovery":
        return (
            "💎 발견 추천",
            "일부 사용자가 반응하기 시작한 숨은 상품이에요"
        )

    if base_priority == "mix":
        return (
            "✨ 오늘의 베스트",
            "맛, 가격, 안심 구매 기준을 균형 있게 반영한 추천이에요"
        )

    return (
        "✨ 균형 추천",
        "가격과 품질의 균형이 좋아요"
    )


def build_reason_list(item, priority="trust"):
    """상품별 고객용 추천 사유 생성: 중요도 기반 자동 정렬"""

    scores = item.get("_ai_scores")

    if scores is None:
        scores = calculate_ai_scores(
            item,
            priority=priority,
        )

    reasons = []

    base_priority = str(priority or "trust").replace("_adaptive", "")

    # 1. 당도/품질
    brix = get_brix_value(item)

    if brix >= 16:
        add_ranked_reason(
            reasons,
            f"🍯 {brix:.0f}brix 고당도 수치가 확인된 상품이에요",
            adjust_reason_weight_by_priority(
            100,
            "brix",
            priority,
            ),
        )
    elif brix >= 15:
        add_ranked_reason(
            reasons,
            f"🍯 {brix:.0f}brix 고당도 수치가 확인된 상품이에요",
            adjust_reason_weight_by_priority(
                92,
                "brix",
                priority,
            ),
        )
    elif brix >= 13:
        add_ranked_reason(
            reasons,
            f"🍬 {brix:.0f}brix 당도 정보가 있어 맛 기준 비교가 가능해요",
            adjust_reason_weight_by_priority(
                80,
                "brix",
                priority,
            ),
        )
    elif item.get("is_high_brix"):
        add_ranked_reason(
            reasons,
            "🍎 고당도 문구가 확인된 상품이에요",
            adjust_reason_weight_by_priority(
                72,
                "brix",
                priority,
            ),
        )

    # 2. 가격/혜택
    price_signals = extract_price_signals(
        item
    )

    discount_rate = price_signals.get(
        "discount_rate",
        0.0,
    )

    coupon_amount = price_signals.get(
        "coupon_amount",
        0.0,
    )

    price_per_100g = price_signals.get(
        "price_per_100g",
        0.0,
    )

    has_coupon = bool(
        price_signals.get(
            "has_coupon",
            False,
        )
    )

    try:
        discount_rate_value = float(discount_rate or 0)
        if discount_rate_value >= 60:
            add_ranked_reason(
                reasons,
                f"🔥 현재 약 {discount_rate_value:.0f}% 할인으로 가격 메리트가 커요",
                98,
            )
        elif discount_rate_value >= 30:
            add_ranked_reason(
                reasons,
                f"💰 현재 약 {discount_rate_value:.0f}% 할인 신호가 있어요",
                88,
            )
    except Exception:
        pass

    try:
        coupon_amount_value = float(coupon_amount or 0)
        if coupon_amount_value >= 1000:
            add_ranked_reason(
                reasons,
                f"🎫 쿠폰 {int(coupon_amount_value):,}원 혜택이 있어요",
                adjust_reason_weight_by_priority(
                    86,
                    "coupon",
                    priority,
                ),
            )
        elif has_coupon:
            add_ranked_reason(
                reasons,
                "🎟️ 쿠폰/특가 혜택이 확인돼요",
                adjust_reason_weight_by_priority(
                    76,
                    "coupon",
                    priority,
                ),
            )
    except Exception:
        pass

    try:
        if price_per_100g and float(price_per_100g) > 0:
            add_ranked_reason(
                reasons,
                f"⚖️ 100g당 약 {int(float(price_per_100g)):,}원 기준으로 비교했어요",
                adjust_reason_weight_by_priority(
                    78,
                    "price",
                    priority,
                ),
            )
    except Exception:
        pass

    # 3. 인증/프리미엄/선물
    certs = item.get("food_certification_labels") or []
    attrs = item.get("food_attributes") or []
    name_text = str(item.get("product_name") or "")

    if isinstance(certs, list):
        if "GAP" in certs:
            add_ranked_reason(
                reasons,
                "🌿 GAP 인증 신호가 확인된 상품이에요",
                adjust_reason_weight_by_priority(
                    90,
                    "cert",
                    priority,
                ),  
            )
        if "유기농" in certs:
            add_ranked_reason(
                reasons,
                "🌱 유기농 인증 신호가 확인된 상품이에요",
                adjust_reason_weight_by_priority(
                    90,
                    "cert",
                    priority,
                ), 
            )
        if "무농약" in certs:
            add_ranked_reason(
                reasons,
                "🥬 무농약 품질 신호가 확인된 상품이에요",
                adjust_reason_weight_by_priority(
                    88,
                    "cert",
                    priority,
                ),
            )

    if "gift" in attrs:
        add_ranked_reason(
            reasons,
            "🎁 선물용으로 보기 좋은 상품이에요",
            adjust_reason_weight_by_priority(
                82,
                "gift",
                priority,
            ),
        )

    if any(word in name_text for word in ["프리미엄", "특품", "정품", "고급"]):
        add_ranked_reason(
            reasons,
            "👑 프리미엄·특품 계열 품질 신호가 있어요",
            adjust_reason_weight_by_priority(
                84,
                "premium",
                priority,
            ),
        )

    # 4. 배송/판매처
    platform_name = str(item.get("platform_name") or item.get("platform") or "")
    seller_name = str(item.get("seller_name") or "")

    if "마켓컬리" in platform_name or "컬리" in seller_name:
        add_ranked_reason(
            reasons,
            "🌙 새벽배송이 가능해 빠르게 받아볼 수 있어요",
            adjust_reason_weight_by_priority(
                76,
                "delivery",
                priority,
            ),
        )
    elif "쿠팡" in platform_name or "coupang" in platform_name.lower():
        add_ranked_reason(
            reasons,
            "🚀 빠른배송이 가능해 배송 대기 부담이 적어요",
            adjust_reason_weight_by_priority(
                74,
                "delivery",
                priority,
            ),
        )

    # 5. 리뷰/사용자 반응
    review_count = item.get("review_count")
    rating = item.get("rating")

    try:
        review_count_value = int(review_count or 0)
        if review_count_value >= 1000:
            add_ranked_reason(
                reasons,
                f"💬 리뷰 {review_count_value:,}개 이상으로 구매 반응이 충분해요",
                adjust_reason_weight_by_priority(
                    84,
                    "review",
                    priority,
                ),
            )
        elif review_count_value >= 500:
            add_ranked_reason(
                reasons,
                f"💬 리뷰 {review_count_value:,}개 이상 누적된 상품이에요",
                adjust_reason_weight_by_priority(
                    78,
                    "review",
                    priority,
                ),
            )
    except Exception:
        pass

    try:
        rating_value = float(rating or 0)
        if rating_value >= 4.7:
            add_ranked_reason(
                reasons,
                f"⭐ 별점 {rating_value:.1f}점으로 만족도 신호가 좋아요",
                adjust_reason_weight_by_priority(
                    84,
                    "review",
                    priority,
                ),
            )
        elif rating_value >= 4.5:
            add_ranked_reason(
                reasons,
                f"⭐ 별점 {rating_value:.1f}점으로 만족도가 높아요",
                adjust_reason_weight_by_priority(
                    78,
                    "review",
                    priority,
                ),
            )
    except Exception:
        pass

    # 6. 탐색/발견 모드
    impression_count = item.get("impression_count") or 0
    click_count = item.get("click_count") or 0
    ctr_pct = item.get("ctr_pct") or 0

    try:
        ctr_pct = float(ctr_pct or 0)
    except Exception:
        ctr_pct = 0

    if base_priority == "exploration":
        add_ranked_reason(
            reasons,
            "🧭 아직 많이 노출되지 않은 탐색 추천 후보예요",
            adjust_reason_weight_by_priority(
                90,
                "exploration",
                priority,
            ),
        )
    elif base_priority == "discovery":
        hidden_gem_score = calculate_hidden_gem_score(item)
        if hidden_gem_score >= 60:
            add_ranked_reason(
                reasons,
                "💎 숨은 인기 상품 후보예요",
                adjust_reason_weight_by_priority(
                    90,
                    "discovery",
                    priority,
                ),
            )

    if base_priority in ("exploration", "discovery"):
        add_ranked_reason(
            reasons,
            f"노출 {int(impression_count or 0)}회 · 클릭 {int(click_count or 0)}회",
            adjust_reason_weight_by_priority(
                64,
                "exploration",
                priority,
            ),
        )

        if ctr_pct > 0:
            add_ranked_reason(
                reasons,
                f"클릭 반응률 {ctr_pct:.1f}%",
                adjust_reason_weight_by_priority(
                    70,
                    "exploration",
                    priority,
                ),
            )

    # 7. fallback
    if not reasons:
        price_score = float(scores.get("price", 0) or 0)
        quality_score = float(scores.get("quality", 0) or 0)

        if price_score >= quality_score:
            add_ranked_reason(
                reasons,
                "💰 가격 조건을 우선 고려한 추천이에요",
                adjust_reason_weight_by_priority(
                    50,
                    "fallback",
                    priority,
                ),
            )
        else:
            add_ranked_reason(
                reasons,
                "⭐ 품질과 가격을 함께 고려한 추천이에요",
                adjust_reason_weight_by_priority(
                    50,
                    "fallback",
                    priority,
                ),
            )

    return finalize_ranked_reasons(reasons, limit=5)

