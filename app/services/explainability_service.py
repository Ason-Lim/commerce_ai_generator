
"""
Recommendation Explainability Engine V6

역할:
- Recommendation Intelligence V5.5에서 계산된 점수/이유를 바탕으로
  사람이 이해할 수 있는 추천 설명을 생성합니다.
- UI, PDF, API, 챗봇에서 공통으로 재사용할 수 있는 설명 객체를 반환합니다.

사용 예:
from app.services.explainability_service import build_explainability

explain = build_explainability(item)
"""

from decimal import Decimal


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


def get_effective_review_count(item):
    return max(
        safe_int(item.get("review_count"), 0),
        safe_int(item.get("propagated_review_count"), 0),
    )


def build_recommendation_summary(item):
    value_score = safe_float(item.get("recommendation_value_score"), 0)
    price_score = safe_float(item.get("price_advantage_score"), 0)
    quality_score = safe_float(item.get("quality_advantage_score"), 0)
    market_score = safe_float(item.get("market_signal_score_final"), 0)

    if value_score >= 90:
        return "가격·품질·시장 신호가 모두 우수한 강력 추천 상품입니다."

    if price_score >= 90 and quality_score >= 75:
        return "시장 대비 가격 경쟁력과 품질을 함께 갖춘 추천 상품입니다."

    if quality_score >= 85:
        return "품질 신호가 뚜렷한 고품질 추천 상품입니다."

    if price_score >= 90:
        return "동일 시장 안에서 가격 경쟁력이 돋보이는 상품입니다."

    if market_score >= 75:
        return "리뷰와 시장 반응이 확인된 안정적인 추천 상품입니다."

    if value_score >= 70:
        return "가격·품질·시장 정보를 종합해 추천할 만한 상품입니다."

    return "일부 장점은 있으나 추가 비교가 필요한 후보 상품입니다."


def build_recommendation_story(item):
    summary = build_recommendation_summary(item)

    avg_gap = safe_float(item.get("price_vs_market_avg_pct"), 0)
    median_gap = safe_float(item.get("price_vs_market_median_pct"), 0)
    quality_score = safe_float(item.get("quality_advantage_score"), 0)
    market_score = safe_float(item.get("market_signal_score_final"), 0)
    trust_score = safe_float(item.get("trust_score_final"), 0)
    market_label = item.get("market_cluster_label") or "동일 시장"

    sentences = [summary]

    if avg_gap < -5:
        sentences.append(
            f"{market_label} 평균보다 약 {abs(avg_gap):.1f}% 저렴해 가격 경쟁력이 있습니다."
        )
    elif median_gap < -5:
        sentences.append(
            f"{market_label} 중앙값보다 약 {abs(median_gap):.1f}% 저렴한 편입니다."
        )

    if quality_score >= 85:
        sentences.append("품질 점수도 높아 단순히 싼 상품이 아니라 품질 측면에서도 강점이 있습니다.")
    elif quality_score >= 75:
        sentences.append("품질 점수가 양호해 가격과 품질의 균형이 괜찮습니다.")

    if market_score >= 75:
        sentences.append("리뷰·평점 등 시장 반응도 확인되어 구매 안정성이 높습니다.")

    if trust_score >= 85:
        sentences.append("상품 식별과 시장 분류 신뢰도도 높아 비교 기준이 비교적 명확합니다.")

    if len(sentences) == 1:
        sentences.append("다만 시장 데이터가 충분하지 않은 부분이 있어 다른 후보와 함께 비교하는 것이 좋습니다.")

    return " ".join(sentences)


def build_recommendation_reasons(item):
    reasons = []

    for key in [
        "recommendation_reason_1",
        "recommendation_reason_2",
        "recommendation_reason_3",
    ]:
        value = item.get(key)
        if value and value not in reasons:
            reasons.append(value)

    avg_gap = safe_float(item.get("price_vs_market_avg_pct"), 0)
    median_gap = safe_float(item.get("price_vs_market_median_pct"), 0)
    price_score = safe_float(item.get("price_advantage_score"), 0)
    quality_score = safe_float(item.get("quality_advantage_score"), 0)
    market_score = safe_float(item.get("market_signal_score_final"), 0)
    review_count = get_effective_review_count(item)
    rating = safe_float(item.get("rating"), 0)

    if avg_gap < -5:
        text = f"동일 시장 평균보다 {abs(avg_gap):.1f}% 저렴합니다."
        if text not in reasons:
            reasons.append(text)

    if median_gap < -5:
        text = f"동일 시장 중앙값보다 {abs(median_gap):.1f}% 저렴합니다."
        if text not in reasons:
            reasons.append(text)

    if price_score >= 90:
        text = "동일 시장 내 가격 경쟁력이 우수합니다."
        if text not in reasons:
            reasons.append(text)

    if quality_score >= 85:
        text = "상품 품질 점수가 우수합니다."
        if text not in reasons:
            reasons.append(text)
    elif quality_score >= 75:
        text = "상품 품질 점수가 양호합니다."
        if text not in reasons:
            reasons.append(text)

    if review_count >= 9999:
        text = "리뷰 9,999건 이상으로 시장 반응이 충분히 확인되었습니다."
        if text not in reasons:
            reasons.append(text)
    elif review_count >= 1000:
        text = f"리뷰 {review_count:,}건으로 시장 반응이 확인되었습니다."
        if text not in reasons:
            reasons.append(text)
    elif rating >= 4.7:
        text = f"평점 {rating:g}점으로 만족도 신호가 좋습니다."
        if text not in reasons:
            reasons.append(text)

    if market_score >= 75:
        text = "시장 신호 점수가 높아 안정적인 후보입니다."
        if text not in reasons:
            reasons.append(text)

    defaults = [
        "가격·품질·시장 신호를 종합해 선별된 상품입니다.",
        "동일 시장 비교 기준으로 평가되었습니다.",
        "추천 가치 점수를 기준으로 검토되었습니다.",
    ]

    for default in defaults:
        if len(reasons) >= 4:
            break
        if default not in reasons:
            reasons.append(default)

    return reasons[:5]


def build_target_users(item):
    targets = []

    gift_band = str(item.get("market_gift_band") or "")
    quality_band = str(item.get("market_quality_band") or "")
    attr_band = str(item.get("market_attribute_band") or "")
    price_score = safe_float(item.get("price_advantage_score"), 0)
    quality_score = safe_float(item.get("quality_advantage_score"), 0)
    market_label = str(item.get("market_cluster_label") or "")

    if "LUXURY" in gift_band or "PREMIUM" in gift_band:
        targets.append("선물용 상품을 찾는 고객")

    if quality_score >= 80 or "HIGH_SUGAR" in quality_band or "VERY_HIGH_SUGAR" in quality_band:
        targets.append("품질과 당도를 중요하게 보는 고객")

    if price_score >= 85:
        targets.append("동일 시장 대비 가격 경쟁력을 중시하는 고객")

    if "HOME_USE" in gift_band:
        targets.append("가정용·실속형 상품을 찾는 고객")

    if "WASHED" in attr_band:
        targets.append("세척·간편 섭취 상품을 선호하는 고객")

    if "DIRECT" in attr_band:
        targets.append("산지직송 상품을 선호하는 고객")

    if "사과" in market_label:
        targets.append("사과 구매를 비교 중인 고객")
    elif "배" in market_label:
        targets.append("배 선물 또는 가정용 구매를 비교 중인 고객")
    elif "샤인머스켓" in market_label:
        targets.append("샤인머스켓 구매를 비교 중인 고객")

    if not targets:
        targets.append("가격과 품질을 함께 비교하려는 고객")

    return targets[:4]


def build_cautions(item):
    cautions = []

    review_count = get_effective_review_count(item)
    rating = safe_float(item.get("rating"), 0)
    quality_score = safe_float(item.get("quality_advantage_score"), 0)
    trust_score = safe_float(item.get("trust_score_final"), 0)
    market_count = safe_int(item.get("market_price_count"), 0)
    market_cluster_confidence = safe_float(item.get("market_cluster_confidence"), 0)
    price_score = safe_float(item.get("price_advantage_score"), 0)

    if review_count <= 0 and rating <= 0:
        cautions.append("리뷰·평점 데이터가 아직 충분하지 않습니다.")

    if market_count <= 2:
        cautions.append("동일 시장 내 비교 상품 수가 적어 가격 기준이 제한적일 수 있습니다.")

    if quality_score < 60:
        cautions.append("품질 정보가 충분하지 않거나 품질 신호가 약합니다.")

    if trust_score < 60 or market_cluster_confidence < 60:
        cautions.append("상품 식별 또는 시장 분류 신뢰도가 낮아 추가 확인이 필요합니다.")

    if price_score < 40:
        cautions.append("동일 시장 안에서 가격 경쟁력은 약한 편입니다.")

    if not cautions:
        cautions.append("현재 기준에서 특별한 주의 신호는 크지 않습니다.")

    return cautions[:3]


def calculate_explainability_confidence(item):
    score = 40

    if safe_float(item.get("recommendation_value_score"), 0) > 0:
        score += 15

    if safe_float(item.get("market_price_score"), 0) > 0:
        score += 15

    if safe_float(item.get("quality_advantage_score"), 0) > 0:
        score += 15

    if get_effective_review_count(item) > 0 or safe_float(item.get("rating"), 0) > 0:
        score += 10

    if safe_float(item.get("trust_score_final"), 0) >= 70:
        score += 10

    if safe_int(item.get("market_price_count"), 0) >= 3:
        score += 5

    return round(max(0, min(100, score)), 1)


def build_explainability(item):
    return {
        "summary": build_recommendation_summary(item),
        "story": build_recommendation_story(item),
        "reasons": build_recommendation_reasons(item),
        "target_users": build_target_users(item),
        "cautions": build_cautions(item),
        "confidence": calculate_explainability_confidence(item),
        "grade": item.get("recommendation_grade"),
        "score": safe_float(item.get("recommendation_value_score"), 0),
    }


def build_short_explain_text(item):
    explain = build_explainability(item)
    reasons = explain.get("reasons", [])

    reason_text = " / ".join(reasons[:2]) if reasons else "추천 가치 기준으로 선별되었습니다."

    return f"{explain['summary']} {reason_text}"
