import re

def get_safe_number(
    value,
    default=0.0,
):
    """
    None, 빈 문자열, 콤마가 포함된 숫자를 안전하게 float로 변환합니다.
    """
    try:
        if value is None:
            return float(default)

        if isinstance(value, str):
            value = value.strip().replace(",", "")

            if not value:
                return float(default)

        return float(value)

    except (TypeError, ValueError):
        return float(default)

def get_cached_identity_validation(
    item,
) -> dict:
    """
    상품에 이미 캐싱된 Identity 검증 결과를 안전하게 반환합니다.

    Identity 엔진 전체 이전 전까지 score_engine이
    UI 계층의 enrich_item_identity()에 의존하지 않도록 합니다.
    """
    item = item or {}

    validation = item.get(
        "_identity_validation"
    )

    if isinstance(validation, dict):
        return validation

    return {
        "identity_score": float(
            item.get(
                "_identity_score",
                50,
            )
            or 50
        ),
        "price_confidence": float(
            item.get(
                "_price_confidence",
                50,
            )
            or 50
        ),
        "brix_confidence": float(
            item.get(
                "_brix_confidence",
                50,
            )
            or 50
        ),
        "identity_key": str(
            item.get(
                "_product_identity_key",
                "",
            )
            or ""
        ),
        "warnings": [],
    }

def calculate_mode_score(
    item,
    scores,
    base_priority,
    search_context=None,
):
    
    """추천 모드별 최종 정렬 점수 계산"""

    try:
        trend_boost = float(
            getattr(search_context, "trend_boost", 0.0)
            if search_context is not None
            else 0.0
        )
    except Exception:
        trend_boost = 0.0
    

    quality_score = scores.get("quality", 0)
    price_score = scores.get("price", 0)
    trust_score = scores.get("trust", 0)
    popularity_score = scores.get("popularity", 0)

    if base_priority == "quality":
        validation = get_cached_identity_validation(
            item
        )
        brix_confidence = validation.get("brix_confidence", 0)

        return (
    quality_score * 0.70
    + brix_confidence * 0.20
    + trust_score * 0.07
    + price_score * 0.03
    + trend_boost
)

    if base_priority == "price":
        validation = get_cached_identity_validation(
            item
        )
        price_confidence = validation.get("price_confidence", 0)

        return (
            price_score * 0.58
            + price_confidence * 0.22
            + quality_score * 0.12
            + trust_score * 0.08
            + trend_boost
        )

    if base_priority == "trust":
        return (
            trust_score * 0.75
            + quality_score * 0.15
            + price_score * 0.10
            + trend_boost
        )



    if base_priority == "exploration":
        novelty_score = calculate_novelty_score(item)

        return (
            quality_score * 0.55
            + novelty_score * 0.35
            + price_score * 0.10
            + trend_boost
        )

    if base_priority == "discovery":
        hidden_gem_score = calculate_hidden_gem_score(item)

        return (
            quality_score * 0.45
            + hidden_gem_score * 0.45
            + trust_score * 0.10
            + trend_boost
        )

    if base_priority == "mix":
        return (
            quality_score * 0.40
            + price_score * 0.30
            + trust_score * 0.30
            + trend_boost
        )

    return (
        quality_score * 0.35
        + trust_score * 0.25
        + price_score * 0.20
        + popularity_score * 0.10
        + trend_boost
    )

    
def calculate_price_value_score(item):
    """100g당 가격 기준 가성비 점수 계산"""

    price_per_100g = item.get("price_per_100g")

    try:
        price_per_100g = float(price_per_100g or 0)
    except Exception:
        price_per_100g = 0

    if price_per_100g <= 0:
        return 0

    if price_per_100g <= 400:
        return 90

    if price_per_100g <= 600:
        return 80

    if price_per_100g <= 800:
        return 70

    if price_per_100g <= 1000:
        return 60

    if price_per_100g <= 1200:
        return 45

    if price_per_100g <= 1500:
        return 30

    return 15



def get_brix_value(item):
    """상품에서 brix 값을 안전하게 추출

    1) API/DB 필드에서 먼저 찾고
    2) 없으면 상품명/설명 텍스트에서 15brix, 15 브릭스, 당도 15 같은 패턴을 추출합니다.
    """
    candidates = [
        item.get("brix"),
        item.get("brix_value"),
        item.get("avg_brix"),
        item.get("max_brix"),
        item.get("sugar_brix"),
        item.get("display_brix"),
    ]

    for value in candidates:
        try:
            if value is not None and float(value) > 0:
                return float(value)
        except Exception:
            pass

    text = " ".join(
        str(item.get(key) or "")
        for key in [
            "product_name",
            "raw_name",
            "name",
            "title",
            "description",
            "summary",
        ]
    )

    patterns = [
        r"(\d{2}(?:\.\d+)?)\s*brix",
        r"(\d{2}(?:\.\d+)?)\s*브릭스",
        r"당도\s*(\d{2}(?:\.\d+)?)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            try:
                value = float(match.group(1))
                if 8 <= value <= 30:
                    return value
            except Exception:
                pass

    return 0


def calculate_reaction_trust_score(item):
    """클릭/CTR/사용자 반응 기반 안심 점수 보정"""

    click_count = int(get_safe_number(item.get("click_count"), 0))
    ctr_pct = get_safe_number(item.get("ctr_pct"), 0)

    score = 0

    if item.get("final_recommendation_label") == "사용자 반응 우수 추천":
        score += 25

    if click_count >= 10:
        score += 25
    elif click_count >= 5:
        score += 18
    elif click_count >= 3:
        score += 12
    elif click_count >= 1:
        score += 6

    if ctr_pct >= 10:
        score += 25
    elif ctr_pct >= 5:
        score += 18
    elif ctr_pct >= 3:
        score += 10
    elif ctr_pct > 0:
        score += 5

    return min(score, 45)


def calculate_hidden_gem_score(item):
    """숨은 인기 상품 점수"""

    impression_count = item.get("impression_count") or 0
    click_count = item.get("click_count") or 0
    ctr_pct = item.get("ctr_pct") or 0

    try:
        impression_count = int(impression_count)
    except Exception:
        impression_count = 0

    try:
        click_count = int(click_count)
    except Exception:
        click_count = 0

    try:
        ctr_pct = float(ctr_pct)
    except Exception:
        ctr_pct = 0

    score = 0

    # 발견 추천은 너무 적은 노출보다, 어느 정도 검증된 노출을 더 높게 봅니다.
    if 30 <= impression_count <= 150:
        score += 25
    elif 10 <= impression_count < 30:
        score += 15
    elif 150 < impression_count <= 300:
        score += 10

    # 실제 클릭 반응
    if click_count >= 10:
        score += 35
    elif click_count >= 5:
        score += 30
    elif click_count >= 3:
        score += 25
    elif click_count >= 1:
        score += 15

    # 클릭 반응률
    if ctr_pct >= 20:
        score += 40
    elif ctr_pct >= 10:
        score += 30
    elif ctr_pct >= 5:
        score += 20
    elif ctr_pct >= 3:
        score += 10

    return min(score, 100)


def calculate_ai_scores(item, priority="trust"):
    """상품별 AI 추천 근거 점수 계산"""

    scores = {}

    # 품질 점수
    quality_score = 0

    rating = item.get("rating") or 0
    review_count = item.get("review_count") or 0

    brix = get_brix_value(item)

    if brix >= 16:
        quality_score += 100
    elif brix >= 15:
        quality_score += 85
    elif brix >= 14:
        quality_score += 65
    elif brix >= 13:
        quality_score += 45
    elif item.get("is_high_brix"):
        quality_score += 20

    try:
        rating = float(rating)
    except Exception:
        rating = 0

    try:
        review_count = int(review_count)
    except Exception:
        review_count = 0

    if rating >= 4.8:
        quality_score += 8
    elif rating >= 4.5:
        quality_score += 5
    elif rating >= 4.0:
        quality_score += 3

    if review_count >= 10000:
        quality_score += 8
    elif review_count >= 3000:
        quality_score += 6
    elif review_count >= 1000:
        quality_score += 4
    elif review_count >= 500:
        quality_score += 2

    scores["quality"] = round(quality_score, 1)
    
    # 신뢰 점수    
    
    trust_score = 0

    if rating >= 4.8:
        trust_score += 35
    elif rating >= 4.5:
        trust_score += 25
    elif rating >= 4.0:
        trust_score += 15

    if review_count >= 10000:
        trust_score += 35
    elif review_count >= 3000:
        trust_score += 25
    elif review_count >= 1000:
        trust_score += 15
    elif review_count >= 500:
        trust_score += 10

    if rating >= 4.7 and review_count >= 3000:
        trust_score += 20
    elif rating >= 4.5 and review_count >= 1000:
        trust_score += 12
    elif rating >= 4.3 and review_count >= 500:
        trust_score += 6

    # 리뷰/평점이 부족한 신규 데이터도 실제 클릭/CTR 반응이 있으면
    # 오늘의 베스트와 안심 기준에서 완전히 밀리지 않도록 보정합니다.
    trust_score += calculate_reaction_trust_score(item)

    scores["trust"] = round(min(trust_score, 100), 1)
    

    # 가격 점수

    price_score = calculate_price_value_score(item)

    if item.get("final_discount_rate") or item.get("discount_rate"):
        price_score += 10

    if (item.get("price_drop_boost") or 0) >= 5:
        price_score += 15

    scores["price"] = round(min(price_score, 100), 1)

    # 사용자 반응 점수
    popularity_score = 0

    if item.get("final_recommendation_label") == "사용자 반응 우수 추천":
        popularity_score += 30

    if (item.get("ctr_feedback_boost") or 0) >= 7:
        popularity_score += 30

    try:
        if (item.get("ctr_pct") or 0) >= 20:
            popularity_score += 20
    except Exception:
        pass

    # 발견 추천에서는 실제 클릭/CTR 반응이 있는데도
    # 사용자 반응이 0점으로 보이지 않도록 발견성 점수를 일부 반영합니다.
    base_priority = str(priority or "trust").replace("_adaptive", "")

    if base_priority == "discovery":
        try:
            hidden_gem_score = calculate_hidden_gem_score(item)
            popularity_score = max(
                popularity_score,
                min(hidden_gem_score * 0.4, 35)
            )
        except Exception:
            pass

    scores["popularity"] = round(popularity_score, 1)

    if priority == "price":
        total_score = (
            quality_score * 0.25
            + price_score * 0.60
            + popularity_score * 0.15
        )

    elif priority == "quality":
        total_score = (
            quality_score * 0.60
            + price_score * 0.15
            + popularity_score * 0.25
        )

    elif priority == "trust":
        total_score = (
            quality_score * 0.30
            + price_score * 0.20
            + popularity_score * 0.50
        )

    else:
        total_score = (
            quality_score * 0.40
            + price_score * 0.30
            + popularity_score * 0.30
        )

    scores["total"] = round(total_score, 1)

    return scores
