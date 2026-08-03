import re


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


def score_brix(brix: float, text: str) -> float:
    normalized = normalize_text(text)

    if brix >= 16:
        return 30
    if brix >= 15:
        return 26
    if brix >= 14:
        return 22
    if brix >= 13:
        return 16

    if any(word in normalized for word in ["초고당도", "고당도", "당도"]):
        return 14

    return 0


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

    brix_score = score_brix(brix, name)

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
        reasons.append(f"{brix:g}brix 당도 수치가 확인되었습니다.")
    elif brix_score:
        reasons.append("고당도 표현이 확인되었습니다.")

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
