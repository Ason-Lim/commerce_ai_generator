
import re
import time
from sqlalchemy import text
from playwright.sync_api import sync_playwright
from app.db.database import engine


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


def parse_review_rating(rendered_text):
    text_value = str(rendered_text or "")
    text_value = re.sub(r"\s+", " ", text_value).strip()

    patterns = [
        r"(\d(?:\.\d+)?)\s*\(\s*최근\s*6개월\s*\d(?:\.\d+)?\s*\)\s*(\d{1,3}(?:,\d{3})*|\d+)\s*건\s*리뷰",
        r"(\d(?:\.\d+)?)\s*\([^)]*최근[^)]*\)\s*(\d{1,3}(?:,\d{3})*|\d+)\s*건\s*리뷰",
        r"(\d(?:\.\d+)?)\s*(\d{1,3}(?:,\d{3})*|\d+)\s*건\s*리뷰",
    ]

    for pattern in patterns:
        match = re.search(pattern, text_value)
        if match:
            return safe_float(match.group(1)), safe_int(match.group(2))

    review_count = None

    for pattern in [
        r"리뷰\s*(\d{1,3}(?:,\d{3})*|\d+)",
        r"(\d{1,3}(?:,\d{3})*|\d+)\s*건\s*리뷰",
    ]:
        match = re.search(pattern, text_value)
        if match:
            review_count = safe_int(match.group(1))
            break

    rating = None

    if review_count:
        review_pos = text_value.find("리뷰")
        window = text_value[max(0, review_pos - 200):review_pos + 200] if review_pos >= 0 else text_value[:500]

        for value in re.findall(r"\b([1-5]\.\d{1,2})\b", window):
            candidate = safe_float(value)
            if candidate and 0 < candidate <= 5:
                rating = candidate
                break

    return rating, review_count


def fetch_targets(limit=30):
    sql = text("""
        SELECT
            id,
            product_name,
            mall_name,
            product_url,
            redirect_url,
            raw_link,
            rating,
            review_count
        FROM online_food_price_snapshot
        WHERE
            mall_name ILIKE '%컬리N마트%'
            AND product_url ILIKE '%smartstore.naver.com/main/products/%'
            AND (
                rating IS NULL
                OR review_count IS NULL
            )

            AND product_url IS NOT NULL
            AND (
                rating IS NULL
                OR review_count IS NULL
            )
        ORDER BY collected_at DESC NULLS LAST
        LIMIT :limit
    """)

    with engine.connect() as conn:
        return [dict(row) for row in conn.execute(sql, {"limit": limit}).mappings().all()]


def update_review_rating(row_id, rating, review_count):
    sql = text("""
        UPDATE online_food_price_snapshot
        SET
            rating = COALESCE(:rating, rating),
            review_count = COALESCE(:review_count, review_count)
        WHERE id = :id
    """)

    with engine.begin() as conn:
        conn.execute(
            sql,
            {
                "id": row_id,
                "rating": rating,
                "review_count": review_count,
            },
        )


def enrich_kurly_review_rating(limit=30, headless=True, sleep_seconds=0.5):
    targets = fetch_targets(limit=limit)

    updated = 0
    skipped = 0

    print(f"🔎 Playwright 리뷰/평점 보강 대상: {len(targets)}건")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page(
            viewport={"width": 1365, "height": 2200},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )

        for row in targets:
            url = row.get("redirect_url") or row.get("product_url") or row.get("raw_link")

            if not url:
                skipped += 1
                continue

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(3000)

                rendered_text = page.locator("body").inner_text(timeout=10000)
                rating, review_count = parse_review_rating(rendered_text)

                if not rating and not review_count:
                    skipped += 1
                    print("⚠️ 리뷰/평점 미검출:", row.get("product_name"))
                    continue

                update_review_rating(row["id"], rating, review_count)
                updated += 1

                print(
                    "✅ 리뷰/평점 보강:",
                    str(row.get("product_name", ""))[:50],
                    {"rating": rating, "review_count": review_count},
                )

                time.sleep(sleep_seconds)

            except Exception as e:
                skipped += 1
                print("❌ 보강 실패:", row.get("product_name"), str(e)[:120])

        browser.close()

    print(f"✅ Playwright 리뷰/평점 보강 완료: updated={updated}, skipped={skipped}")
    return {"updated": updated, "skipped": skipped}


if __name__ == "__main__":
    enrich_kurly_review_rating(limit=30, headless=True)
