
import re
import time
from sqlalchemy import text
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
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


def normalize_text(value):
    value = str(value or "")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def parse_review_rating(text_value):
    text_value = normalize_text(text_value)

    patterns = [
        r"(\d(?:\.\d+)?)\s*\(\s*최근\s*6개월\s*\d(?:\.\d+)?\s*\)\s*(\d{1,3}(?:,\d{3})*|\d+)\s*건\s*리뷰",
        r"(\d(?:\.\d+)?)\s*\([^)]*최근[^)]*\)\s*(\d{1,3}(?:,\d{3})*|\d+)\s*건\s*리뷰",
        r"(\d(?:\.\d+)?)\s+(?:최근\s*6개월\s*)?(\d{1,3}(?:,\d{3})*|\d+)\s*건\s*리뷰",
        r"평점\s*(\d(?:\.\d+)?)\s*.*?리뷰\s*(\d{1,3}(?:,\d{3})*|\d+)",
        r"리뷰\s*(\d{1,3}(?:,\d{3})*|\d+).*?평점\s*(\d(?:\.\d+)?)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text_value)
        if not match:
            continue

        g1 = match.group(1)
        g2 = match.group(2)

        if "." in g1:
            return safe_float(g1), safe_int(g2)

        return safe_float(g2), safe_int(g1)

    review_count = None
    rating = None

    for pattern in [
        r"리뷰\s*(\d{1,3}(?:,\d{3})*|\d+)",
        r"(\d{1,3}(?:,\d{3})*|\d+)\s*건\s*리뷰",
    ]:
        match = re.search(pattern, text_value)
        if match:
            review_count = safe_int(match.group(1))
            break

    if review_count:
        review_pos = text_value.find("리뷰")
        window = text_value[max(0, review_pos - 250): review_pos + 250] if review_pos >= 0 else text_value[:700]
        for value in re.findall(r"\b([1-5]\.\d{1,2})\b", window):
            candidate = safe_float(value)
            if candidate and 0 < candidate <= 5:
                rating = candidate
                break

    return rating, review_count


def parse_price_fields(text_value):
    text_value = normalize_text(text_value)

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

    return {
        "original_price": None,
        "price": None,
        "discount_rate": None,
        "member_price": None,
        "benefit_price": None,
        "max_benefit_price": None,
    }


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
            review_count,
            original_price,
            discount_rate,
            member_price
        FROM online_food_price_snapshot
        WHERE
            mall_name ILIKE '%컬리N마트%'
            AND product_url ILIKE '%smartstore.naver.com/main/products/%'
            AND (
                rating IS NULL
                OR review_count IS NULL
                OR original_price IS NULL
                OR discount_rate IS NULL
                OR member_price IS NULL
            )
        ORDER BY collected_at DESC NULLS LAST
        LIMIT :limit
    """)

    with engine.connect() as conn:
        return [dict(row) for row in conn.execute(sql, {"limit": limit}).mappings().all()]


def update_row(row_id, fields):
    sql = text("""
        UPDATE online_food_price_snapshot
        SET
            rating = COALESCE(:rating, rating),
            review_count = COALESCE(:review_count, review_count),
            original_price = COALESCE(:original_price, original_price),
            price = COALESCE(:price, price),
            discount_rate = COALESCE(:discount_rate, discount_rate),
            member_price = COALESCE(:member_price, member_price),
            benefit_price = COALESCE(:benefit_price, benefit_price),
            max_benefit_price = COALESCE(:max_benefit_price, max_benefit_price)
        WHERE id = :id
    """)

    with engine.begin() as conn:
        conn.execute(sql, {"id": row_id, **fields})


def read_text_by_selectors(page):
    selectors = [
        "text=리뷰",
        "text=건 리뷰",
        "text=멤버십 할인가",
        "text=할인가",
        "text=상품정보",
        "[class*=review]",
        "[class*=Review]",
        "[class*=score]",
        "[class*=Score]",
        "[class*=price]",
        "[class*=Price]",
        "[data-testid*=review]",
        "[data-testid*=price]",
        "body",
    ]

    chunks = []

    for selector in selectors:
        try:
            locator = page.locator(selector)
            count = min(locator.count(), 5)

            for idx in range(count):
                try:
                    text_value = normalize_text(locator.nth(idx).inner_text(timeout=1500))
                    if text_value:
                        chunks.append(text_value)
                except Exception:
                    continue
        except Exception:
            continue

    return "\n".join(dict.fromkeys(chunks))


def click_possible_expand_buttons(page):
    for selector in [
        "text=상세정보 펼쳐보기",
        "text=더보기",
        "text=상품정보 더보기",
        "text=리뷰 전체보기",
    ]:
        try:
            locator = page.locator(selector)
            if locator.count() > 0:
                locator.first.click(timeout=1500)
                page.wait_for_timeout(1000)
        except Exception:
            continue


def enrich_collector_v3(limit=30, headless=True, sleep_seconds=0.5):
    targets = fetch_targets(limit=limit)

    updated = 0
    skipped = 0

    print(f"🔎 Collector V3 선택자 기반 보강 대상: {len(targets)}건")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={"width": 1365, "height": 2400},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="ko-KR",
        )

        page = context.new_page()

        for row in targets:
            url = row.get("redirect_url") or row.get("product_url") or row.get("raw_link")

            if not url:
                skipped += 1
                continue

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(3000)

                click_possible_expand_buttons(page)

                extracted_text = read_text_by_selectors(page)
                
                print("===== DEBUG URL =====")
                print(url)

                print("===== DEBUG TEXT START =====")
                print(extracted_text[:2000])
                print("===== DEBUG TEXT END =====")

                page.screenshot(path=f"/tmp/kurly_debug_{row['id']}.png", full_page=True)
                
                if not extracted_text:
                    extracted_text = page.locator("body").inner_text(timeout=5000)

                rating, review_count = parse_review_rating(extracted_text)
                price_fields = parse_price_fields(extracted_text)

                fields = {
                    **price_fields,
                    "rating": rating,
                    "review_count": review_count,
                }

                has_value = any(
                    fields.get(k)
                    for k in [
                        "rating",
                        "review_count",
                        "original_price",
                        "discount_rate",
                        "member_price",
                    ]
                )

                if not has_value:
                    skipped += 1
                    print("⚠️ 미검출:", row.get("product_name"))
                    continue

                update_row(row["id"], fields)
                updated += 1

                print("✅ V3 보강:", str(row.get("product_name", ""))[:50], fields)
                time.sleep(sleep_seconds)

            except PlaywrightTimeoutError:
                skipped += 1
                print("❌ Timeout:", url)
            except Exception as e:
                skipped += 1
                print("❌ 실패:", row.get("product_name"), str(e)[:120])

        context.close()
        browser.close()

    print(f"✅ Collector V3 완료: updated={updated}, skipped={skipped}")
    return {"updated": updated, "skipped": skipped}


if __name__ == "__main__":
    enrich_collector_v3(limit=30, headless=True)
