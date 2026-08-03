import re


CATEGORY_KEYWORDS = {
    "fruit": [
        "사과", "배", "감귤", "귤", "오렌지", "바나나", "포도", "샤인머스캣",
        "딸기", "블루베리", "체리", "복숭아", "자두", "수박", "멜론",
        "망고", "키위", "무화과", "석류", "레몬", "라임",
    ],
    "vegetable": [
        "상추", "깻잎", "배추", "양배추", "시금치", "부추", "오이", "호박",
        "당근", "감자", "고구마", "양파", "마늘", "파", "대파", "토마토",
        "브로콜리", "파프리카", "버섯", "새송이", "표고", "가지",
    ],
    "meat": [
        "한우", "소고기", "쇠고기", "돼지고기", "삼겹살", "목살", "갈비",
        "닭고기", "닭가슴살", "오리고기", "양고기", "스테이크", "불고기",
    ],
    "seafood": [
        "고등어", "갈치", "광어", "연어", "참치", "오징어", "문어", "낙지",
        "새우", "대하", "전복", "굴", "홍합", "조개", "게", "킹크랩",
    ],
    "dairy": [
        "우유", "치즈", "요거트", "요구르트", "버터", "크림", "그릭요거트",
    ],
    "processed_food": [
        "라면", "만두", "두부", "햄", "소시지", "참치캔", "김치", "반찬",
        "즉석밥", "시리얼", "오트밀", "빵", "과자", "스낵", "소스",
        "드레싱", "잼", "꿀", "프로틴바",
    ],
    "beverage": [
        "커피", "차", "녹차", "홍차", "주스", "음료", "탄산", "생수",
        "귀리우유", "아몬드브리즈", "두유", "오트밀크", "오트 밀크",
    ],
    "vegan": [
        "비건", "vegan", "식물성", "대체육", "콩고기", "두유", "귀리우유",
        "오트밀크", "오트 밀크", "아몬드밀크", "식물성 단백질",
    ],
    "organic": [
        "유기농", "무농약", "친환경", "organic", "저탄소", "gap",
    ],
    "gift": [
        "선물", "선물세트", "명절", "부모님", "프리미엄", "특품", "정품",
        "세트", "답례품",
    ],
}


PRIMARY_PRIORITY = [
    "fruit",
    "vegetable",
    "meat",
    "seafood",
    "beverage",
    "processed_food",
    "dairy",
]


ATTRIBUTE_CATEGORIES = {
    "vegan",
    "organic",
    "gift",
}


def normalize_text(text: str) -> str:
    text = text or ""
    text = text.lower()
    text = re.sub(r"[^가-힣a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def score_category(text: str, category: str) -> int:
    normalized = normalize_text(text)
    score = 0

    for keyword in CATEGORY_KEYWORDS.get(category, []):
        keyword_normalized = normalize_text(keyword)

        if not keyword_normalized:
            continue

        if keyword_normalized in normalized:
            score += 3

        if normalized == keyword_normalized:
            score += 5

    return score


def classify_food_category(text: str) -> dict:
    normalized = normalize_text(text)

    scores = {
        category: score_category(normalized, category)
        for category in CATEGORY_KEYWORDS.keys()
    }

        # 식물성 음료 보정
    plant_based_beverage_keywords = [
        "귀리우유",
        "오트밀크",
        "오트 밀크",
        "아몬드밀크",
        "아몬드 브리즈",
        "두유",
    ]

    if any(keyword in normalized for keyword in plant_based_beverage_keywords):
        scores["beverage"] += 5
        scores["vegan"] += 3
        scores["dairy"] = 0

    matched_categories = [
        category
        for category, score in scores.items()
        if score > 0
    ]    

    primary_category = "unknown"

    for category in PRIMARY_PRIORITY:
        if scores.get(category, 0) > 0:
            primary_category = category
            break

    attributes = [
        category
        for category in ATTRIBUTE_CATEGORIES
        if scores.get(category, 0) > 0
    ]

    confidence = 0

    if primary_category != "unknown":
        confidence = min(100, 50 + scores.get(primary_category, 0) * 10)

    return {
        "input_text": text,
        "normalized_text": normalized,
        "primary_category": primary_category,
        "attributes": attributes,
        "matched_categories": matched_categories,
        "category_scores": scores,
        "confidence": confidence,
    }


def classify_item_category(item: dict) -> dict:
    name = (
        item.get("product_name")
        or item.get("name")
        or item.get("keyword")
        or ""
    )

    return classify_food_category(name)


def enrich_item_with_category(item: dict) -> dict:
    result = dict(item)
    category_info = classify_item_category(result)

    result["food_primary_category"] = category_info["primary_category"]
    result["food_attributes"] = category_info["attributes"]
    result["food_category_confidence"] = category_info["confidence"]
    result["food_category_scores"] = category_info["category_scores"]

    return result


def enrich_items_with_category(items: list[dict]) -> list[dict]:
    return [
        enrich_item_with_category(item)
        for item in items
        if isinstance(item, dict)
    ]
