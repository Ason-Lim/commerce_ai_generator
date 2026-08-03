import re


CERTIFICATION_KEYWORDS = {
    "gap": ["gap", "GAP", "농산물우수관리"],
    "haccp": ["haccp", "HACCP", "해썹"],
    "organic": ["유기농", "organic", "오가닉"],
    "pesticide_free": ["무농약"],
    "eco_friendly": ["친환경", "저탄소"],
    "vegan_certified": ["비건인증", "비건 인증", "한국비건인증원", "v-label", "브이라벨"],
    "non_gmo": ["non-gmo", "nongmo", "비유전자변형"],
    "animal_welfare": ["동물복지"],
    "msc": ["msc", "MSC"],
    "asc": ["asc", "ASC"],
}


CERTIFICATION_LABELS = {
    "gap": "GAP",
    "haccp": "HACCP",
    "organic": "유기농",
    "pesticide_free": "무농약",
    "eco_friendly": "친환경",
    "vegan_certified": "비건 인증",
    "non_gmo": "Non-GMO",
    "animal_welfare": "동물복지",
    "msc": "MSC",
    "asc": "ASC",
}


CERTIFICATION_WEIGHTS = {
    "gap": 12,
    "haccp": 10,
    "organic": 14,
    "pesticide_free": 10,
    "eco_friendly": 8,
    "vegan_certified": 12,
    "non_gmo": 8,
    "animal_welfare": 10,
    "msc": 10,
    "asc": 10,
}


def normalize_text(text: str) -> str:
    text = text or ""
    text = text.lower()
    text = re.sub(r"[^가-힣a-z0-9\s\-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def detect_certifications(text: str) -> dict:
    normalized = normalize_text(text)

    found = []
    score = 0

    for cert_key, keywords in CERTIFICATION_KEYWORDS.items():
        for keyword in keywords:
            keyword_normalized = normalize_text(keyword)

            if keyword_normalized and keyword_normalized in normalized:
                found.append(
                    {
                        "key": cert_key,
                        "label": CERTIFICATION_LABELS.get(cert_key, cert_key),
                        "matched_keyword": keyword,
                        "score": CERTIFICATION_WEIGHTS.get(cert_key, 5),
                    }
                )
                score += CERTIFICATION_WEIGHTS.get(cert_key, 5)
                break

    score = min(100, score)

    return {
        "certification_score": score,
        "certifications": found,
        "certification_labels": [item["label"] for item in found],
        "has_certification": bool(found),
    }


def enrich_item_with_certifications(item: dict) -> dict:
    result = dict(item)

    text = " ".join(
        [
            str(result.get("product_name") or ""),
            str(result.get("name") or ""),
            str(result.get("seller_name") or ""),
            str(result.get("mall_name") or ""),
        ]
    )

    cert_info = detect_certifications(text)

    result["food_certification_score"] = cert_info["certification_score"]
    result["food_certifications"] = cert_info["certifications"]
    result["food_certification_labels"] = cert_info["certification_labels"]
    result["has_food_certification"] = cert_info["has_certification"]

    return result


def enrich_items_with_certifications(items: list[dict]) -> list[dict]:
    return [
        enrich_item_with_certifications(item)
        for item in items
        if isinstance(item, dict)
    ]
