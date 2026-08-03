from app.services.platform_score_engine import enrich_with_platform_scores


def safe_number(value, default=0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def calculate_price_score(item: dict, min_price: float, max_price: float) -> float:
    price = safe_number(item.get("price"), 0)

    if price <= 0:
        return 30

    if max_price <= min_price:
        return 70

    score = 100 - ((price - min_price) / (max_price - min_price) * 100)
    return round(max(20, min(100, score)), 1)


def calculate_quality_signal_score(item: dict) -> float:
    return safe_number(
        item.get("fruit_quality_score")
        or item.get("food_intelligence_score")
        or item.get("v7_quality_score")
        or 50,
        50,
    )


def calculate_market_ai_score_v8(item: dict, min_price: float, max_price: float) -> dict:
    enriched = enrich_with_platform_scores(item)

    food_score = safe_number(enriched.get("food_intelligence_score"), 50)
    price_score = calculate_price_score(enriched, min_price, max_price)
    platform_score = safe_number(enriched.get("platform_boost_score"), 50)
    quality_signal_score = calculate_quality_signal_score(enriched)
    stability_score = 65

    final_score = (
        food_score * 0.35
        + price_score * 0.25
        + platform_score * 0.20
        + quality_signal_score * 0.15
        + stability_score * 0.05
    )

    enriched["v8_food_score"] = round(food_score, 1)
    enriched["v8_price_score"] = round(price_score, 1)
    enriched["v8_platform_score"] = round(platform_score, 1)
    enriched["v8_quality_signal_score"] = round(quality_signal_score, 1)
    enriched["v8_stability_score"] = stability_score
    enriched["v8_final_score"] = round(final_score, 1)

    enriched["v8_score_reason"] = build_v8_score_reason(enriched)

    # 기존 UI 호환
    enriched["v7_final_score"] = enriched["v8_final_score"]
    enriched["final_recommendation_score"] = enriched["v8_final_score"]
    enriched["score"] = enriched["v8_final_score"]
    enriched["adaptive_score"] = enriched["v8_final_score"]

    return enriched


def build_v8_score_reason(item: dict) -> str:
    reasons = []

    food = safe_number(item.get("v8_food_score"), 0)
    price = safe_number(item.get("v8_price_score"), 0)
    platform = item.get("platform")

    if food >= 70:
        reasons.append("식품 품질 신호가 강합니다.")
    elif food >= 55:
        reasons.append("식품 품질 신호가 확인됩니다.")
    else:
        reasons.append("식품 품질 신호는 제한적입니다.")

    if price >= 80:
        reasons.append("가격 경쟁력이 높습니다.")
    elif price >= 55:
        reasons.append("가격은 비교적 무난합니다.")
    else:
        reasons.append("가격은 비교군 대비 높은 편입니다.")

    if platform == "coupang":
        reasons.append("쿠팡의 구매 전환·배송 편의성이 반영되었습니다.")
    elif platform == "naver":
        reasons.append("네이버 쇼핑의 가격 비교 장점이 반영되었습니다.")

    food_reason = item.get("food_intelligence_reason")
    if food_reason:
        reasons.append(food_reason)

    return " ".join(reasons)


def rank_market_items_v8(items):
    valid_items = [item for item in items if isinstance(item, dict)]

    prices = [
        safe_number(item.get("price"), 0)
        for item in valid_items
        if safe_number(item.get("price"), 0) > 0
    ]

    min_price = min(prices) if prices else 0
    max_price = max(prices) if prices else 0

    ranked = [
        calculate_market_ai_score_v8(item, min_price, max_price)
        for item in valid_items
    ]

    ranked.sort(
        key=lambda x: (
            safe_number(x.get("v8_final_score"), 0),
            safe_number(x.get("v8_food_score"), 0),
            safe_number(x.get("v8_price_score"), 0),
        ),
        reverse=True,
    )

    for index, item in enumerate(ranked, start=1):
        item["v8_rank"] = index
        item["v7_rank"] = index
        item["rank"] = index
        item["recommendation_reason"] = item.get("v8_score_reason")

    return ranked
