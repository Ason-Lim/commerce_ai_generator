import re
import time
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from sqlalchemy import text

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from app.db.database import engine


def clean_number(value):
    if value is None:
        return None
    text = str(value).replace(",", "").replace("개", "").replace("건", "")
    m = re.search(r"\d+", text)
    return int(m.group()) if m else None


def clean_rating(value):
    if value is None:
        return None
    m = re.search(r"\d+(\.\d+)?", str(value))
    if not m:
        return None
    rating = float(m.group())
    if 0 <= rating <= 5:
        return rating
    if 0 <= rating <= 100:
        return round(rating / 20, 1)
    return None


def detect_platform(url):
    host = urlparse(url).netloc.lower()

    if "coupang.com" in host:
        return "coupang"
    if "smartstore.naver.com" in host or "shopping.naver.com" in host:
        return "naver"
    if "kurly.com" in host:
        return "kurly"

    return "unknown"


def make_driver(headless=True):
    options = Options()

    if headless:
        options.add_argument("--headless=new")

    options.add_argument("--window-size=1400,1200")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--lang=ko-KR")
    options.add_argument("--disable-blink-features=AutomationControlled")

    options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    driver.set_page_load_timeout(25)
    return driver


def get_visible_text(driver):
    soup = BeautifulSoup(driver.page_source, "lxml")
    return soup.get_text(" ", strip=True), soup


def parse_common(text):
    rating = None
    review_count = None

    rating_patterns = [
        r"평점\s*([0-9.]+)",
        r"별점\s*([0-9.]+)",
        r"([0-9.]+)\s*점",
        r"ratingValue[\"']?\s*[:=]\s*[\"']?([0-9.]+)",
    ]

    review_patterns = [
        r"리뷰\s*([0-9,]+)",
        r"상품평\s*([0-9,]+)",
        r"후기\s*([0-9,]+)",
        r"구매후기\s*([0-9,]+)",
        r"reviewCount[\"']?\s*[:=]\s*[\"']?([0-9,]+)",
    ]

    for p in rating_patterns:
        m = re.search(p, text, re.I)
        if m:
            rating = clean_rating(m.group(1))
            if rating:
                break

    for p in review_patterns:
        m = re.search(p, text, re.I)
        if m:
            review_count = clean_number(m.group(1))
            if review_count:
                break

    return rating, review_count


def parse_coupang(text, soup):
    rating, review_count = parse_common(text)

    if review_count is None:
        m = re.search(r"상품평\s*([0-9,]+)개", text)
        if m:
            review_count = clean_number(m.group(1))

    if rating is None:
        # 쿠팡은 aria-label/title에 평점이 들어가는 경우가 있음
        for tag in soup.find_all(attrs={"aria-label": True}):
            val = tag.get("aria-label")
            if "별점" in val or "평점" in val:
                rating = clean_rating(val)
                if rating:
                    break

    return rating, review_count


def parse_naver(text, soup):
    rating, review_count = parse_common(text)

    if review_count is None:
        patterns = [
            r"리뷰\s*([0-9,]+)",
            r"방문자리뷰\s*([0-9,]+)",
            r"쇼핑몰리뷰\s*([0-9,]+)",
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                review_count = clean_number(m.group(1))
                break

    return rating, review_count


def parse_kurly(text, soup):
    rating, review_count = parse_common(text)

    if review_count is None:
        patterns = [
            r"후기\s*([0-9,]+)",
            r"상품후기\s*([0-9,]+)",
            r"리뷰\s*([0-9,]+)",
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                review_count = clean_number(m.group(1))
                break

    return rating, review_count

def extract_with_selenium(driver, url):
    platform = detect_platform(url)

    try:
        driver.get(url)
        time.sleep(3)

        # 🔥 1️⃣ 리뷰 탭 클릭 시도
        try:
            review_keywords = ["리뷰", "상품평", "후기"]
            for keyword in review_keywords:
                elements = driver.find_elements("xpath", f"//*[contains(text(), '{keyword}')]")
                if elements:
                    elements[0].click()
                    print(f"👉 {keyword} 클릭 성공")
                    time.sleep(2)
                    break
        except Exception as e:
            print("리뷰 클릭 실패:", e)

        # 🔥 2️⃣ 스크롤 다운 (리뷰 로딩 유도)
        try:
            for _ in range(5):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5)
        except Exception as e:
            print("스크롤 실패:", e)

        # 🔥 3️⃣ DOM 다시 파싱
        soup = BeautifulSoup(driver.page_source, "lxml")
        text = soup.get_text(" ", strip=True)

        # 🔥 차단 감지
        blocked_words = ["로봇", "captcha", "접속이 일시적으로 제한"]
        if any(word in text for word in blocked_words):
            return {
                "rating": None,
                "review_count": None,
                "status": "blocked",
                "source": platform,
            }

        # 🔥 플랫폼별 파싱 강화
        rating = None
        review_count = None

        # ⭐ 쿠팡 (강화)
        if platform == "coupang":
            m = re.search(r"별점\s*([0-9.]+)", text)
            if m:
                rating = clean_rating(m.group(1))

            m = re.search(r"상품평\s*([0-9,]+)", text)
            if m:
                review_count = clean_number(m.group(1))

        # ⭐ 네이버
        elif platform == "naver":
            m = re.search(r"평점\s*([0-9.]+)", text)
            if m:
                rating = clean_rating(m.group(1))

            m = re.search(r"리뷰\s*([0-9,]+)", text)
            if m:
                review_count = clean_number(m.group(1))

        # ⭐ 컬리
        elif platform == "kurly":
            m = re.search(r"([0-9.]+)\s*점", text)
            if m:
                rating = clean_rating(m.group(1))

            m = re.search(r"후기\s*([0-9,]+)", text)
            if m:
                review_count = clean_number(m.group(1))

        # 🔥 fallback
        if not rating:
            m = re.search(r"([0-9.]+)\s*점", text)
            if m:
                rating = clean_rating(m.group(1))

        if not review_count:
            m = re.search(r"(리뷰|상품평|후기)\s*([0-9,]+)", text)
            if m:
                review_count = clean_number(m.group(2))

        status = "parsed" if rating or review_count else "not_found"

        return {
            "rating": rating,
            "review_count": review_count,
            "status": status,
            "source": f"selenium_{platform}",
        }

    except Exception as e:
        return {
            "rating": None,
            "review_count": None,
            "status": f"error:{type(e).__name__}",
            "source": platform,
        }


def get_target_products(limit=30):
    sql = text("""
        SELECT id, product_name, mall_name, source_type, product_url
        FROM online_food_price_snapshot
        WHERE product_url IS NOT NULL
          AND product_url <> ''
          AND (
                rating IS NULL
             OR review_count IS NULL
             OR review_parse_status IS NULL
             OR review_parse_status IN ('not_found', 'blocked_or_captcha')
          )
        ORDER BY collected_at DESC NULLS LAST, id DESC
        LIMIT :limit
    """)

    with engine.connect() as conn:
        rows = conn.execute(sql, {"limit": limit}).mappings().all()

    return [dict(row) for row in rows]


def update_product(product_id, rating, review_count, status, source):
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


def main(limit=20, sleep_sec=3.0, headless=True):
    products = get_target_products(limit=limit)
    print(f"대상 상품 수: {len(products)}")

    driver = make_driver(headless=headless)

    success = 0
    failed = 0

    try:
        for idx, product in enumerate(products, start=1):
            product_id = product["id"]
            name = product["product_name"]
            url = product["product_url"]

            print(f"\n[{idx}/{len(products)}] {name}")
            print(url)

            result = extract_with_selenium(driver, url)

            print(
                f"rating={result['rating']} | "
                f"review_count={result['review_count']} | "
                f"status={result['status']} | "
                f"source={result['source']}"
            )

            update_product(
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

    finally:
        driver.quit()

    print("\n완료")
    print(f"성공: {success}")
    print(f"실패/미검출: {failed}")


if __name__ == "__main__":
    main(limit=20, sleep_sec=4.0, headless=False)
    