from app.services.food_intelligence.category_classifier import enrich_item_with_category
from app.services.food_intelligence.certification_engine import enrich_item_with_certifications
from app.services.food_intelligence.engines.fruit_engine import enrich_item_with_fruit_quality


CATEGORY_BASE_SCORES = {
    "fruit": 55,
    "vegetable": 55,
    "meat": 55,
    "seafood": 55,
    "dairy": 55,
    "processed_food": 50,
    "beverage": 50,
    "unknown": 45,
}


ATTRIBUTE_BONUS = {
    "vegan": 8,
    "organic": 8,
    "gift": 5,
}


def safe_number(value, default=0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def calculate_food_intelligence_score(item: dict) -> float:
    category = item.get("food_primary_category") or "unknown"
    attributes = item.get("food_attributes") or []
    certification_score = safe_number(item.get("food_certification_score"), 0)

    score = CATEGORY_BASE_SCORES.get(category, 45)

    for attr in attributes:
        score += ATTRIBUTE_BONUS.get(attr, 0)

    score += certification_score * 0.4

    return round(max(0, min(100, score)), 1)


def build_food_intelligence_reason(item: dict) -> str:
    category = item.get("food_primary_category") or "unknown"
    attributes = item.get("food_attributes") or []
    cert_labels = item.get("food_certification_labels") or []

    reasons = []

    if category != "unknown":
        reasons.append(f"{category} 카테고리로 분류되었습니다.")
    else:
        reasons.append("식품 카테고리 신호가 제한적입니다.")

    if attributes:
        reasons.append("속성: " + ", ".join(attributes))

    if cert_labels:
        reasons.append("인증 신호: " + ", ".join(cert_labels))

    if not cert_labels:
        reasons.append("인증 정보는 아직 확인되지 않았습니다.")

    return " ".join(reasons)


def enrich_item_with_food_intelligence(item: dict) -> dict:
    result = dict(item)

    result = enrich_item_with_category(result)
    result = enrich_item_with_certifications(result)

    result["food_intelligence_score"] = calculate_food_intelligence_score(result)
    result["food_intelligence_reason"] = build_food_intelligence_reason(result)
    
    if result.get("food_primary_category") == "fruit":
        result = enrich_item_with_fruit_quality(result)

        fruit_score = result.get("fruit_quality_score") or 0

        result["food_intelligence_score"] = round(
            result["food_intelligence_score"] * 0.45
            + fruit_score * 0.55,
            1,
        )

    result["food_intelligence_reason"] += " " + result.get("fruit_quality_reason", "")
    
    return result


def enrich_items_with_food_intelligence(items: list[dict]) -> list[dict]:
    return [
        enrich_item_with_food_intelligence(item)
        for item in items
        if isinstance(item, dict)
    ]