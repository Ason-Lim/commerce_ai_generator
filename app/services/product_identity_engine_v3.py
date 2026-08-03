
import hashlib
import re
from difflib import SequenceMatcher
from urllib.parse import urlparse


FRUIT_KEYWORDS = {
    "사과": ["사과", "부사", "홍로", "감홍", "시나노", "아오리", "엔비", "피치애플", "문루즈"],
    "배": ["배", "신고배", "황금배"],
    "샤인머스캣": ["샤인머스캣", "샤인머스켓", "망고포도", "청포도"],
    "감귤": ["감귤", "귤", "밀감", "천혜향", "한라봉", "레드향"],
    "딸기": ["딸기", "설향", "금실"],
}

GRADE_KEYWORDS = {
    "못난이": ["못난이", "흠과", "흠집", "기스", "가정용", "실속", "파지"],
    "선물용": ["선물", "선물세트", "명절", "프리미엄", "특품", "고급", "특선"],
    "프리미엄": ["프리미엄", "특품", "특상", "상급", "고급", "GAP", "gap"],
    "세척": ["세척", "씻어나온", "세척사과"],
}

ORIGIN_KEYWORDS = [
    "청송", "안동", "문경", "영주", "경북", "밀양", "얼음골", "충주", "봉화",
    "거창", "무주", "강원", "제주", "나주", "성주", "김천", "영천",
]

DELIVERY_KEYWORDS = {
    "새벽배송": ["새벽배송", "샛별배송"],
    "산지직송": ["산지직송", "농가직송", "농장직송", "직송"],
    "택배배송": ["택배", "무료배송", "배송"],
}


def clean_text(value):
    value = str(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    value = value.replace("&nbsp;", " ")
    value = value.replace("&amp;", "&")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_text(value):
    value = clean_text(value).lower()
    value = re.sub(r"[\[\]\(\)\{\},./_+\-|·:;!?'\"~]", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def get_text_blob(item):
    return " ".join(
        clean_text(item.get(k))
        for k in [
            "product_name",
            "name",
            "raw_name",
            "title",
            "description",
            "seller_name",
            "mall_name",
            "platform_name",
            "brand",
            "maker",
        ]
        if item.get(k)
    )


def extract_domain(url):
    try:
        parsed = urlparse(str(url or ""))
        return parsed.netloc.lower().replace("www.", "")
    except Exception:
        return ""


def extract_fruit(text):
    normalized = normalize_text(text)
    for fruit, aliases in FRUIT_KEYWORDS.items():
        if any(alias.lower() in normalized for alias in aliases):
            return fruit
    return None


def extract_weight_g(text):
    text = normalize_text(text).replace(",", "")
    text = text.replace("㎏", "kg")
    matches = re.findall(r"(\d+(?:\.\d+)?)\s*(kg|g|키로|킬로)", text, re.IGNORECASE)
    if not matches:
        return None

    candidates = []
    for value, unit in matches:
        try:
            amount = float(value)
        except Exception:
            continue

        unit = unit.lower()
        grams = int(amount * 1000) if unit in ["kg", "키로", "킬로"] else int(amount)
        if 50 <= grams <= 50000:
            candidates.append(grams)

    if not candidates:
        return None

    return min(candidates)


def extract_brix(text):
    text = normalize_text(text)
    patterns = [
        r"(\d{2}(?:\.\d+)?)\s*brix",
        r"(\d{2}(?:\.\d+)?)\s*브릭스",
        r"(\d{2}(?:\.\d+)?)\s*당도",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except Exception:
                pass

    return None


def extract_grade(text):
    normalized = normalize_text(text)
    found = []
    for grade, keywords in GRADE_KEYWORDS.items():
        if any(keyword.lower() in normalized for keyword in keywords):
            found.append(grade)
    return found


def extract_origin(text):
    normalized = normalize_text(text)
    found = []
    for origin in ORIGIN_KEYWORDS:
        if origin.lower() in normalized:
            found.append(origin)
    return found[:3]


def extract_delivery_type(text):
    normalized = normalize_text(text)
    found = []
    for delivery_type, keywords in DELIVERY_KEYWORDS.items():
        if any(keyword.lower() in normalized for keyword in keywords):
            found.append(delivery_type)
    return found


def extract_brand_hint(item, text):
    for key in ["brand", "maker", "seller_name", "mall_name"]:
        value = clean_text(item.get(key))
        if value:
            return value

    match = re.search(r"\[([^\]]+)\]", str(text or ""))
    if match:
        return clean_text(match.group(1))

    return None


def get_product_url(item):
    return clean_text(
        item.get("redirect_url")
        or item.get("product_url")
        or item.get("url")
        or item.get("raw_link")
        or item.get("search_url")
        or ""
    )


def is_search_url(url):
    url = str(url or "").lower()
    return "search" in url and ("kurly.com" in url or "naver.com" in url)


def calculate_name_similarity(a, b):
    a = normalize_text(a)
    b = normalize_text(b)
    if not a or not b:
        return 0
    return round(SequenceMatcher(None, a, b).ratio() * 100, 1)


def build_identity_fingerprint(parts):
    raw_parts = [
        parts.get("fruit") or "",
        str(parts.get("weight_g") or ""),
        str(parts.get("brix") or ""),
        "|".join(parts.get("grade") or []),
        "|".join(parts.get("origin") or []),
        normalize_text(parts.get("brand_hint") or ""),
        parts.get("mall_product_id") or "",
    ]
    raw = "::".join(raw_parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def calculate_identity_v3_score(item, parts):
    score = 0
    reasons = []

    if parts.get("mall_product_id"):
        score += 25
        reasons.append("상품번호 확인")

    url = get_product_url(item)
    domain = extract_domain(url)

    if url and not is_search_url(url):
        score += 15
        reasons.append("상세 URL 확인")
    elif is_search_url(url):
        score -= 20
        reasons.append("검색 URL 주의")
    else:
        score -= 10
        reasons.append("URL 없음")

    if parts.get("fruit"):
        score += 10
        reasons.append(f"과일 식별: {parts['fruit']}")

    if parts.get("weight_g"):
        score += 15
        reasons.append(f"중량 식별: {parts['weight_g']}g")

    if parts.get("brix"):
        score += 15
        reasons.append(f"Brix 식별: {parts['brix']:g}")

    if parts.get("origin"):
        score += 8
        reasons.append("산지 정보 확인")

    if parts.get("grade"):
        score += 7
        reasons.append("등급/용도 정보 확인")

    if parts.get("brand_hint"):
        score += 5
        reasons.append("브랜드/판매처 정보 확인")

    if domain:
        score += 5
        reasons.append("도메인 확인")

    score = max(0, min(100, score))

    if score >= 85:
        label = "🟢 동일 상품 가능성 높음"
        grade = "high"
        penalty = 0
    elif score >= 70:
        label = "🟡 유사 상품"
        grade = "medium"
        penalty = 5
    elif score >= 55:
        label = "🟠 상품 식별 주의"
        grade = "low"
        penalty = 15
    else:
        label = "🔴 검색 기반 추천"
        grade = "weak"
        penalty = 30

    return {
        "identity_v3_score": score,
        "identity_v3_label": label,
        "identity_v3_grade": grade,
        "identity_v3_penalty": penalty,
        "identity_v3_reasons": reasons,
    }


def extract_identity_parts(item):
    text = get_text_blob(item)
    product_url = get_product_url(item)

    parts = {
        "fruit": extract_fruit(text),
        "weight_g": item.get("weight_g") or extract_weight_g(text),
        "brix": item.get("brix_value") or item.get("brix") or extract_brix(text),
        "grade": extract_grade(text),
        "origin": extract_origin(text),
        "delivery_type": extract_delivery_type(text),
        "brand_hint": extract_brand_hint(item, text),
        "mall_product_id": str(item.get("mall_product_id") or "").strip() or None,
        "domain": extract_domain(product_url),
        "is_search_url": is_search_url(product_url),
    }

    try:
        if parts["weight_g"]:
            parts["weight_g"] = int(float(parts["weight_g"]))
    except Exception:
        parts["weight_g"] = extract_weight_g(text)

    try:
        if parts["brix"]:
            parts["brix"] = float(parts["brix"])
    except Exception:
        parts["brix"] = extract_brix(text)

    parts["identity_fingerprint"] = build_identity_fingerprint(parts)
    return parts


def enrich_identity_v3(item):
    parts = extract_identity_parts(item)
    score_payload = calculate_identity_v3_score(item, parts)

    enriched = dict(item)
    enriched["_identity_v3"] = {**parts, **score_payload}
    enriched["identity_fingerprint"] = parts["identity_fingerprint"]
    enriched["identity_v3_score"] = score_payload["identity_v3_score"]
    enriched["identity_v3_label"] = score_payload["identity_v3_label"]
    enriched["identity_v3_penalty"] = score_payload["identity_v3_penalty"]

    if not enriched.get("fruit_name") and parts.get("fruit"):
        enriched["fruit_name"] = parts.get("fruit")
    if not enriched.get("weight_g") and parts.get("weight_g"):
        enriched["weight_g"] = parts.get("weight_g")
    if not enriched.get("brix_value") and parts.get("brix"):
        enriched["brix_value"] = parts.get("brix")

    return enriched


def apply_identity_v3_penalty(score, item):
    identity = item.get("_identity_v3") or enrich_identity_v3(item).get("_identity_v3", {})
    try:
        score = float(score or 0)
    except Exception:
        score = 0

    return max(0, round(score - float(identity.get("identity_v3_penalty") or 0), 1))
