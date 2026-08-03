
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


def clean_text(value):
    value = str(value or "")
    value = re.sub(r"<script.*?</script>", " ", value, flags=re.S | re.I)
    value = re.sub(r"<style.*?</style>", " ", value, flags=re.S | re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    value = value.replace("&nbsp;", " ")
    value = value.replace("&amp;", "&")
    value = value.replace("\\u002F", "/")
    value = value.replace("\\u003C", "<")
    value = value.replace("\\u003E", ">")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


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


def extract_mall_product_id(url, html_text=""):
    candidates = [
        (r"/products/(\d+)", str(url or "")),
        (r"상품번호\s*(\d+)", str(html_text or "")),
        (r"productNo[^0-9]{0,20}(\d+)", str(html_text or "")),
        (r"channelProductNo[^0-9]{0,20}(\d+)", str(html_text or "")),
    ]

    for pattern, target in candidates:
        match = re.search(pattern, target)
        if match:
            return match.group(1)

    return None


def parse_review_rating(text_value):
    raw_text = str(text_value or "")
    text_value = clean_text(raw_text)

    rating = None
    review_count = None

    combined_patterns = [
        r"(\d(?:\.\d+)?)\s*\(\s*최근\s*6개월\s*\d(?:\.\d+)?\s*\)\s*(\d{1,3}(?:,\d{3})*|\d+)\s*건\s*리뷰",
        r"(\d(?:\.\d+)?)\s*\([^)]*\)\s*(\d{1,3}(?:,\d{3})*|\d+)\s*건\s*리뷰",
        r"(\d(?:\.\d+)?)\s+(\d{1,3}(?:,\d{3})*|\d+)\s*건\s*리뷰",
    ]

    for pattern in combined_patterns:
        match = re.search(pattern, text_value)
        if match:
            return safe_float(match.group(1)), safe_int(match.group(2))

    review_patterns = [
        r"리뷰\s*(\d{1,3}(?:,\d{3})*|\d+)",
        r"(\d{1,3}(?:,\d{3})*|\d+)\s*건\s*리뷰",
        r'"reviewCount"\s*:\s*"?([0-9,]+)"?',
        r'"totalReviewCount"\s*:\s*"?([0-9,]+)"?',
        r'"reviewCnt"\s*:\s*"?([0-9,]+)"?',
    ]

    for pattern in review_patterns:
        match = re.search(pattern, raw_text) or re.search(pattern, text_value)
        if match:
            review_count = safe_int(match.group(1))
            break

    rating_patterns = [
        r'"averageReviewScore"\s*:\s*"?([0-9.]+)"?',
        r'"reviewScore"\s*:\s*"?([0-9.]+)"?',
        r'"rating"\s*:\s*"?([0-9.]+)"?',
        r"평점\s*(\d(?:\.\d+)?)",
        r"별점\s*(\d(?:\.\d+)?)",
    ]

    for pattern in rating_patterns:
        match = re.search(pattern, raw_text) or re.search(pattern, text_value)
        if match:
            candidate = safe_float(match.group(1))
            if candidate and 0 < candidate <= 5:
                rating = candidate
                break

    if review_count and rating is None:
        review_pos = text_value.find("리뷰")
        if review_pos >= 0:
            window = text_value[max(0, review_pos - 140):review_pos + 140]
            for value in re.findall(r"\b([1-5]\.\d{1,2})\b", window):
                candidate = safe_float(value)
                if candidate and 0 < candidate <= 5:
                    rating = candidate
                    break

    return rating, review_count


def parse_kurly_price_block(text_value):
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
            benefit = member_price if member_price and member_price < sale_price else None
            return {
                "original_price": original_price,
                "price": sale_price,
                "discount_rate": discount_rate,
                "member_price": member_price,
                "benefit_price": benefit,
                "max_benefit_price": benefit,
            }

    member_match = re.search(
        r"(\d{1,3}(?:,\d{3})+)\s*원\s*(?:멤버십|회원|멤버스)\s*할인가",
        text_value,
    )
    member_price = safe_int(member_match.group(1)) if member_match else None

    return {
        "original_price": None,
        "price": None,
        "discount_rate": None,
        "member_price": member_price,
        "benefit_price": member_price,
        "max_benefit_price": member_price,
    }


def fetch_html(url, timeout=10):
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


def fetch_kurly_nmart_targets(limit=50):
    sql = text("""
        SELECT
            id,
            product_name,
            mall_name,
            product_url,
            raw_link,
            redirect_url,
            price,
            original_price,
            discount_rate,
            member_price,
            mall_product_id,
            rating,
            review_count
        FROM online_food_price_snapshot
        WHERE
            (
                mall_name ILIKE '%컬리N마트%'
                OR mall_name ILIKE '%컬리%'
                OR product_name ILIKE '%brix%'
                OR product_name ILIKE '%못생겨도 맛있는 사과%'
            )
            AND product_url IS NOT NULL
        ORDER BY collected_at DESC NULLS LAST
        LIMIT :limit
    """)

    with engine.connect() as conn:
        return [dict(row) for row in conn.execute(sql, {"limit": limit}).mappings().all()]


def update_kurly_nmart_row(row_id, fields):
    sql = text("""
        UPDATE online_food_price_snapshot
        SET
            original_price = COALESCE(:original_price, original_price),
            price = COALESCE(:price, price),
            discount_rate = COALESCE(:discount_rate, discount_rate),
            member_price = COALESCE(:member_price, member_price),
            benefit_price = COALESCE(:benefit_price, benefit_price),
            max_benefit_price = COALESCE(:max_benefit_price, max_benefit_price),
            review_count = COALESCE(:review_count, review_count),
            rating = COALESCE(:rating, rating),
            mall_product_id = COALESCE(:mall_product_id, mall_product_id)
        WHERE id = :id
    """)

    with engine.begin() as conn:
        conn.execute(
            sql,
            {
                "id": row_id,
                "original_price": fields.get("original_price"),
                "price": fields.get("price"),
                "discount_rate": fields.get("discount_rate"),
                "member_price": fields.get("member_price"),
                "benefit_price": fields.get("benefit_price"),
                "max_benefit_price": fields.get("max_benefit_price"),
                "review_count": fields.get("review_count"),
                "rating": fields.get("rating"),
                "mall_product_id": fields.get("mall_product_id"),
            },
        )


def enrich_kurly_nmart_products(limit=50, sleep_seconds=0.5):
    targets = fetch_kurly_nmart_targets(limit=limit)

    updated = 0
    skipped = 0

    print(f"🔎 컬리N마트 보강 대상: {len(targets)}건")

    for row in targets:
        url = row.get("redirect_url") or row.get("product_url") or row.get("raw_link")
        html = fetch_html(url)

        if not html:
            skipped += 1
            continue

        price_fields = parse_kurly_price_block(html)
        rating, review_count = parse_review_rating(html)
        mall_product_id = extract_mall_product_id(url, html)

        fields = {
            **price_fields,
            "rating": rating,
            "review_count": review_count,
            "mall_product_id": mall_product_id,
        }

        has_value = any(
            fields.get(k)
            for k in [
                "original_price",
                "price",
                "discount_rate",
                "member_price",
                "review_count",
                "rating",
                "mall_product_id",
            ]
        )

        if not has_value:
            skipped += 1
            continue

        update_kurly_nmart_row(row["id"], fields)
        updated += 1
        print("✅ 컬리N마트 보강:", str(row.get("product_name", ""))[:50], fields)
        time.sleep(sleep_seconds)

    print(f"✅ 컬리N마트 보강 완료: updated={updated}, skipped={skipped}")
    return {"updated": updated, "skipped": skipped}


if __name__ == "__main__":
    enrich_kurly_nmart_products(limit=50)
