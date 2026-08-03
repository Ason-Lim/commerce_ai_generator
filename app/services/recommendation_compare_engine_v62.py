"""
Recommendation Compare Engine V6.2

역할:
- Hero 1위 상품과 다른 후보 상품을 비교합니다.
- 가격, 100g당 가격, Brix/품질, 배송, 리뷰/평점, 할인율 차이를 자연어로 설명합니다.
- Hero, 상품 카드, PDF, API에서 공통으로 사용할 수 있는 compare 객체를 반환합니다.
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
    value = safe_float(value, 0)
    if value <= 0:
        return ""
    return f"{int(round(value)):,}원"


def get_text_blob(item, display=None):
    values = []
    for key in [
        "product_name", "raw_name", "title", "seller_name", "mall_name",
        "platform_name", "market_cluster_label", "market_quality_band",
        "market_gift_band", "market_attribute_band",
    ]:
        value = item.get(key)
        if value:
            values.append(str(value))

    if display:
        for key in ["name", "seller_text", "brix_text", "weight_text", "platform_label"]:
            value = display.get(key)
            if value:
                values.append(str(value))

    return " ".join(values)


def get_effective_price(item, display=None):
    display = display or {}
    for key in ["ai_estimated_price", "benefit_price", "max_benefit_price", "member_price", "sale_price", "price"]:
        value = display.get(key) if key in display else item.get(key)
        value = safe_float(value, 0)
        if value > 0:
            return value
    return 0


def get_unit_price(item, display=None):
    display = display or {}
    for key in ["price_per_100g", "unit_price_100g", "unit_price_per_100g"]:
        value = display.get(key) if key in display else item.get(key)
        value = safe_float(value, 0)
        if value > 0:
            return value

    price = get_effective_price(item, display)
    weight_g = safe_float(display.get("weight_g") or item.get("weight_g"), 0)
    if price > 0 and weight_g > 0:
        return price / weight_g * 100
    return 0


def get_brix_value(item, display=None):
    display = display or {}
    candidates = [
        display.get("brix"), display.get("brix_value"), item.get("brix"),
        item.get("brix_value"), item.get("avg_brix"), item.get("max_brix"),
        item.get("display_brix"),
    ]
    for value in candidates:
        value = safe_float(value, 0)
        if value > 0:
            return value

    text = get_text_blob(item, display).lower()
    patterns = [
        r"(\d{2}(?:\.\d+)?)\s*brix",
        r"(\d{2}(?:\.\d+)?)\s*브릭스",
        r"당도\s*(\d{2}(?:\.\d+)?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = safe_float(match.group(1), 0)
            if 8 <= value <= 30:
                return value
    return 0


def has_high_sugar_signal(item, display=None):
    text = get_text_blob(item, display)
    return (
        get_brix_value(item, display) >= 13
        or "고당도" in text
        or "꿀사과" in text
        or "당도" in text
        or bool(item.get("is_high_brix"))
    )


def has_dawn_delivery(item, display=None):
    text = get_text_blob(item, display)
    return "새벽배송" in text or "샛별배송" in text or "컬리" in text


def get_discount_rate(item, display=None):
    display = display or {}
    return safe_float(display.get("discount_rate") or item.get("discount_rate"), 0)


def get_review_count(item):
    return max(safe_int(item.get("review_count"), 0), safe_int(item.get("propagated_review_count"), 0))


def get_rating(item):
    return safe_float(item.get("rating"), 0)


def compare_price(top_item, other_item, top_display=None, other_display=None):
    top_price = get_effective_price(top_item, top_display)
    other_price = get_effective_price(other_item, other_display)
    if top_price <= 0 or other_price <= 0:
        return None

    diff = other_price - top_price
    if abs(diff) < 500:
        return "구매 기준가는 주요 후보와 큰 차이가 없습니다."
    if diff > 0:
        return f"1위 상품이 비교 후보보다 구매 기준가 기준 {fmt_money(diff)} 저렴합니다."
    return f"비교 후보가 1위 상품보다 구매 기준가 기준 {fmt_money(abs(diff))} 저렴합니다."


def compare_unit_price(top_item, other_item, top_display=None, other_display=None):
    top_unit = get_unit_price(top_item, top_display)
    other_unit = get_unit_price(other_item, other_display)
    if top_unit <= 0 or other_unit <= 0:
        return None

    diff = other_unit - top_unit
    if abs(diff) < 30:
        return "100g당 가격은 주요 후보와 비슷한 수준입니다."
    if diff > 0:
        return f"1위 상품이 100g당 약 {fmt_money(diff)} 더 저렴합니다."
    return f"비교 후보가 100g당 약 {fmt_money(abs(diff))} 더 저렴합니다."


def compare_quality(top_item, other_item, top_display=None, other_display=None):
    top_brix = get_brix_value(top_item, top_display)
    other_brix = get_brix_value(other_item, other_display)
    top_high = has_high_sugar_signal(top_item, top_display)
    other_high = has_high_sugar_signal(other_item, other_display)

    if top_brix and other_brix:
        if top_brix > other_brix:
            return f"1위 상품은 {top_brix:g}brix로 비교 후보보다 당도 정보가 더 높습니다."
        if other_brix > top_brix:
            return f"비교 후보는 {other_brix:g}brix로 당도 수치만 보면 더 높습니다."
        return f"두 상품 모두 {top_brix:g}brix 당도 정보가 확인됩니다."
    if top_brix and not other_brix:
        return f"1위 상품은 {top_brix:g}brix 당도 수치가 확인되어 품질 비교가 더 명확합니다."
    if other_brix and not top_brix:
        return f"비교 후보는 {other_brix:g}brix 당도 수치가 확인되어 품질 정보가 더 구체적입니다."
    if top_high and not other_high:
        return "1위 상품은 고당도 신호가 확인되지만 비교 후보는 당도 정보가 약합니다."
    if other_high and not top_high:
        return "비교 후보는 고당도 신호가 확인되지만 1위 상품은 당도 정보가 약합니다."
    return None


def compare_delivery(top_item, other_item, top_display=None, other_display=None):
    top_dawn = has_dawn_delivery(top_item, top_display)
    other_dawn = has_dawn_delivery(other_item, other_display)
    if top_dawn and not other_dawn:
        return "1위 상품은 새벽배송/컬리 계열 배송 편의성이 있어 배송 측면에서 유리합니다."
    if other_dawn and not top_dawn:
        return "비교 후보는 새벽배송 신호가 있어 배송 편의성은 더 좋을 수 있습니다."
    if top_dawn and other_dawn:
        return "두 상품 모두 새벽배송 또는 컬리 계열 배송 편의성을 기대할 수 있습니다."
    return None


def compare_market_signal(top_item, other_item):
    top_review = get_review_count(top_item)
    other_review = get_review_count(other_item)
    top_rating = get_rating(top_item)
    other_rating = get_rating(other_item)

    if top_review >= 1000 and top_review > other_review * 1.5:
        return f"1위 상품은 리뷰 {top_review:,}건으로 비교 후보보다 시장 반응이 더 풍부합니다."
    if other_review >= 1000 and other_review > top_review * 1.5:
        return f"비교 후보는 리뷰 {other_review:,}건으로 시장 반응이 더 풍부합니다."
    if top_rating >= 4.7 and top_rating > other_rating:
        return f"1위 상품은 평점 {top_rating:g}점으로 만족도 신호가 더 좋습니다."
    if other_rating >= 4.7 and other_rating > top_rating:
        return f"비교 후보는 평점 {other_rating:g}점으로 만족도 신호가 더 좋습니다."
    return None


def compare_discount(top_item, other_item, top_display=None, other_display=None):
    top_discount = get_discount_rate(top_item, top_display)
    other_discount = get_discount_rate(other_item, other_display)
    if top_discount <= 0 and other_discount <= 0:
        return None
    if top_discount >= other_discount + 10:
        return f"1위 상품은 할인율이 약 {top_discount:.1f}%로 비교 후보보다 할인 폭이 큽니다."
    if other_discount >= top_discount + 10:
        return f"비교 후보는 할인율이 약 {other_discount:.1f}%로 할인 폭은 더 큽니다."
    return None


def build_pair_compare_v62(top_item, other_item, top_display=None, other_display=None):
    bullets = []
    checks = [
        compare_price, compare_unit_price, compare_quality,
        compare_delivery, compare_market_signal, compare_discount,
    ]

    for fn in checks:
        try:
            if fn.__name__ == "compare_market_signal":
                sentence = fn(top_item, other_item)
            else:
                sentence = fn(top_item, other_item, top_display, other_display)
            if sentence and sentence not in bullets:
                bullets.append(sentence)
        except Exception:
            continue

    if not bullets:
        bullets.append("두 상품은 가격·품질 신호가 비슷해 상세 옵션을 함께 비교하는 것이 좋습니다.")

    advantage_count = sum(1 for b in bullets if b.startswith("1위 상품") or "1위 상품이" in b)
    caution_count = sum(1 for b in bullets if b.startswith("비교 후보") or "후보가" in b)

    if advantage_count > caution_count:
        summary = "1위 상품이 가격·품질·편의성 중 일부 기준에서 더 유리합니다."
    elif caution_count > advantage_count:
        summary = "비교 후보도 일부 기준에서는 더 나은 장점이 있습니다."
    else:
        summary = "두 상품은 장단점이 나뉘어 구매 기준에 따라 선택이 달라질 수 있습니다."

    return {
        "compare_summary": summary,
        "compare_bullets": bullets[:5],
        "advantage_count": advantage_count,
        "caution_count": caution_count,
    }


def build_hero_compare_v62(top_item, compare_items, top_display=None, compare_displays=None):
    compare_items = compare_items or []
    compare_displays = compare_displays or {}
    all_bullets = []
    pair_summaries = []

    for idx, other_item in enumerate(compare_items[:3], start=2):
        key = id(other_item)
        other_display = compare_displays.get(key) or compare_displays.get(idx) or None
        pair = build_pair_compare_v62(top_item, other_item, top_display=top_display, other_display=other_display)
        pair_summaries.append(f"{idx}위 후보 비교: {pair['compare_summary']}")
        for bullet in pair["compare_bullets"]:
            if bullet not in all_bullets:
                all_bullets.append(bullet)

    if not all_bullets:
        all_bullets.append("1위 상품은 가격·품질·시장 신호를 종합해 우선 추천되었습니다.")

    top_positive = [b for b in all_bullets if b.startswith("1위 상품") or "1위 상품이" in b]
    summary = "1위 상품을 다른 후보와 가격·품질·배송 기준으로 비교했습니다."
    if top_positive:
        summary = "1위 상품은 다른 후보보다 일부 핵심 기준에서 더 유리합니다."

    return {
        "compare_title": "AI 비교 분석",
        "compare_summary": summary,
        "compare_bullets": all_bullets[:5],
        "pair_summaries": pair_summaries[:3],
        "compare_score": min(100, 60 + len(top_positive) * 10),
    }


def build_item_compare_v62(item, top_item, item_display=None, top_display=None):
    pair = build_pair_compare_v62(top_item, item, top_display=top_display, other_display=item_display)
    bullets = []

    for bullet in pair.get("compare_bullets", []):
        if bullet.startswith("1위 상품은"):
            bullets.append(bullet.replace("1위 상품은", "1위와 비교하면 이 상품은"))
        elif bullet.startswith("1위 상품이"):
            bullets.append(bullet.replace("1위 상품이", "1위 상품이"))
        elif bullet.startswith("비교 후보는"):
            bullets.append(bullet.replace("비교 후보는", "이 상품은"))
        elif bullet.startswith("비교 후보가"):
            bullets.append(bullet.replace("비교 후보가", "이 상품이"))
        else:
            bullets.append(bullet)

    return {
        "compare_title": "1위 상품과 비교",
        "compare_summary": pair.get("compare_summary"),
        "compare_bullets": bullets[:4],
        "compare_score": pair.get("advantage_count", 0) * 20 - pair.get("caution_count", 0) * 10,
    }


def build_short_compare_text(top_item, compare_items, top_display=None):
    compare = build_hero_compare_v62(top_item, compare_items, top_display=top_display)
    bullets = compare.get("compare_bullets") or []
    if bullets:
        return bullets[0]
    return compare.get("compare_summary", "")
