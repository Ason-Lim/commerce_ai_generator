
import re
import time
import requests
from sqlalchemy import text
from app.db.database import engine


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}


FRUIT_KEYWORDS = [
    "사과", "부사", "홍로", "감홍", "시나노", "아오리", "엔비",
    "청송", "안동", "문경", "얼음골", "밀양", "고당도", "brix",
    "배", "샤인머스캣", "감귤", "귤", "딸기",
]

EXCLUDE_KEYWORDS = [
    "카네이션", "꽃", "화분", "꽃바구니", "한우", "갈치", "굴비",
    "견과", "쌀", "물티슈", "화장지", "돈까스", "생수",
]


def clean_text(value):
    value = str(value or "")
    value = re.sub(r"<script.*?</script>", " ", value, flags=re.S | re.I)
    value = re.sub(r"<style.*?</style>", " ", value, flags=re.S | re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    value = value.replace("&nbsp;", " ")
    value = value.replace("&amp;", "&")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def safe_int(value):
    try:
        if value is None or value == "":
            return None
        return int(float(str(value).replace(",", "")))
    except Exception:
        return None


def is_relevant_product(row, keyword=None):
    text_value = " ".join(
        str(row.get(k) or "")
        for k in ["product_name", "mall_name", "keyword", "fruit_type"]
    )

    if keyword and keyword not in text_value:
        return False

    if any(word in text_value for word in EXCLUDE_KEYWORDS):
        return False

    return any(word in text_value for word in FRUIT_KEYWORDS)


def parse_member_price(text_value):
    text_value = clean_text(text_value)

    patterns = [
        r"(\d{1,3}(?:,\d{3})+)\s*원\s*(?:멤버십|회원|멤버스)\s*할인가",
        r"(?:멤버십|회원|멤버스)\s*할인가\s*(\d{1,3}(?:,\d{3})+)\s*원",
        r"(\d{1,3}(?:,\d{3})+)\s*원\s*(?:최대\s*)?(?:혜택가|쿠폰가)",
        r"(?:최대\s*)?(?:혜택가|쿠폰가)\s*(\d{1,3}(?:,\d{3})+)\s*원",
    ]

    for pattern in patterns:
        match = re.search(pattern, text_value)
        if match:
            return safe_int(match.group(1))

    return None


def parse_kurly_nmart_price_block(text_value):
    text_value = clean_text(text_value)
    member_price = parse_member_price(text_value)

    patterns = [
        r"(\d{1,2})\s*%\s*(\d{1,3}(?:,\d{3})+)\s*원\s*(\d{1,3}(?:,\d{3})+)\s*원\s*(\d{1,3}(?:,\d{3})+)\s*원\s*(?:멤버십|회원|멤버스)\s*할인가",
        r"(\d{1,2})\s*%\s*(\d{1,3}(?:,\d{3})+)\s*원\s*(\d{1,3}(?:,\d{3})+)\s*원",
    ]

    for pattern in patterns:
        match = re.search(pattern, text_value)
        if not match:
            continue

        groups = match.groups()
        discount_rate = float(groups[0])
        original_price = safe_int(groups[1])
        sale_price = safe_int(groups[2])

        if len(groups) >= 4:
            member_price = safe_int(groups[3]) or member_price

        if original_price and sale_price and original_price > sale_price:
            benefit = member_price if member_price and member_price < sale_price else None
            return {
                "original_price": original_price,
                "sale_price": sale_price,
                "discount_rate": discount_rate,
                "member_price": member_price,
                "benefit_price": benefit,
                "max_benefit_price": benefit,
            }

    return None


def parse_price_candidates(text_value):
    candidates = []
    for match in re.finditer(r"(\d{1,3}(?:,\d{3})+)\s*원", str(text_value or "")):
        value = safe_int(match.group(1))
        if not value:
            continue
        if value < 1000 or value > 1000000:
            continue

        start = max(match.start() - 60, 0)
        end = min(match.end() + 60, len(text_value))
        candidates.append({"price": value, "context": text_value[start:end], "pos": match.start()})
    return candidates


def parse_discount_rate(text_value):
    values = []
    for match in re.finditer(r"(\d{1,2})\s*%", str(text_value or "")):
        try:
            value = int(match.group(1))
            if 1 <= value <= 90:
                values.append(value)
        except Exception:
            pass
    return max(values) if values else None


def filter_reasonable_prices(candidates, current_price):
    if not current_price:
        return candidates

    filtered = []
    for item in candidates:
        price = item["price"]
        if current_price * 0.35 <= price <= current_price * 3.0:
            filtered.append(item)

    return filtered or candidates


def infer_price_fields(raw_text, current_price=None):
    text_value = clean_text(raw_text)

    block_result = parse_kurly_nmart_price_block(text_value)
    if block_result:
        return block_result

    candidates = parse_price_candidates(text_value)
    candidates = filter_reasonable_prices(candidates, current_price)

    prices = sorted(set(item["price"] for item in candidates))
    discount_rate = parse_discount_rate(text_value)
    member_price = parse_member_price(text_value)

    sale_price = current_price
    original_price = None

    if len(prices) >= 2:
        if current_price:
            sale_price = min(prices, key=lambda p: abs(p - current_price))
        else:
            sale_price = min(prices)

        higher_prices = [p for p in prices if p > sale_price]
        if higher_prices:
            original_price = max(higher_prices)

    elif len(prices) == 1:
        only_price = prices[0]
        if not current_price or abs(only_price - current_price) / max(only_price, current_price) <= 0.25:
            sale_price = only_price

    if original_price and sale_price and original_price > sale_price:
        discount_rate = round((original_price - sale_price) / original_price * 100, 1)
    elif current_price and discount_rate and not original_price:
        try:
            original_price = round(current_price / (1 - discount_rate / 100))
            sale_price = current_price
        except Exception:
            pass

    if member_price and sale_price and member_price >= sale_price:
        member_price = None

    return {
        "original_price": original_price,
        "sale_price": sale_price,
        "discount_rate": discount_rate,
        "member_price": member_price,
        "benefit_price": member_price,
        "max_benefit_price": member_price,
    }


def fetch_page_text(url, timeout=8):
    if not url:
        return ""

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=timeout,
            allow_redirects=True,
        )
        if response.status_code >= 400:
            return ""
        return response.text
    except Exception:
        return ""


def choose_url(row):
    for key in ["redirect_url", "product_url", "raw_link"]:
        value = row.get(key)
        if value:
            return value
    return None


def fetch_targets(limit=50, keyword=None):
    where_keyword = ""
    params = {"limit": limit}

    if keyword:
        where_keyword = "AND (keyword ILIKE :keyword OR product_name ILIKE :keyword)"
        params["keyword"] = f"%{keyword}%"

    sql = text(f"""
        SELECT
            id,
            keyword,
            fruit_type,
            product_name,
            mall_name,
            price,
            original_price,
            discount_rate,
            member_price,
            benefit_price,
            max_benefit_price,
            product_url,
            raw_link,
            redirect_url,
            search_url
        FROM online_food_price_snapshot
        WHERE
            product_url IS NOT NULL
            {where_keyword}
            AND (
                original_price IS NULL
                OR discount_rate IS NULL
                OR member_price IS NULL
                OR benefit_price IS NULL
                OR max_benefit_price IS NULL
            )
        ORDER BY collected_at DESC NULLS LAST
        LIMIT :limit
    """)

    with engine.connect() as conn:
        rows = [dict(row) for row in conn.execute(sql, params).mappings().all()]

    return [row for row in rows if is_relevant_product(row, keyword=None)]


def update_price_fields(row_id, fields):
    sql = text("""
        UPDATE online_food_price_snapshot
        SET
            original_price = COALESCE(:original_price, original_price),
            price = COALESCE(:sale_price, price),
            discount_rate = COALESCE(:discount_rate, discount_rate),
            member_price = COALESCE(:member_price, member_price),
            benefit_price = COALESCE(:benefit_price, benefit_price),
            max_benefit_price = COALESCE(:max_benefit_price, max_benefit_price)
        WHERE id = :id
    """)

    with engine.begin() as conn:
        conn.execute(
            sql,
            {
                "id": row_id,
                "original_price": fields.get("original_price"),
                "sale_price": fields.get("sale_price"),
                "discount_rate": fields.get("discount_rate"),
                "member_price": fields.get("member_price"),
                "benefit_price": fields.get("benefit_price"),
                "max_benefit_price": fields.get("max_benefit_price"),
            },
        )


def enrich_price_details(limit=50, keyword="사과", sleep_seconds=0.5):
    targets = fetch_targets(limit=limit, keyword=keyword)

    updated = 0
    skipped = 0

    print(f"🔎 상세 가격 보강 대상: {len(targets)}건")

    for row in targets:
        url = choose_url(row)
        if not url:
            skipped += 1
            continue

        html = fetch_page_text(url)
        if not html:
            skipped += 1
            continue

        fields = infer_price_fields(raw_text=html, current_price=safe_int(row.get("price")))

        has_new_value = any(
            fields.get(key)
            for key in [
                "original_price",
                "discount_rate",
                "member_price",
                "benefit_price",
                "max_benefit_price",
            ]
        )

        if not has_new_value:
            skipped += 1
            continue

        update_price_fields(row["id"], fields)
        updated += 1

        print("✅ 보강:", str(row.get("product_name", ""))[:50], fields)
        time.sleep(sleep_seconds)

    print(f"✅ 상세 가격 보강 완료: updated={updated}, skipped={skipped}")
    return {"updated": updated, "skipped": skipped}


if __name__ == "__main__":
    enrich_price_details(limit=50, keyword="사과")
