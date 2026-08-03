def safe_number(value, default=0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def normalize_platform_name(item: dict) -> str:
    platform = str(item.get("platform") or "").lower()
    mall_name = str(item.get("mall_name") or "").lower()
    source = str(item.get("source") or "").lower()

    if "coupang" in platform or "쿠팡" in mall_name or "coupang" in source:
        return "coupang"

    if "naver" in platform or "네이버" in mall_name or "naver" in source:
        return "naver"

    return platform or "unknown"


def calculate_platform_scores(item: dict) -> dict:
    platform = normalize_platform_name(item)
    price = safe_number(item.get("price"), 0)

    trust_score = 50
    delivery_score = 50
    price_compare_score = 50
    conversion_score = 50
    policy_score = 50

    if platform == "coupang":
        trust_score = 72
        delivery_score = 82
        price_compare_score = 58
        conversion_score = 78
        policy_score = 65

        if item.get("is_ad"):
            policy_score += 5

        if item.get("product_url"):
            conversion_score += 5

    elif platform == "naver":
        trust_score = 68
        delivery_score = 58
        price_compare_score = 82
        conversion_score = 62
        policy_score = 70

    else:
        trust_score = 50
        delivery_score = 50
        price_compare_score = 50
        conversion_score = 50
        policy_score = 50

    if price <= 0:
        price_compare_score -= 20
        conversion_score -= 10

    return {
        "platform": platform,
        "platform_trust_score": max(0, min(100, trust_score)),
        "platform_delivery_score": max(0, min(100, delivery_score)),
        "platform_price_compare_score": max(0, min(100, price_compare_score)),
        "platform_conversion_score": max(0, min(100, conversion_score)),
        "platform_policy_score": max(0, min(100, policy_score)),
    }


def calculate_platform_boost(item: dict) -> float:
    scores = calculate_platform_scores(item)

    boost = (
        scores["platform_trust_score"] * 0.25
        + scores["platform_delivery_score"] * 0.25
        + scores["platform_price_compare_score"] * 0.20
        + scores["platform_conversion_score"] * 0.20
        + scores["platform_policy_score"] * 0.10
    )

    return round(boost, 1)


def enrich_with_platform_scores(item: dict) -> dict:
    result = dict(item)
    platform_scores = calculate_platform_scores(result)
    result.update(platform_scores)
    result["platform_boost_score"] = calculate_platform_boost(result)

    platform = platform_scores["platform"]

    if platform == "coupang":
        result["platform_reason"] = "쿠팡 판매 채널의 배송·구매 편의 신호를 반영했습니다."
        result["platform_notice"] = result.get(
            "partner_notice",
            "쿠팡 파트너스 활동의 일환으로 일정액의 수수료를 제공받을 수 있습니다.",
        )

    elif platform == "naver":
        result["platform_reason"] = "네이버쇼핑의 가격·판매 조건 비교 편의성을 반영했습니다."
        result["platform_notice"] = ""

    else:
        result["platform_reason"] = "플랫폼 정보가 제한적이므로 가격과 상품 정보를 함께 확인하는 것이 좋습니다."
        result["platform_notice"] = ""

    return result


def enrich_market_items_with_platform_scores(items):
    return [enrich_with_platform_scores(item) for item in items if isinstance(item, dict)]
