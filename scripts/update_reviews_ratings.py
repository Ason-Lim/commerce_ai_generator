import re
import time
import json
import requests
from bs4 import BeautifulSoup
from sqlalchemy import text

from app.db.database import engine


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
}


def clean_number(value):
    if value is None:
        return None

    text_value = str(value)
    text_value = text_value.replace(",", "")
    text_value = text_value.replace("개", "")
    text_value = text_value.replace("건", "")
    text_value = text_value.strip()

    match = re.search(r"\d+", text_value)
    if not match:
        return None

    return int(match.group())


def clean_rating(value):
    if value is None:
        return None

    text_value = str(value).strip()

    match = re.search(r"\d+(\.\d+)?", text_value)
    if not match:
        return None

    rating = float(match.group())

    if 0 <= rating <= 5:
        return rating

    if 0 <= rating <= 100:
        return round(rating / 20, 1)

    return None


def fetch_html(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=8)

        if response.status_code != 200:
            return None, f"http_status_{response.status_code}"

        html = response.text

        if "로봇" in html or "captcha" in html.lower() or "접속이 일시적으로 제한" in html:
            return None, "blocked_or_captcha"

        return html, "ok"

    except Exception as e:
        return None, f"request_error:{type(e).__name__}"


def extract_from_json_ld(html):
    soup = BeautifulSoup(html, "lxml")
    scripts = soup.find_all("script", type="application/ld+json")

    for script in scripts:
        try:
            data = json.loads(script.string or "")
        except Exception:
            continue

        candidates = data if isinstance(data, list) else [data]

        for item in candidates:
            if not isinstance(item, dict):
                continue

            aggregate = item.get("aggregateRating")
            if isinstance(aggregate, dict):
                rating = clean_rating(
                    aggregate.get("ratingValue")
                    or aggregate.get("rating")
                    or aggregate.get("value")
                )
                review_count = clean_number(
                    aggregate.get("reviewCount")
                    or aggregate.get("ratingCount")
                    or aggregate.get("count")
                )

                if rating or review_count:
                    return rating, review_count, "json_ld"

    return None, None, None


def extract_from_meta(html):
    soup = BeautifulSoup(html, "lxml")

    rating_candidates = [
        {"property": "product:rating:value"},
        {"property": "og:rating"},
        {"name": "rating"},
        {"itemprop": "ratingValue"},
    ]

    review_candidates = [
        {"property": "product:rating:count"},
        {"property": "product:review_count"},
        {"name": "reviewCount"},
        {"itemprop": "reviewCount"},
        {"itemprop": "ratingCount"},
    ]

    rating = None
    review_count = None

    for attrs in rating_candidates:
        tag = soup.find(attrs=attrs)
        if tag:
            rating = clean_rating(tag.get("content") or tag.get_text())
            if rating:
                break

    for attrs in review_candidates:
        tag = soup.find(attrs=attrs)
        if tag:
            review_count = clean_number(tag.get("content") or tag.get_text())
            if review_count:
                break

    if rating or review_count:
        return rating, review_count, "meta"

    return None, None, None


def extract_from_regex(html):
    patterns = [
        # common json keys
        (r'"ratingValue"\s*:\s*"?([0-9.]+)"?', r'"reviewCount"\s*:\s*"?([0-9,]+)"?'),
        (r'"averageRating"\s*:\s*"?([0-9.]+)"?', r'"reviewCount"\s*:\s*"?([0-9,]+)"?'),
        (r'"rating"\s*:\s*"?([0-9.]+)"?', r'"reviewCount"\s*:\s*"?([0-9,]+)"?'),
        (r'"score"\s*:\s*"?([0-9.]+)"?', r'"reviewCount"\s*:\s*"?([0-9,]+)"?'),
        # korean visible text fallback
        (r'평점\s*([0-9.]+)', r'리뷰\s*([0-9,]+)'),
        (r'별점\s*([0-9.]+)', r'후기\s*([0-9,]+)'),
    ]

    for rating_pattern, review_pattern in patterns:
        rating_match = re.search(rating_pattern, html)
        review_match = re.search(review_pattern, html)

        rating = clean_rating(rating_match.group(1)) if rating_match else None
        review_count = clean_number(review_match.group(1)) if review_match else None

        if rating or review_count:
            return rating, review_count, "regex"

    return None, None, None


def extract_rating_review(url):
    html, status = fetch_html(url)

    if not html:
        return {
            "rating": None,
            "review_count": None,
            "status": status,
            "source": None,
        }

    extractors = [
        extract_from_json_ld,
        extract_from_meta,
        extract_from_regex,
    ]

    for extractor in extractors:
        rating, review_count, source = extractor(html)

        if rating or review_count:
            return {
                "rating": rating,
                "review_count": review_count,
                "status": "parsed",
                "source": source,
            }

    return {
        "rating": None,
        "review_count": None,
        "status": "not_found",
        "source": None,
    }


def get_target_products(limit=50):
    sql = text("""
        SELECT id, product_name, mall_name, source_type, product_url
        FROM online_food_price_snapshot
        WHERE product_url IS NOT NULL
          AND product_url <> ''
          AND (
                rating IS NULL
             OR review_count IS NULL
             OR review_parse_status IS NULL
          )
        ORDER BY collected_at DESC NULLS LAST, id DESC
        LIMIT :limit
    """)

    with engine.connect() as conn:
        rows = conn.execute(sql, {"limit": limit}).mappings().all()

    return [dict(row) for row in rows]


def update_product_review(product_id, rating, review_count, status, source):
    sql = text("""
        UPDATE online_food_price_snapshot
        SET
            rating = COALESCE(:rating, rating),
            review_count = COALESCE(:review_count, review_count),
            review_parse_status = :status,
            review_source = :source
        WHERE id = :id
    """)

    with engine.begin() as conn:
        conn.execute(
            sql,
            {
                "id": product_id,
                "rating": rating,
                "review_count": review_count,
                "status": status,
                "source": source,
            },
        )


def main(limit=50, sleep_sec=1.5):
    products = get_target_products(limit=limit)

    print(f"대상 상품 수: {len(products)}")

    success = 0
    failed = 0

    for idx, product in enumerate(products, start=1):
        product_id = product["id"]
        url = product["product_url"]
        name = product["product_name"]

        print(f"\n[{idx}/{len(products)}] {name}")
        print(url)

        result = extract_rating_review(url)

        print(
            f"rating={result['rating']} | "
            f"review_count={result['review_count']} | "
            f"status={result['status']} | "
            f"source={result['source']}"
        )

        update_product_review(
            product_id=product_id,
            rating=result["rating"],
            review_count=result["review_count"],
            status=result["status"],
            source=result["source"],
        )

        if result["rating"] or result["review_count"]:
            success += 1
        else:
            failed += 1

        time.sleep(sleep_sec)

    print("\n완료")
    print(f"성공: {success}")
    print(f"실패/미검출: {failed}")


if __name__ == "__main__":
    main(limit=30, sleep_sec=1.5)
