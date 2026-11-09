import re
from app.services.recommendation.claim_source import brix_claim_source
from app.services.food_intelligence.brix_standards import (
    SUGGESTED_TEXT_ONLY_POINTS,
    SUGGESTED_TIER_POINTS,
    classify_brix,
)


FRUIT_QUALITY_KEYWORDS = {
    "high_brix": ["고당도", "당도", "brix", "브릭스", "초고당도"],
    "premium": ["특품", "정품", "프리미엄", "명품", "선물용", "선물세트"],
    "origin": ["청송", "영주", "문경", "안동", "경북", "충주", "나주", "성주", "제주"],
    "freshness": ["산지직송", "당일수확", "당일출고", "햇", "새벽배송", "세척"],
    "variety": ["부사", "홍로", "시나노골드", "감홍", "아오리", "루비에스", "샤인머스캣"],
    "risk": ["못난이", "흠과", "흠집", "랜덤", "혼합", "소과"],
}


def normalize_text(text: str) -> str:
    text = text or ""
    text = text.lower()
    text = re.sub(r"[^가-힣a-z0-9\s\.]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_brix(text: str) -> float:
    text = text or ""

    patterns = [
        r"(\d+(?:\.\d+)?)\s*brix",
        r"(\d+(?:\.\d+)?)\s*브릭스",
        r"(\d+(?:\.\d+)?)\s*bx",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except Exception:
                return 0

    return 0


TIER_LABEL = {"top": "최상", "high": "고당도", "normal": "보통", "below": "출하 하한 미만"}

_TEXT_ONLY_WORDS = ["초고당도", "고당도", "당도"]


def _legacy_score_brix(brix: float, normalized: str) -> float:
    """품종 기준표에 없는 상품: 2026-11-04 이전과 같은 고정 구간."""
    if brix >= 16:
        return 30
    if brix >= 15:
        return 26
    if brix >= 14:
        return 22
    if brix >= 13:
        return 16

    if any(word in normalized for word in _TEXT_ONLY_WORDS):
        return 14

    return 0


def judge_brix(brix: float, text: str) -> dict:
    """Brix 가점과 판정 근거.

    2026-11-04: 품종별 기준표(brix_standards)에 있는 과일은 그 품종의 고당도·최상 기준으로 판정한다.
    숫자 없는 '고당도' 문구는 숫자로 적은 '보통'보다 낮은 가점을 준다.
    기준표에 없는 상품은 이전 고정 구간을 그대로 쓴다.
    """
    normalized = normalize_text(text)
    judged = classify_brix(text, brix)
    standard = judged["standard"]

    if standard is None:
        return {"points": _legacy_score_brix(brix, normalized), "tier": None, "standard": None}

    tier = judged["tier"]
    if tier == "no_value":
        text_only = any(word in normalized for word in _TEXT_ONLY_WORDS)
        return {
            "points": SUGGESTED_TEXT_ONLY_POINTS if text_only else 0,
            "tier": "text_only" if text_only else None,
            "standard": standard,
        }

    return {"points": SUGGESTED_TIER_POINTS[tier], "tier": tier, "standard": standard}


def score_brix(brix: float, text: str) -> float:
    return judge_brix(brix, text)["points"]


def _standard_label(standard) -> str:
    return standard.variety or f"{standard.fruit} 공통"


def keyword_score(text: str, keywords: list[str], score_per_match: float, max_score: float) -> float:
    normalized = normalize_text(text)
    score = 0

    for keyword in keywords:
        if normalize_text(keyword) in normalized:
            score += score_per_match

    return min(score, max_score)


def calculate_fruit_quality(item: dict) -> dict:
    name = (
        item.get("product_name")
        or item.get("name")
        or ""
    )

    brix = extract_brix(name)

    brix_judgement = judge_brix(brix, name)
    brix_score = brix_judgement["points"]
    brix_tier = brix_judgement["tier"]
    brix_standard = brix_judgement["standard"]

    premium_score = keyword_score(
        name,
        FRUIT_QUALITY_KEYWORDS["premium"],
        4,
        12,
    )

    origin_score = keyword_score(
        name,
        FRUIT_QUALITY_KEYWORDS["origin"],
        3,
        12,
    )

    freshness_score = keyword_score(
        name,
        FRUIT_QUALITY_KEYWORDS["freshness"],
        3,
        12,
    )

    variety_score = keyword_score(
        name,
        FRUIT_QUALITY_KEYWORDS["variety"],
        3,
        9,
    )

    risk_penalty = keyword_score(
        name,
        FRUIT_QUALITY_KEYWORDS["risk"],
        4,
        12,
    )

    base = 45

    score = (
        base
        + brix_score
        + premium_score
        + origin_score
        + freshness_score
        + variety_score
        - risk_penalty
    )

    score = round(max(0, min(100, score)), 1)

    reasons = []

    if brix:
        if brix_claim_source(item, brix) == "seller_page_claim":
            reasons.append(f"상품명·상세 설명에 {brix:g}brix로 표기되어 있습니다. 실제 당도는 확인되지 않았습니다.")
        else:
            reasons.append(f"Brix 입력값 {brix:g}의 출처와 실제 당도는 확인되지 않았습니다.")
        if brix_standard is not None and brix_tier in TIER_LABEL:
            reasons.append(
                f"표기값은 {_standard_label(brix_standard)} 기준 {TIER_LABEL[brix_tier]} 구간입니다 "
                f"(고당도 {brix_standard.high:g}·최상 {brix_standard.top:g} 이상)."
            )
    elif brix_score:
        if brix_claim_source(item) == "seller_page_claim":
            reasons.append("상품명·상세 설명에 고당도로 표기되어 있습니다. 실제 당도는 확인되지 않았습니다.")
        else:
            reasons.append("고당도 입력값의 출처와 실제 당도는 확인되지 않았습니다.")

    if premium_score:
        reasons.append("특품·정품·프리미엄 등급 신호가 있습니다.")

    if origin_score:
        reasons.append("산지 정보가 확인되었습니다.")

    if freshness_score:
        reasons.append("산지직송·당일출고·세척 등 신선도 신호가 있습니다.")

    if variety_score:
        reasons.append("품종 정보가 확인되었습니다.")

    if risk_penalty:
        reasons.append("못난이·흠과·혼합 등 품질 리스크 신호도 있습니다.")

    if not reasons:
        reasons.append("과일 품질 신호는 제한적입니다.")

    return {
        "fruit_quality_score": score,
        "fruit_brix": brix,
        "fruit_brix_score": brix_score,
        "fruit_brix_tier": brix_tier,
        "fruit_brix_standard": _standard_label(brix_standard) if brix_standard else None,
        "fruit_premium_score": premium_score,
        "fruit_origin_score": origin_score,
        "fruit_freshness_score": freshness_score,
        "fruit_variety_score": variety_score,
        "fruit_risk_penalty": risk_penalty,
        "fruit_quality_reason": " ".join(reasons),
    }


def enrich_item_with_fruit_quality(item: dict) -> dict:
    result = dict(item)
    result.update(calculate_fruit_quality(result))
    return result


def enrich_items_with_fruit_quality(items: list[dict]) -> list[dict]:
    return [
        enrich_item_with_fruit_quality(item)
        for item in items
        if isinstance(item, dict)
    ]
