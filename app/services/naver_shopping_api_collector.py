import requests
import os
import re
import json
import hashlib
from sqlalchemy import text
from app.db.database import engine
from dotenv import load_dotenv

load_dotenv()


def get_naver_credentials():
    return os.getenv("NAVER_CLIENT_ID"), os.getenv("NAVER_CLIENT_SECRET")


def call_naver_api(query, display=20, start=1):
    client_id, client_secret = get_naver_credentials()
    url = "https://openapi.naver.com/v1/search/shop.json"
    headers = {"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": client_secret}
    params = {"query": query, "display": display, "start": start, "sort": "sim"}
    response = requests.get(url, headers=headers, params=params, timeout=10)
    if response.status_code != 200:
        raise Exception(f"네이버 API 오류: {response.status_code}")
    return response.json()


def clean_html(text_value):
    return re.sub("<.*?>", "", str(text_value or "")).strip()


def safe_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(float(str(value).replace(",", "")))
    except Exception:
        return default


def parse_weight_text(text_value):
    value = clean_html(text_value).lower().replace(",", "").replace("㎏", "kg")
    m = re.search(r"(\d+(?:\.\d+)?)\s*(kg|g)", value, re.IGNORECASE)
    if not m:
        return None, None, None
    amount = float(m.group(1)); unit = m.group(2).lower()
    weight_g = int(amount * 1000) if unit == "kg" else int(amount)
    return f"{m.group(1)}{unit}", weight_g, round(weight_g / 1000, 3)


def parse_brix_value(text_value):
    value = clean_html(text_value).lower()
    m = re.search(r"(\d{2}(?:\.\d+)?)\s*(?:brix|브릭스)", value, re.IGNORECASE)
    return float(m.group(1)) if m else None


def calc_discount_rate(original_price, sale_price):
    try:
        if original_price and sale_price and original_price > sale_price:
            return round((original_price - sale_price) / original_price * 100, 1)
    except Exception:
        pass
    return None


def calc_unit_price_per_kg(price, weight_g):
    try:
        if price and weight_g:
            return round(float(price) / (float(weight_g) / 1000), 1)
    except Exception:
        pass
    return None


def calc_price_per_100g(price, weight_g):
    try:
        if price and weight_g:
            return round(float(price) / (float(weight_g) / 100), 1)
    except Exception:
        pass
    return None


def normalize_source_type(mall_name, link):
    mall = str(mall_name or "").lower(); link = str(link or "").lower()
    if "컬리" in mall or "kurly" in mall or "kurly" in link:
        return "naver_api_kurly"
    if "쿠팡" in mall or "coupang" in link:
        return "naver_api_coupang"
    return "naver_api"


def extract_url_fields(item):
    raw_link = item.get("link") or ""
    product_url = raw_link; redirect_url = ""; search_url = ""
    lower = raw_link.lower()
    if "redirect.kurly.com/entry" in lower:
        redirect_url = raw_link
    elif "kurly.com/search" in lower or "search.shopping.naver.com" in lower:
        search_url = raw_link
    return product_url, raw_link, redirect_url, search_url


def build_product_identity_key(mall_name, product_name, product_url, weight_text, brix_value):
    raw = "|".join([str(mall_name or "").lower(), str(product_name or "").lower(), str(product_url or "").lower(), str(weight_text or "").lower(), str(brix_value or "")])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def ensure_collector_v2_columns():
    ddl = [
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS raw_link TEXT",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS redirect_url TEXT",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS search_url TEXT",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS thumbnail_url TEXT",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS brand TEXT",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS maker TEXT",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS category1 TEXT",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS category2 TEXT",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS category3 TEXT",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS category4 TEXT",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS mall_product_id TEXT",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS product_identity_key TEXT",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS weight_g INTEGER",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS price_per_100g NUMERIC",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS member_price INTEGER",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS benefit_price INTEGER",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS max_benefit_price INTEGER",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS raw_payload JSONB",
    ]
    with engine.begin() as conn:
        for stmt in ddl:
            conn.execute(text(stmt))


def insert_products(items, keyword):
    ensure_collector_v2_columns()
    sql = text("""
        INSERT INTO online_food_price_snapshot (
            keyword, mall_name, product_name, price, original_price, discount_rate,
            product_url, raw_link, redirect_url, search_url, source_type,
            thumbnail_url, brand, maker, category1, category2, category3, category4,
            mall_product_id, product_identity_key, weight_text, weight_g, weight_kg,
            unit_price_per_kg, price_per_100g, brix_value, high_sugar_flag,
            member_price, benefit_price, max_benefit_price, raw_payload
        ) VALUES (
            :keyword, :mall_name, :product_name, :price, :original_price, :discount_rate,
            :product_url, :raw_link, :redirect_url, :search_url, :source_type,
            :thumbnail_url, :brand, :maker, :category1, :category2, :category3, :category4,
            :mall_product_id, :product_identity_key, :weight_text, :weight_g, :weight_kg,
            :unit_price_per_kg, :price_per_100g, :brix_value, :high_sugar_flag,
            :member_price, :benefit_price, :max_benefit_price, CAST(:raw_payload AS JSONB)
        ) ON CONFLICT DO NOTHING
    """)
    with engine.begin() as conn:
        for item in items:
            product_name = clean_html(item.get("title"))
            mall_name = item.get("mallName") or ""
            price = safe_int(item.get("lprice"))
            hprice = safe_int(item.get("hprice"))
            original_price = hprice if hprice and hprice > price else None
            product_url, raw_link, redirect_url, search_url = extract_url_fields(item)
            weight_text, weight_g, weight_kg = parse_weight_text(product_name)
            brix_value = parse_brix_value(product_name)
            identity = build_product_identity_key(mall_name, product_name, product_url, weight_text, brix_value)
            conn.execute(sql, {
                "keyword": keyword, "mall_name": mall_name, "product_name": product_name,
                "price": price or None, "original_price": original_price,
                "discount_rate": calc_discount_rate(original_price, price),
                "product_url": product_url, "raw_link": raw_link, "redirect_url": redirect_url,
                "search_url": search_url, "source_type": normalize_source_type(mall_name, product_url),
                "thumbnail_url": item.get("image"), "brand": item.get("brand"), "maker": item.get("maker"),
                "category1": item.get("category1"), "category2": item.get("category2"),
                "category3": item.get("category3"), "category4": item.get("category4"),
                "mall_product_id": item.get("productId"), "product_identity_key": identity,
                "weight_text": weight_text, "weight_g": weight_g, "weight_kg": weight_kg,
                "unit_price_per_kg": calc_unit_price_per_kg(price, weight_g),
                "price_per_100g": calc_price_per_100g(price, weight_g),
                "brix_value": brix_value, "high_sugar_flag": bool(brix_value and brix_value >= 13),
                "member_price": None, "benefit_price": None, "max_benefit_price": None,
                "raw_payload": json.dumps(item, ensure_ascii=False),
            })


def collect_naver_products(query):
    print(f"🔍 네이버 API 수집 시작: {query}")
    data = call_naver_api(query)
    items = data.get("items", [])
    insert_products(items, query)
    print(f"✅ {len(items)}건 저장 완료")
    return len(items)
