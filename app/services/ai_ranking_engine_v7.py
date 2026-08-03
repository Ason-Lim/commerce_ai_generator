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

    # 저렴할수록 높은 점수
    score = 100 - ((price - min_price) / (max_price - min_price) * 100)
    return round(max(20, min(100, score)), 1)


def calculate_quality_signal_score(item: dict) -> float:
    name = str(item.get("product_name") or item.get("name") or "")

    score = 50

    quality_keywords = [
        "고당도",
        "당도",
        "brix",
        "브릭스",
        "산지직송",
        "당일출고",
        "선별",
        "프리미엄",
        "명품",
        "국내산",
    ]

    risk_keywords = [
        "못난이",
        "흠과",
        "랜덤",
        "소과",
        "혼합",
    ]

    for keyword in quality_keywords:
        if keyword.lower() in name.lower():
            score += 5

    for keyword in risk_keywords:
        if keyword.lower() in name.lower():
            score -= 4

    return round(max(20, min(100, score)), 1)


def calculate_market_ai_score(item: dict, min_price: float, max_price: float) -> dict:
    enriched = enrich_with_platform_scores(item)

    price_score = calculate_price_score(enriched, min_price, max_price)
    quality_score = calculate_quality_signal_score(enriched)
    platform_score = safe_number(enriched.get("platform_boost_score"), 50)

    # V7 기본 가중치
    final_score = (
        quality_score * 0.35
        + price_score * 0.30
        + platform_score * 0.25
        + 65 * 0.10
    )

    enriched["v7_quality_score"] = quality_score
    enriched["v7_price_score"] = price_score
    enriched["v7_platform_score"] = platform_score
    enriched["v7_stability_score"] = 65
    enriched["v7_final_score"] = round(final_score, 1)

    enriched["v7_score_reason"] = build_v7_score_reason(enriched)

    return enriched


def build_v7_score_reason(item: dict) -> str:
    platform = item.get("platform")
    quality = safe_number(item.get("v7_quality_score"), 0)
    price = safe_number(item.get("v7_price_score"), 0)
    platform_score = safe_number(item.get("v7_platform_score"), 0)

    reasons = []

    if quality >= 70:
        reasons.append("상품명에 고당도·선별·산지직송 등 품질 신호가 많습니다.")
    elif quality >= 55:
        reasons.append("기본적인 품질 신호가 확인됩니다.")
    else:
        reasons.append("품질 신호는 제한적입니다.")

    if price >= 80:
        reasons.append("비교 상품 중 가격 경쟁력이 높습니다.")
    elif price >= 55:
        reasons.append("가격은 비교적 무난한 편입니다.")
    else:
        reasons.append("가격은 비교군 대비 높은 편입니다.")

    if platform == "coupang":
        reasons.append("쿠팡 상품으로 구매 전환과 배송 편의성이 반영되었습니다.")
    elif platform == "naver":
        reasons.append("네이버 쇼핑 상품으로 가격 비교 장점이 반영되었습니다.")

    if platform_score >= 70:
        reasons.append("플랫폼 보정 점수가 높습니다.")

    return " ".join(reasons)


def rank_market_items_v7(items):
    valid_items = [item for item in items if isinstance(item, dict)]

    prices = [
        safe_number(item.get("price"), 0)
        for item in valid_items
        if safe_number(item.get("price"), 0) > 0
    ]

    min_price = min(prices) if prices else 0
    max_price = max(prices) if prices else 0

    ranked = [
        calculate_market_ai_score(item, min_price, max_price)
        for item in valid_items
    ]

    ranked.sort(
        key=lambda x: (
            safe_number(x.get("v7_final_score"), 0),
            safe_number(x.get("v7_quality_score"), 0),
            safe_number(x.get("v7_price_score"), 0),
        ),
        reverse=True,
    )

    for index, item in enumerate(ranked, start=1):
        item["v7_rank"] = index
        item["rank"] = index

    return ranked
