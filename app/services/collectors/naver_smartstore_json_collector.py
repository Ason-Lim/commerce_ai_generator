import json
import re
import requests


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}


def safe_int(value):
    try:
        if value is None or value == "":
            return None
        return int(float(str(value).replace(",", "")))
    except Exception:
        return None


def safe_float(value):
    try:
        if value is None or value == "":
            return None
        return float(str(value).replace(",", ""))
    except Exception:
        return None


def clean_text(value):
    value = str(value or "")
    value = re.sub(r"<script.*?</script>", " ", value, flags=re.S | re.I)
    value = re.sub(r"<style.*?</style>", " ", value, flags=re.S | re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    value = value.replace("&nbsp;", " ")
    value = value.replace("&amp;", "&")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def extract_product_no(url, html_text=""):
    patterns = [
        (r"/products/(\d+)", str(url or "")),
        (r"상품번호\s*(\d+)", str(html_text or "")),
        (r'"productNo"\s*:\s*"?(\d+)"?', str(html_text or "")),
        (r'"channelProductNo"\s*:\s*"?(\d+)"?', str(html_text or "")),
        (r"productNo[^0-9]{0,30}(\d+)", str(html_text or "")),
        (r"channelProductNo[^0-9]{0,30}(\d+)", str(html_text or "")),
    ]

    for pattern, target in patterns:
        match = re.search(pattern, target)
        if match:
            return match.group(1)

    return None


def parse_price_block(text_value):
    text_value = clean_text(text_value)

    patterns = [
        r"(\d{1,2})\s*%\s*(\d{1,3}(?:,\d{3})+)\s*원\s*(\d{1,3}(?:,\d{3})+)\s*원\s*(\d{1,3}(?:,\d{3})+)\s*원\s*(?:멤버십|회원|멤버스)\s*할인가",
        r"(\d{1,2})\s*%\s*(\d{1,3}(?:,\d{3})+)\s*원\s*(\d{1,3}(?:,\d{3})+)\s*원",
    ]

    for pattern in patterns:
        match = re.search(pattern, text_value)
        if not match:
            continue

        groups = match.groups()
        discount_rate = safe_float(groups[0])
        original_price = safe_int(groups[1])
        sale_price = safe_int(groups[2])
        member_price = safe_int(groups[3]) if len(groups) >= 4 else None

        if original_price and sale_price and original_price > sale_price:
            benefit_price = member_price if member_price and member_price < sale_price else None
            return {
                "original_price": original_price,
                "price": sale_price,
                "sale_price": sale_price,
                "discount_rate": discount_rate,
                "member_price": member_price,
                "benefit_price": benefit_price,
                "max_benefit_price": benefit_price,
            }

    return {}


def parse_review_rating(text_value):
    text_value = clean_text(text_value)

    patterns = [
        r"(\d(?:\.\d+)?)\s*\(\s*최근\s*6개월\s*\d(?:\.\d+)?\s*\)\s*(\d{1,3}(?:,\d{3})*|\d+)\s*건\s*리뷰",
        r"(\d(?:\.\d+)?)\s*\([^)]*최근[^)]*\)\s*(\d{1,3}(?:,\d{3})*|\d+)\s*건\s*리뷰",
        r"(\d(?:\.\d+)?)\s+(\d{1,3}(?:,\d{3})*|\d+)\s*건\s*리뷰",
    ]

    for pattern in patterns:
        match = re.search(pattern, text_value)
        if match:
            return {
                "rating": safe_float(match.group(1)),
                "review_count": safe_int(match.group(2)),
            }

    return {}


def fetch_html(url):
    if not url:
        return ""

    try:
        response = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
        if response.status_code >= 400:
            return ""
        return response.text
    except Exception:
        return ""


def extract_json_candidates(html_text):
    candidates = []

    for pattern in [
        r'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        r'<script[^>]+type="application/json"[^>]*>(.*?)</script>',
    ]:
        for match in re.finditer(pattern, html_text, flags=re.S | re.I):
            raw = match.group(1).strip()
            if raw:
                candidates.append(raw)

    return candidates


def find_values_in_json(obj):
    result = {}

    key_map = {
        "salePrice": "price",
        "discountedSalePrice": "price",
        "price": "price",
        "originPrice": "original_price",
        "originalPrice": "original_price",
        "consumerPrice": "original_price",
        "discountRate": "discount_rate",
        "discountRatio": "discount_rate",
        "memberPrice": "member_price",
        "benefitPrice": "benefit_price",
        "maxBenefitPrice": "max_benefit_price",
        "reviewCount": "review_count",
        "totalReviewCount": "review_count",
        "averageReviewScore": "rating",
        "reviewScore": "rating",
        "productNo": "mall_product_id",
        "channelProductNo": "mall_product_id",
    }

    def walk(value):
        if isinstance(value, dict):
            for k, v in value.items():
                mapped = key_map.get(str(k))
                if mapped and result.get(mapped) is None:
                    if mapped in ["rating", "discount_rate"]:
                        result[mapped] = safe_float(v)
                    elif mapped == "mall_product_id":
                        result[mapped] = str(v) if v is not None else None
                    else:
                        result[mapped] = safe_int(v)
                walk(v)
        elif isinstance(value, list):
            for x in value:
                walk(x)

    walk(obj)

    if result.get("price"):
        result["sale_price"] = result["price"]

    return {k: v for k, v in result.items() if v is not None}


def enrich_from_json(html_text):
    for raw in extract_json_candidates(html_text):
        try:
            obj = json.loads(raw)
        except Exception:
            continue

        values = find_values_in_json(obj)
        if values:
            return values

    return {}


def enrich_naver_smartstore_product(item):
    url = (
        item.get("product_url")
        or item.get("url")
        or item.get("redirect_url")
        or item.get("raw_link")
        or ""
    )

    enriched = dict(item)
    enriched["_collector_type"] = "naver_smartstore"

    html = fetch_html(url)
    product_no = extract_product_no(url, html)

    if product_no:
        enriched["mall_product_id"] = product_no

    if not html:
        enriched["_collector_status"] = "partial"
        enriched["_collector_reason"] = "HTML 접근 실패. URL 상품번호만 반영했습니다."
        return enriched

    if "아이디 또는 전화번호" in html and "비밀번호" in html:
        enriched["_collector_status"] = "blocked"
        enriched["_collector_reason"] = "네이버 로그인 페이지로 리다이렉트되었습니다."
        return enriched

    json_values = enrich_from_json(html)
    text_values = {
        **parse_price_block(html),
        **parse_review_rating(html),
    }

    merged = {**text_values, **json_values}

    for key, value in merged.items():
        if value is not None:
            enriched[key] = value

    enriched["_collector_status"] = "ok" if merged else "no_data"
    enriched["_collector_reason"] = "JSON/HTML 후보에서 보강 완료" if merged else "보강 가능한 데이터 없음"

    return enriched
