from app.services.db_product_collector import fetch_products_from_db
from app.services.price_engine import (
    calculate_discount_rate,
    calculate_price_per_100g,
)
from app.services.brix_analyzer import build_brix_info
from app.services.strategy_engine import build_b2b_strategy
from app.services.coupang_review_matcher import apply_coupang_review_signal
from app.services.intent_analyzer import analyze_user_query

def build_platform_label(raw):
    base = raw.get("platform")
    mall = raw.get("mall_name")

    if base == "네이버" and mall:
        return f"네이버/{mall}"

    return base or "기타"


def deduplicate_products(products):
    seen = set()
    unique = []

    for p in products:
        name = (p.get("name") or "").strip()
        price = p.get("price")
        key = f"{name}_{price}"

        if key in seen:
            continue

        seen.add(key)
        unique.append(p)

    return unique


def normalize_product(raw):
    price = raw.get("price")
    original_price = raw.get("original_price")

    discount_rate = raw.get("discount_rate")
    if discount_rate is None:
        discount_rate = calculate_discount_rate(original_price, price) or 0

    if raw.get("unit_price_per_kg"):
        price_per_100g = round(float(raw["unit_price_per_kg"]) / 10, 1)
    else:
        price_per_100g = calculate_price_per_100g(price, raw.get("weight_g"))

    brix_info = build_brix_info(raw.get("name", ""), raw.get("description", ""))

    brix_value = raw.get("brix_value") or brix_info.get("brix_value")
    is_high_sugar = bool(
        raw.get("high_sugar_flag")
        or raw.get("taste_guarantee_flag")
        or brix_info.get("is_high_sugar")
    )

    quality_labels = []

    if brix_value:
        quality_labels.append(f"Brix {brix_value}")

    if is_high_sugar:
        quality_labels.append("고당도")

    if raw.get("premium_flag"):
        quality_labels.append("프리미엄")

    if raw.get("gift_flag"):
        quality_labels.append("선물용")

    if not quality_labels:
        quality_labels.append(brix_info.get("brix_label", "품질 정보 부족"))

    quality_score = brix_info.get("quality_score", 50)

    if brix_value and brix_value >= 13:
        quality_score = max(quality_score, 90)

    if is_high_sugar:
        quality_score = max(quality_score, 75)

    if raw.get("premium_flag"):
        quality_score += 8

    if raw.get("gift_flag"):
        quality_score += 5

    quality_score = min(quality_score, 100)

    return {
        "name": raw.get("name"),
        "platform": raw.get("platform"),
        "platform_label": build_platform_label(raw),
        "price": price,
        "original_price": original_price,
        "discount_rate": round(float(discount_rate or 0), 1),
        "price_per_100g": price_per_100g,
        "weight_g": raw.get("weight_g"),
        "rating": raw.get("rating"),
        "review_count": raw.get("review_count"),
        "brix_value": brix_value,
        "is_high_sugar": is_high_sugar,
        "brix_label": " / ".join(quality_labels),
        "quality_score": quality_score,
        "url": raw.get("url"),
    }


def calculate_score(p, priority):
    price_score = 0
    discount_score = 0
    quality_score = 0
    trust_score = 0

    if p.get("price_per_100g") is not None:
        price_score = max(0, 2500 - float(p["price_per_100g"])) / 25

    if p.get("discount_rate") is not None:
        discount_score = float(p["discount_rate"]) * 2

    if p.get("quality_score"):
        quality_score += float(p["quality_score"]) * 0.7

    if p.get("is_high_sugar"):
        quality_score += 20

    if p.get("rating"):
        trust_score += float(p["rating"]) * 10

    if p.get("review_count"):
        trust_score += min(int(p["review_count"]) / 100, 30)

    if priority == "price":
        score = price_score * 0.65 + discount_score * 0.15 + quality_score * 0.1 + trust_score * 0.1
    elif priority == "quality":
        score = quality_score * 0.55 + trust_score * 0.25 + price_score * 0.1 + discount_score * 0.1
    elif priority == "discount":
        score = discount_score * 0.6 + price_score * 0.2 + quality_score * 0.1 + trust_score * 0.1
    else:
        score = price_score + discount_score + quality_score + trust_score

    return round(score, 1)

def calculate_trust_score(p):
    score = 0

    if p.get("price"):
        score += 20

    if p.get("price_per_100g"):
        score += 20

    if p.get("weight_g"):
        score += 15

    if p.get("is_high_sugar"):
        score += 20

    if p.get("discount_rate") and p["discount_rate"] > 0:
        score += 10

    if p.get("platform"):
        score += 10

    return min(score, 100)

def calculate_final_score(p, priority):
    base_score = calculate_score(p, priority)
    trust = calculate_trust_score(p)

    # 🔥 신뢰도 가중치 (핵심 튜닝 포인트)
    trust_weight = 0.3   # 0.2 ~ 0.4 추천

    final_score = base_score + (trust * trust_weight)

    return round(final_score, 1)



def build_recommendation_reasons(product, rank_label):
    reasons = []

    if product.get("price_per_100g"):
        reasons.append(f"100g당 {int(product['price_per_100g']):,}원으로 가격 비교가 가능합니다.")

    if product.get("discount_rate") and product["discount_rate"] > 0:
        reasons.append(f"현재 할인율 {product['discount_rate']}%가 반영되어 구매 타이밍이 좋습니다.")

    if product.get("is_high_sugar"):
        reasons.append("고당도/프리미엄 품질 신호가 있어 선물용·프리미엄 구매 설득력이 있습니다.")

    if product.get("review_count"):
        reasons.append(f"리뷰 {int(product['review_count']):,}개 기반으로 구매 신뢰도를 보강할 수 있습니다.")

    if product.get("rating"):
        reasons.append(f"별점 {product['rating']}점으로 소비자 만족도 신호가 있습니다.")

    if product.get("trust_score"):
        reasons.append(
            f"상품 정보 완성도 {product['trust_score']}점으로 비교 기준이 명확합니다."
        )

    if not reasons:
        reasons.append("가격과 상품명을 기준으로 비교 가능한 후보 상품입니다.")
        
        if product.get("review_signal"):
            signal = product["review_signal"]
            if signal.get("review_count"):
                reasons.append(
                    f"쿠팡 유사 상품 리뷰 {int(signal['review_count']):,}개를 참고해 구매 신뢰도를 보강했습니다."
                )
            elif signal.get("rating"):
                reasons.append(
                    f"쿠팡 유사 상품 별점 {signal['rating']}점을 참고해 신뢰도를 보강했습니다."
                )

    headline = f"{rank_label} 추천 상품입니다. 가격, 품질, 신뢰도 요소를 종합해 우선 노출했습니다."

    return {
        "headline": headline,
        "bullets": reasons[:4],
        "cta_text": "최저가 보러가기" if product.get("price_per_100g") else "상품 보러가기",
    }


def find_best_price_product(products):
    valid = [p for p in products if p.get("price_per_100g") is not None]
    if not valid:
        valid = [p for p in products if p.get("price") is not None]
        return min(valid, key=lambda x: x["price"]) if valid else None
    return min(valid, key=lambda x: x["price_per_100g"])


def find_best_quality_product(products):
    valid = products[:]
    if not valid:
        return None
    return max(valid, key=lambda x: (x.get("quality_score") or 0, x.get("review_count") or 0))


def safe_price_per_100g(price, weight_g):
    """안전한 100g당 가격 계산"""
    try:
        if not price:
            return None

        if not weight_g:
            return None

        weight_g = float(weight_g)

        # 비정상 방어
        if weight_g <= 0:
            return None

        # 10g 이하 비정상 방어
        if weight_g < 10:
            return None

        value = (float(price) / weight_g) * 100

        # 비정상 가격 방어
        if value > 100000:
            return None

        return round(value)

    except:
        return None


def generate_product_strategy(request):
    intent = analyze_user_query(request.context)

    search_keyword = intent["normalized_keyword"]

    raw_products = fetch_products_from_db(search_keyword)

    products = [normalize_product(p) for p in raw_products]

    products = deduplicate_products(products)

    for p in products:
        # 가격 데이터 검증 및 수정
        p["price_per_100g"] = safe_price_per_100g(
            p.get("price"),
            p.get("weight_g")
        )
        p["trust_score"] = calculate_trust_score(p)
        p["score"] = calculate_final_score(p, request.priority)
    
    products = sorted(products, key=lambda x: x["score"], reverse=True)

    medals = ["🥇 1순위 강력 추천", "🥈 2순위 대안 추천", "🥉 3순위 가성비 후보"]

    for idx, p in enumerate(products[:3]):
        p["rank_label"] = medals[idx]
        p["recommendation"] = build_recommendation_reasons(p, medals[idx])

        if request.mode == "B2B":
            p["b2b_strategy"] = build_b2b_strategy(p, request.quantity)

    best_price = find_best_price_product(products)
    best_quality = find_best_quality_product(products)

    if best_price:
        best_price["compare_label"] = "💰 최저가 후보"
        best_price["recommendation"] = build_recommendation_reasons(best_price, "💰 최저가 후보")

    if best_quality:
        best_quality["compare_label"] = "🍬 최고품질 후보"
        best_quality["recommendation"] = build_recommendation_reasons(best_quality, "🍬 최고품질 후보")

        return {
        "query": request.context,
        "search_keyword": search_keyword,
        "intent": intent,
        "mode": request.mode,
        "priority": request.priority,
        "summary": "문장형 요청을 분석해 맞춤 검색어로 변환하고 추천했습니다.",
        "top3": products[:3],
        "best_price": best_price,
        "best_quality": best_quality,
        "products": products,
    }
