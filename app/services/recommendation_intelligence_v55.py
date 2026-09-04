
"""
Recommendation Intelligence V5.5

역할:
- Market Representative Price V5.4, Product Quality V10, Market Signal, Identity 신뢰도 등을 통합합니다.
- 각 상품의 "추천 가치"를 계산해 DB에 저장합니다.

실행:
python -m app.services.recommendation_intelligence_v55
"""

from decimal import Decimal
from sqlalchemy import text
from app.db.database import engine


def safe_float(value, default=0):
    try:
        if value is None or value == "":
            return default
        if isinstance(value, Decimal):
            return float(value)
        return float(value)
    except Exception:
        return default


def safe_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def clamp(value, low=0, high=100):
    return round(max(low, min(high, value)), 1)


def calculate_price_advantage(row):
    score = safe_float(row.get("market_price_score"), 50)
    avg_gap = safe_float(row.get("price_vs_market_avg_pct"), 0)
    median_gap = safe_float(row.get("price_vs_market_median_pct"), 0)
    percentile = safe_float(row.get("market_price_percentile"), 50)

    if avg_gap < 0:
        score += min(15, abs(avg_gap) * 0.35)
    elif avg_gap > 0:
        score -= min(15, avg_gap * 0.35)

    if median_gap < 0:
        score += min(10, abs(median_gap) * 0.25)
    elif median_gap > 0:
        score -= min(10, median_gap * 0.25)

    if percentile <= 10:
        score += 10
    elif percentile <= 25:
        score += 6
    elif percentile >= 80:
        score -= 10

    return clamp(score)


def calculate_quality_advantage(row):
    values = [
        safe_float(row.get("product_quality_score"), 0),
        safe_float(row.get("ai_product_quality_score"), 0),
        safe_float(row.get("recommendation_base_score"), 0),
    ]
    values = [v for v in values if v > 0]

    if not values:
        return 50

    return clamp(sum(values) / len(values))


def calculate_market_signal_advantage(row):
    market_signal = safe_float(row.get("market_signal_score"), 0)
    propagated_signal = safe_float(row.get("propagated_market_signal_score"), 0)
    market_quality = safe_float(row.get("market_quality_score"), 0)

    rating = safe_float(row.get("rating"), 0)
    review_count = safe_int(row.get("review_count"), 0)
    propagated_review_count = safe_int(row.get("propagated_review_count"), 0)

    best_review_count = max(review_count, propagated_review_count)
    score = max(market_signal, propagated_signal, market_quality, 35)

    if rating >= 4.8:
        score += 10
    elif rating >= 4.5:
        score += 6

    if best_review_count >= 9999:
        score += 15
    elif best_review_count >= 1000:
        score += 10
    elif best_review_count >= 300:
        score += 6
    elif best_review_count >= 100:
        score += 3

    return clamp(score)


def calculate_trust_score(row):
    values = [
        safe_float(row.get("identity_v3_score"), 0),
        safe_float(row.get("identity_cluster_confidence"), 0),
        safe_float(row.get("market_cluster_confidence"), 0),
        safe_float(row.get("product_variety_confidence"), 0),
    ]
    values = [v for v in values if v > 0]

    if not values:
        return 45

    return clamp(sum(values) / len(values))


def calculate_scarcity_score(row):
    market_count = safe_int(row.get("market_price_count"), 0)

    if market_count <= 0:
        return 50
    if market_count <= 2:
        return 90
    if market_count <= 5:
        return 78
    if market_count <= 10:
        return 65
    if market_count <= 30:
        return 50

    return 35


def calculate_representative_bonus(row):
    if row.get("is_cluster_representative"):
        return 100

    representative_score = safe_float(row.get("cluster_representative_score"), 0)

    if representative_score > 0:
        return clamp(representative_score)

    percentile = safe_float(row.get("market_price_percentile"), 100)
    quality = safe_float(row.get("product_quality_score"), 0)

    if percentile <= 25 and quality >= 80:
        return 80

    return 50


def calculate_ai_suitability(row):
    quality_band = str(row.get("market_quality_band") or "")
    gift_band = str(row.get("market_gift_band") or "")
    attr_band = str(row.get("market_attribute_band") or "")
    product_name = str(row.get("product_name") or "")

    score = 50

    if "HIGH_SUGAR" in quality_band or "VERY_HIGH_SUGAR" in quality_band:
        score += 18
    if "PREMIUM" in gift_band or "LUXURY" in gift_band:
        score += 10
    if "HOME_USE" in gift_band:
        score += 5
    if "DIRECT" in attr_band:
        score += 8
    if "WASHED" in attr_band:
        score += 6
    if "GAP" in attr_band or "ORGANIC" in attr_band:
        score += 8
    if "고당도" in product_name or "brix" in product_name.lower() or "브릭스" in product_name:
        score += 8

    return clamp(score)


def calculate_recommendation_grade(score):
    if score >= 95:
        return "★★★★★ AI 적극추천"
    if score >= 90:
        return "★★★★☆ 강력추천"
    if score >= 80:
        return "★★★★ 추천"
    if score >= 70:
        return "★★★ 조건부추천"
    if score >= 60:
        return "★★ 보통"
    return "★ 추천주의"


def build_recommendation_reasons(row, scores):
    reasons = []

    avg_gap = safe_float(row.get("price_vs_market_avg_pct"), 0)
    median_gap = safe_float(row.get("price_vs_market_median_pct"), 0)
    review_count = max(
        safe_int(row.get("review_count"), 0),
        safe_int(row.get("propagated_review_count"), 0),
    )
    rating = safe_float(row.get("rating"), 0)

    if avg_gap < -5:
        reasons.append(f"동일 시장 평균보다 {abs(avg_gap):.1f}% 저렴")
    elif median_gap < -5:
        reasons.append(f"동일 시장 중앙값보다 {abs(median_gap):.1f}% 저렴")
    elif scores["price_advantage_score"] >= 85:
        reasons.append("동일 시장 내 가격 경쟁력 우수")

    if scores["quality_advantage_score"] >= 85:
        reasons.append("상품 품질 점수 우수")
    elif scores["quality_advantage_score"] >= 75:
        reasons.append("상품 품질 점수 양호")

    if review_count >= 9999:
        reasons.append("리뷰 9,999건 이상 시장 반응 확인")
    elif review_count >= 1000:
        reasons.append(f"리뷰 {review_count:,}건으로 시장 반응 확인")
    elif rating >= 4.7:
        reasons.append(f"평점 {rating:g}점으로 만족도 우수")

    if scores["trust_score_final"] >= 85:
        reasons.append("상품 식별 및 시장 분류 신뢰도 높음")

    if scores["scarcity_score"] >= 78:
        reasons.append("동일 시장 내 비교 상품이 적은 희소 상품군")

    if scores["representative_bonus"] >= 80:
        reasons.append("가격과 품질이 함께 좋은 대표 후보")

    defaults = [
        "가격·품질·시장 신호를 종합한 추천 후보",
        "동일 시장 비교 기준으로 평가됨",
        "추천 가치 점수 기반으로 선별됨",
    ]

    for default in defaults:
        if len(reasons) >= 3:
            break
        reasons.append(default)

    return reasons[:3]


def calculate_recommendation_intelligence(row):
    price = calculate_price_advantage(row)
    quality = calculate_quality_advantage(row)
    market = calculate_market_signal_advantage(row)
    trust = calculate_trust_score(row)
    scarcity = calculate_scarcity_score(row)
    representative = calculate_representative_bonus(row)
    suitability = calculate_ai_suitability(row)

    final_score = clamp(
        price * 0.30
        + quality * 0.25
        + market * 0.15
        + trust * 0.10
        + scarcity * 0.10
        + representative * 0.05
        + suitability * 0.05
    )

    payload = {
        "recommendation_value_score": final_score,
        "price_advantage_score": price,
        "quality_advantage_score": quality,
        "market_signal_score_final": market,
        "trust_score_final": trust,
        "scarcity_score": scarcity,
        "representative_bonus": representative,
        "ai_suitability_score": suitability,
        "recommendation_grade": calculate_recommendation_grade(final_score),
    }

    reasons = build_recommendation_reasons(row, payload)
    payload["recommendation_reason_1"] = reasons[0]
    payload["recommendation_reason_2"] = reasons[1]
    payload["recommendation_reason_3"] = reasons[2]

    payload["recommendation_rank_score"] = clamp(
        final_score * 0.85
        + price * 0.08
        + quality * 0.07
    )

    return payload




def fetch_targets(limit=3000):
    sql = text("""
        SELECT *
        FROM online_food_price_snapshot
        WHERE product_name IS NOT NULL
        ORDER BY collected_at DESC NULLS LAST
        LIMIT :limit
    """)

    with engine.connect() as conn:
        return [dict(row) for row in conn.execute(sql, {"limit": limit}).mappings().all()]


def update_recommendation_fields(row_id, payload):
    sql = text("""
        UPDATE online_food_price_snapshot
        SET
            recommendation_value_score = :recommendation_value_score,
            price_advantage_score = :price_advantage_score,
            quality_advantage_score = :quality_advantage_score,
            market_signal_score_final = :market_signal_score_final,
            trust_score_final = :trust_score_final,
            scarcity_score = :scarcity_score,
            representative_bonus = :representative_bonus,
            ai_suitability_score = :ai_suitability_score,
            recommendation_grade = :recommendation_grade,
            recommendation_reason_1 = :recommendation_reason_1,
            recommendation_reason_2 = :recommendation_reason_2,
            recommendation_reason_3 = :recommendation_reason_3,
            recommendation_rank_score = :recommendation_rank_score
        WHERE id = :id
    """)

    with engine.begin() as conn:
        conn.execute(sql, {"id": row_id, **payload})


def run_recommendation_intelligence_v55(limit=3000):
    rows = fetch_targets(limit=limit)

    updated = 0
    failed = 0

    print(f"🔎 Recommendation Intelligence V5.5 대상: {len(rows)}건")

    for row in rows:
        try:
            payload = calculate_recommendation_intelligence(row)
            update_recommendation_fields(row["id"], payload)
            updated += 1

            print(
                "✅ Recommendation V5.5:",
                str(row.get("product_name", ""))[:45],
                {
                    "value": payload.get("recommendation_value_score"),
                    "grade": payload.get("recommendation_grade"),
                    "price": payload.get("price_advantage_score"),
                    "quality": payload.get("quality_advantage_score"),
                    "market": payload.get("market_signal_score_final"),
                    "reason": payload.get("recommendation_reason_1"),
                },
            )

        except Exception as e:
            failed += 1
            print("❌ Recommendation V5.5 실패:", str(row.get("product_name", ""))[:45], str(e)[:160])

    print(f"✅ Recommendation Intelligence V5.5 완료: updated={updated}, failed={failed}")

    return {"updated": updated, "failed": failed}


if __name__ == "__main__":
    run_recommendation_intelligence_v55(limit=3000)
