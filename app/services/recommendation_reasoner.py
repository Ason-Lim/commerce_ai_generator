def calculate_ai_scores(item):

    scores = {}

    # ---------------------------
    # 품질 점수
    # ---------------------------
    quality_score = 0

    rating = item.get("rating") or 0
    review_count = item.get("review_count") or 0
    brix = item.get("brix") or 0

    quality_score += rating * 20

    if review_count >= 100:
        quality_score += 15

    if brix >= 14:
        quality_score += 25

    scores["quality"] = round(quality_score, 1)

    # ---------------------------
    # 가격 점수
    # ---------------------------
    price_score = 0

    unit_price = item.get("price_per_100g")

    if unit_price:
        if unit_price <= 1000:
            price_score += 40
        elif unit_price <= 2000:
            price_score += 25

    if item.get("discount_rate"):
        price_score += min(
            item.get("discount_rate"),
            30
        )

    scores["price"] = round(price_score, 1)

    # ---------------------------
    # 인기 점수
    # ---------------------------
    popularity_score = 0

    ctr = item.get("ctr_score") or 0

    popularity_score += ctr * 100

    if review_count >= 1000:
        popularity_score += 30

    scores["popularity"] = round(popularity_score, 1)

    # ---------------------------
    # 총합 점수
    # ---------------------------
    total_score = (
        quality_score * 0.4
        + price_score * 0.3
        + popularity_score * 0.3
    )

    scores["total"] = round(total_score, 1)

    return scores