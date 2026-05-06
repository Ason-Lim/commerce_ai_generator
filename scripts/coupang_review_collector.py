import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from sqlalchemy import text

from app.db.database import engine


def create_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(options=options)
    return driver


def clean_number(text):
    if not text:
        return None
    text = text.replace(",", "")
    m = re.search(r"\d+", text)
    return int(m.group()) if m else None


def clean_rating(text):
    if not text:
        return None
    m = re.search(r"\d+(\.\d+)?", text)
    return float(m.group()) if m else None


def search_coupang(driver, keyword):
    url = f"https://www.coupang.com/np/search?q={keyword}"
    driver.get(url)
    time.sleep(3)

    links = driver.find_elements(By.CSS_SELECTOR, "a.search-product-link")

    result = []
    for link in links[:5]:
        href = link.get_attribute("href")
        if href:
            result.append(href)

    return result


def extract_review_data(driver, url):
    driver.get(url)
    time.sleep(3)

    try:
        # 리뷰 탭 클릭
        buttons = driver.find_elements(By.XPATH, "//*[contains(text(),'상품평')]")
        if buttons:
            buttons[0].click()
            time.sleep(2)
    except:
        pass

    page = driver.page_source

    # 리뷰 수
    review_match = re.search(r"상품평\s*([0-9,]+)", page)
    review_count = clean_number(review_match.group(1)) if review_match else None

    # 별점
    rating_match = re.search(r"([0-9.]+)\s*점", page)
    rating = clean_rating(rating_match.group(1)) if rating_match else None

    return rating, review_count


def save_to_db(keyword, product_name, rating, review_count, url):
    sql = text("""
        INSERT INTO online_food_price_snapshot (
            keyword,
            product_name,
            mall_name,
            rating,
            review_count,
            product_url,
            source_type
        )
        VALUES (
            :keyword,
            :product_name,
            '쿠팡',
            :rating,
            :review_count,
            :url,
            'coupang_review'
        )
        ON CONFLICT DO NOTHING
    """)

    with engine.begin() as conn:
        conn.execute(sql, {
            "keyword": keyword,
            "product_name": product_name,
            "rating": rating,
            "review_count": review_count,
            "url": url
        })


def run(keyword):
    print(f"🚀 쿠팡 리뷰 수집 시작: {keyword}")

    driver = create_driver()

    try:
        links = search_coupang(driver, keyword)

        for link in links:
            print("🔎 상품:", link)

            rating, review_count = extract_review_data(driver, link)

            print("⭐", rating, "📝", review_count)

            if rating or review_count:
                save_to_db(keyword, keyword, rating, review_count, link)

            time.sleep(2)

    finally:
        driver.quit()

    print("✅ 완료")


if __name__ == "__main__":
    keywords = [
        "샤인머스캣",
        "고당도 사과",
        "딸기",
    ]

    for kw in keywords:
        run(kw)
