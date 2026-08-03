
import hashlib
import re
from difflib import SequenceMatcher
from urllib.parse import urlparse


def clean_text(value):
    value = str(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_text(value):
    value = clean_text(value).lower()
    value = re.sub(r"[\[\]\(\)\{\},./_+\-|·]", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_seller(value):
    value = normalize_text(value)
    value = value.replace("네이버", "")
    value = value.replace("쇼핑", "")
    value = value.replace("마켓", "")
    value = value.replace("스토어", "")
    value = value.replace("n마트", "n마트")
    return value.strip()


def extract_domain(url):
    url = clean_text(url)

    if not url:
        return ""

    try:
        parsed = urlparse(url)
        return parsed.netloc.lower().replace("www.", "")
    except Exception:
        return ""


def parse_weight_g(value):
    value = normalize_text(value).replace(",", "")
    value = value.replace("㎏", "kg")

    match = re.search(r"(\d+(?:\.\d+)?)\s*kg", value)
    if match:
        return int(float(match.group(1)) * 1000)

    match = re.search(r"(\d+(?:\.\d+)?)\s*g", value)
    if match:
        return int(float(match.group(1)))

    return None


def get_weight_g(item):
    for key in ["weight_g", "weight_gram", "product_weight_g"]:
        try:
            value = item.get(key)
            if value:
                return int(float(value))
        except Exception:
            pass

    for key in ["weight_text", "weight", "product_name", "raw_name", "title", "name"]:
        value = parse_weight_g(item.get(key))
        if value:
            return value

    try:
        weight_kg = item.get("weight_kg")
        if weight_kg:
            return int(float(weight_kg) * 1000)
    except Exception:
        pass

    return None


def get_brix_value(item):
    for key in ["brix", "brix_value"]:
        try:
            value = item.get(key)
            if value:
                return float(value)
        except Exception:
            pass

    raw = " ".join(
        str(item.get(k) or "")
        for k in ["product_name", "raw_name", "title", "name", "description"]
    ).lower()

    match = re.search(r"(\d{2}(?:\.\d+)?)\s*brix", raw)
    if match:
        return float(match.group(1))

    match = re.search(r"(\d{2}(?:\.\d+)?)\s*브릭스", raw)
    if match:
        return float(match.group(1))

    return None


def get_product_name(item):
    return clean_text(
        item.get("product_name")
        or item.get("raw_name")
        or item.get("title")
        or item.get("name")
        or ""
    )


def get_seller_name(item):
    return clean_text(
        item.get("seller_name")
        or item.get("mall_name")
        or item.get("platform_name")
        or item.get("platform")
        or ""
    )


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
    url = clean_text(url).lower()
    return (
        "search" in url
        and (
            "kurly.com" in url
            or "shopping.naver.com" in url
            or "naver.com" in url
        )
    )


def calculate_name_similarity(name_a, name_b):
    name_a = normalize_text(name_a)
    name_b = normalize_text(name_b)

    if not name_a or not name_b:
        return 0

    return int(SequenceMatcher(None, name_a, name_b).ratio() * 100)


def calculate_seller_score(item):
    seller = normalize_seller(get_seller_name(item))
    url = get_product_url(item)
    domain = extract_domain(url)

    score = 0
    reason = []

    if seller:
        score += 12
        reason.append("판매처 있음")

    if domain:
        score += 8
        reason.append("URL 도메인 있음")

    if seller and domain:
        if "kurly" in domain and ("컬리" in seller or "kurly" in seller):
            score += 5
            reason.append("컬리 판매처-URL 일치")
        elif "naver" in domain and ("네이버" in seller or "스마트" in seller or seller):
            score += 5
            reason.append("네이버 판매처-URL 확인")
        elif seller:
            score += 3
            reason.append("판매처 정보 확인")

    return min(score, 25), reason


def calculate_name_score(item):
    display_name = clean_text(item.get("display_name") or item.get("name") or "")
    product_name = get_product_name(item)

    if not display_name:
        display_name = product_name

    similarity = calculate_name_similarity(display_name, product_name)

    if similarity >= 90:
        return 30, ["상품명 매우 유사"]
    if similarity >= 75:
        return 24, ["상품명 유사"]
    if similarity >= 55:
        return 16, ["상품명 일부 유사"]
    if product_name:
        return 8, ["상품명 확인 가능"]

    return 0, ["상품명 부족"]


def calculate_weight_score(item):
    weight_g = get_weight_g(item)

    if not weight_g:
        return 0, ["중량 정보 없음"]

    if weight_g >= 1000:
        return 20, [f"중량 확인 {round(weight_g / 1000, 2)}kg"]

    return 16, [f"중량 확인 {weight_g}g"]


def calculate_brix_score(item):
    brix = get_brix_value(item)

    if not brix:
        if item.get("high_sugar_flag") or item.get("is_high_brix"):
            return 7, ["고당도 표시 확인"]
        return 0, ["Brix 정보 없음"]

    if brix >= 15:
        return 15, [f"{brix:g}brix 확인"]
    if brix >= 13:
        return 12, [f"{brix:g}brix 확인"]
    return 7, [f"{brix:g}brix 참고"]


def calculate_price_range_score(item):
    try:
        price = float(
            item.get("ai_estimated_price")
            or item.get("sale_price")
            or item.get("price")
            or 0
        )
    except Exception:
        price = 0

    if price <= 0:
        return 0, ["가격 정보 없음"]

    if 1000 <= price <= 500000:
        return 10, ["가격 범위 정상"]

    return 4, ["가격 범위 주의"]


def calculate_url_score(item):
    url = get_product_url(item)

    if not url:
        return -15, ["URL 없음"]

    if is_search_url(url):
        return -20, ["검색 URL"]

    domain = extract_domain(url)

    if domain:
        return 5, ["상세/이동 URL 확인"]

    return 0, ["URL 형식 확인 필요"]


def build_product_identity_key(item):
    seller = normalize_seller(get_seller_name(item))
    name = normalize_text(get_product_name(item))
    url = get_product_url(item)
    domain = extract_domain(url)
    weight_g = get_weight_g(item) or ""
    brix = get_brix_value(item) or ""

    raw = "|".join(
        [
            seller,
            domain,
            name,
            str(weight_g),
            str(brix),
        ]
    )

    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def calculate_product_identity(item):
    """상품 동일성 점수 계산

    기준:
    - 판매처/URL: 25점
    - 상품명 유사도: 30점
    - 중량: 20점
    - Brix/고당도: 15점
    - 가격 범위: 10점
    - URL 신뢰 보정: 검색 URL/URL 없음 감점
    """
    parts = []

    for calculator in [
        calculate_seller_score,
        calculate_name_score,
        calculate_weight_score,
        calculate_brix_score,
        calculate_price_range_score,
        calculate_url_score,
    ]:
        score, reasons = calculator(item)
        parts.append(
            {
                "score": score,
                "reasons": reasons,
            }
        )

    total_score = sum(part["score"] for part in parts)
    total_score = max(0, min(int(total_score), 100))

    if total_score >= 85:
        label = "🟢 동일 상품 가능성 높음"
        grade = "high"
        penalty = 0
    elif total_score >= 70:
        label = "🟡 유사 상품"
        grade = "medium"
        penalty = 5
    elif total_score >= 55:
        label = "🟠 상품 식별 주의"
        grade = "low"
        penalty = 15
    else:
        label = "🔴 검색 기반 추천"
        grade = "weak"
        penalty = 30

    reasons = []
    for part in parts:
        reasons.extend(part["reasons"])

    return {
        "identity_score": total_score,
        "identity_label": label,
        "identity_grade": grade,
        "identity_penalty": penalty,
        "identity_key": build_product_identity_key(item),
        "identity_reasons": reasons,
        "is_reliable": total_score >= 70,
        "is_exact_like": total_score >= 85,
    }


def apply_identity_score_to_item(item):
    result = calculate_product_identity(item)

    item["_identity_v2"] = result
    item["_identity_score_v2"] = result["identity_score"]
    item["_identity_label_v2"] = result["identity_label"]
    item["_identity_penalty_v2"] = result["identity_penalty"]
    item["_product_identity_key_v2"] = result["identity_key"]

    return item


def apply_identity_penalty(score, item):
    result = item.get("_identity_v2") or calculate_product_identity(item)

    try:
        score = float(score or 0)
    except Exception:
        score = 0

    return max(0, round(score - result.get("identity_penalty", 0), 1))
