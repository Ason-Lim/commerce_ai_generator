
"""
Recommendation Story Engine V6.1

역할:
- 상품의 가격, 품질, 배송, 시장 반응, 신뢰도 신호를 조합해
  사람이 이해하기 쉬운 AI 분석 스토리를 생성합니다.
- Hero, 상품 카드, PDF, API에서 공통으로 재사용할 수 있습니다.
"""

from decimal import Decimal
import re


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


def fmt_money(value):
    try:
        value = float(value or 0)
        if value <= 0:
            return ""
        return f"{int(value):,}원"
    except Exception:
        return ""


def fmt_pct(value):
    try:
        value = float(value or 0)
        return f"{abs(value):.1f}%"
    except Exception:
        return ""


def get_text_blob(item, display=None):
    values = []

    for key in [
        "product_name",
        "raw_name",
        "title",
        "seller_name",
        "mall_name",
        "platform_name",
        "market_cluster_label",
        "market_quality_band",
        "market_gift_band",
        "market_attribute_band",
    ]:
        value = item.get(key)
        if value:
            values.append(str(value))

    if display:
        for key in ["name", "seller_text", "brix_text", "weight_text"]:
            value = display.get(key)
            if value:
                values.append(str(value))

    return " ".join(values)


def get_brix_value(item, display=None):
    candidates = [
        item.get("brix"),
        item.get("brix_value"),
        item.get("avg_brix"),
        item.get("max_brix"),
        item.get("display_brix"),
    ]

    for value in candidates:
        try:
            if value is not None and float(value) > 0:
                return float(value)
        except Exception:
            pass

    text = get_text_blob(item, display).lower()

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


def build_price_story(item, display=None):
    stories = []
    display = display or {}

    ai_price = (
        display.get("ai_estimated_price")
        or item.get("benefit_price")
        or item.get("max_benefit_price")
        or item.get("member_price")
        or item.get("sale_price")
        or item.get("price")
    )

    sale_price = display.get("price") or item.get("sale_price") or item.get("price")
    original_price = display.get("original_price") or item.get("original_price")
    member_price = display.get("member_price") or item.get("member_price")
    discount_rate = display.get("discount_rate") or item.get("discount_rate")
    avg_gap = item.get("price_vs_market_avg_pct")
    median_gap = item.get("price_vs_market_median_pct")

    if ai_price:
        label = display.get("ai_estimated_price_label") or item.get("ai_estimated_price_label") or "구매 기준가"
        stories.append(f"{label} 기준으로 {fmt_money(ai_price)}에 확인되는 상품입니다.")

    if original_price and sale_price and float(original_price or 0) > float(sale_price or 0):
        stories.append(
             f"정상가 {fmt_money(original_price)}에서 판매가 {fmt_money(sale_price)}으로 낮아져 있습니다."
        )

    if member_price and sale_price and float(member_price or 0) < float(sale_price or 0):
        stories.append(f"멤버십 적용 시 {fmt_money(member_price)}까지 낮아질 수 있습니다.")

    if discount_rate and safe_float(discount_rate) >= 10:
        stories.append(f"현재 약 {safe_float(discount_rate):.1f}% 할인 신호가 확인됩니다.")

    if avg_gap is not None and safe_float(avg_gap) < -5:
        stories.append(f"동일 시장 평균보다 약 {fmt_pct(avg_gap)} 저렴합니다.")
    elif median_gap is not None and safe_float(median_gap) < -5:
        stories.append(f"동일 시장 중앙값보다 약 {fmt_pct(median_gap)} 저렴합니다.")

    return dedupe_text_list(stories)[:3]


def build_quality_story(item, display=None):
    stories = []
    display = display or {}

    brix = get_brix_value(item, display)
    quality_score = safe_float(
        item.get("quality_advantage_score")
        or item.get("product_quality_score")
        or item.get("recommendation_base_score")
        or 0
    )

    text = get_text_blob(item, display)

    if brix >= 15:
        stories.append(f"{brix:g}brix 당도 정보가 확인된 고당도 상품입니다.")
    elif brix >= 13:
        stories.append(f"{brix:g}brix 당도 정보가 확인되어 맛 기준 비교가 가능합니다.")
    elif "고당도" in text or item.get("is_high_brix"):
        stories.append("상품명에서 고당도 신호가 확인됩니다.")

    if "GAP" in text.upper():
        stories.append("GAP 인증 또는 관련 품질 신호가 함께 확인됩니다.")

    if "유기농" in text or "무농약" in text or "친환경" in text:
        stories.append("친환경·무농약 계열 품질 신호가 포함되어 있습니다.")

    if quality_score >= 85:
        stories.append("품질 점수가 높아 단순 가격 상품보다 품질 강점이 뚜렷합니다.")
    elif quality_score >= 70:
        stories.append("품질 점수가 양호해 가격과 품질 균형을 함께 볼 수 있습니다.")

    return stories[:3]


def build_market_story(item, display=None):
    stories = []

    review_count = max(
        safe_int(item.get("review_count"), 0),
        safe_int(item.get("propagated_review_count"), 0),
    )
    rating = safe_float(item.get("rating"), 0)
    market_count = safe_int(item.get("market_price_count"), 0)
    market_label = item.get("market_cluster_label") or ""

    if market_label:
        stories.append(f"'{market_label}' 시장군 기준으로 비교되었습니다.")

    if review_count >= 9999:
        stories.append("리뷰 9,999건 이상으로 시장 반응이 매우 충분합니다.")
    elif review_count >= 1000:
        stories.append(f"리뷰 {review_count:,}건으로 구매자 반응이 확인됩니다.")
    elif review_count >= 100:
        stories.append(f"리뷰 {review_count:,}건이 있어 기본적인 구매 반응을 참고할 수 있습니다.")

    if rating >= 4.7:
        stories.append(f"평점 {rating:g}점으로 만족도 신호가 좋습니다.")
    elif rating >= 4.3:
        stories.append(f"평점 {rating:g}점으로 기본 만족도는 확인됩니다.")

    if market_count >= 5:
        stories.append(f"동일 시장 내 {market_count}개 가격 후보와 비교되었습니다.")
    elif market_count > 0:
        stories.append("동일 시장 내 비교 상품 수가 적어 가격 판단은 보조 지표로 보는 것이 좋습니다.")

    return stories[:3]


def build_delivery_story(
    item,
    display=None,
):
    stories = []
    text = get_text_blob(
        item,
        display,
    )

    if (
        "새벽배송" in text
        or "샛별배송" in text
    ):
        stories.append(
            "새벽배송 가능 신호가 확인되어 빠르게 받아볼 수 있습니다."
        )

    elif "오늘출발" in text:
        stories.append(
            "오늘출발 신호가 확인되어 배송 대기 시간을 줄일 수 있습니다."
        )

    elif "무료배송" in text:
        stories.append(
            "무료배송 혜택이 확인됩니다."
        )

    return stories[:1]

def build_trust_story(item, display=None):
    stories = []

    trust_score = safe_float(
        item.get("trust_score_final")
        or item.get("identity_v3_score")
        or item.get("_identity_score")
        or 0
    )

    if trust_score >= 85:
        stories.append("상품 식별과 시장 분류 신뢰도가 높아 비교 기준이 안정적입니다.")
    elif trust_score >= 60:
        stories.append("상품 식별은 가능하지만 옵션·상세 조건 확인은 함께 필요합니다.")
    elif trust_score > 0:
        stories.append("상품 식별 신뢰도가 낮아 상세 페이지 확인이 필요합니다.")

    return stories[:1]


def build_caution_story(item, display=None):
    cautions = []

    review_count = max(
        safe_int(item.get("review_count"), 0),
        safe_int(item.get("propagated_review_count"), 0),
    )
    rating = safe_float(item.get("rating"), 0)
    market_count = safe_int(item.get("market_price_count"), 0)

    if review_count <= 0 and rating <= 0:
        cautions.append("리뷰·평점 데이터가 부족해 사용자 만족도 판단은 제한적입니다.")

    if market_count > 0 and market_count <= 2:
        cautions.append("동일 시장 비교 상품 수가 적어 평균가 기준은 참고용으로 보는 것이 좋습니다.")

    if not (display or {}).get("ai_estimated_price") and not item.get("price"):
        cautions.append("정확한 실구매가는 판매처에서 최종 확인이 필요합니다.")

    if not cautions:
        cautions.append("현재 표시된 가격·품질 기준에서는 큰 주의 신호가 없습니다.")

    return cautions[:2]


def build_story_title(item, display=None):
    brix = get_brix_value(item, display)
    discount_rate = safe_float((display or {}).get("discount_rate") or item.get("discount_rate"), 0)
    avg_gap = safe_float(item.get("price_vs_market_avg_pct"), 0)

    if brix >= 13 and (discount_rate >= 10 or avg_gap < -5):
        return "당도와 가격 경쟁력을 함께 갖춘 추천 후보"

    if discount_rate >= 30:
        return "할인 폭이 큰 가격 경쟁형 상품"

    if brix >= 15:
        return "고당도 품질 중심 추천 후보"

    return "가격·품질 기준으로 비교한 추천 후보"


def build_story_summary(item, display=None):
    price_stories = build_price_story(item, display)
    quality_stories = build_quality_story(item, display)
    delivery_stories = build_delivery_story(item, display)

    selected = []

    if quality_stories:
        selected.append(quality_stories[0])

    if price_stories:
        selected.append(price_stories[-1] if "저렴" in price_stories[-1] else price_stories[0])

    if delivery_stories:
        selected.append(delivery_stories[0])

    if not selected:
        selected.append("가격·품질·시장 정보를 종합해 비교한 추천 후보입니다.")

    return " ".join(selected[:3])


def build_recommendation_story_v61(item, display=None):
    """Recommendation Story V6.1 통합 반환"""

    price = build_price_story(item, display)
    quality = build_quality_story(item, display)
    market = build_market_story(item, display)
    delivery = build_delivery_story(item, display)
    trust = build_trust_story(item, display)
    cautions = build_caution_story(item, display)

    story_summary = build_story_summary(item, display)

    detail_parts = []
    for group in [quality, price, delivery, market, trust]:
        for sentence in group:
            sentence = str(sentence or "").strip()
            if not sentence:
                continue

            # summary에 이미 포함된 문장은 bullet/detail에서 제외
            if sentence in story_summary:
                continue

            if sentence not in detail_parts:
                detail_parts.append(sentence)

    if not detail_parts:
        detail_parts.append("가격·품질·시장 신호를 종합해 비교한 추천 후보입니다.")

    return {
        "story_title": build_story_title(item, display),
        "story_summary": story_summary,
        "story_detail": " ".join(detail_parts[:6]),
        "price_story": price,
        "quality_story": quality,
        "market_story": market,
        "delivery_story": delivery,
        "trust_story": trust,
        "caution_story": cautions,
        "story_bullets": detail_parts[:5],
    }


def build_short_story_text(item, display=None):
    story = build_recommendation_story_v61(item, display=display)
    return story.get("story_summary") or story.get("story_title") or ""


def dedupe_text_list(items):
    result = []
    seen = set()

    for item in items or []:
        text = str(item or "").strip()
        if not text:
            continue

        normalized = re.sub(r"\s+", " ", text)

        if normalized in seen:
            continue

        seen.add(normalized)
        result.append(text)

    return result
