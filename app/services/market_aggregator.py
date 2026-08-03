import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

from app.services.coupang_api import search_coupang_products

try:
    from app.services.naver_shopping_api_collector import collect_naver_products
except Exception:
    collect_naver_products = None


load_dotenv(".env")

DB_URL = (
    os.getenv("COMMERCE_DB_URL")
    or os.getenv("FRUIT_DB_URL")
    or "postgresql+psycopg2://mom@localhost:5432/dashboard_db"
)

engine = create_engine(DB_URL)


def _safe_int(value, default=0):
    try:
        return int(float(value))
    except Exception:
        return default


def fetch_naver_products_from_db(keyword: str, limit: int = 10):
    sql = text("""
        SELECT
            keyword,
            mall_name,
            product_name,
            price,
            original_price,
            discount_rate,
            product_url,
            raw_link,
            redirect_url,
            search_url,
            source_type,
            weight_text,
            weight_g,
            weight_kg,
            brix_value
        FROM online_food_price_snapshot
        WHERE keyword = :keyword
        ORDER BY price ASC
        LIMIT :limit
    """)

    try:
        with engine.connect() as conn:
            rows = conn.execute(sql, {"keyword": keyword, "limit": limit}).mappings().all()

        results = []
        for row in rows:
            item = dict(row)
            item["name"] = item.get("product_name")
            item["platform"] = "naver"
            item["source"] = "naver_shopping"
            item["seller_name"] = item.get("mall_name")
            item["price"] = _safe_int(item.get("price"))
            item["is_ad"] = False
            item["is_coupang"] = False
            results.append(item)

        return results

    except Exception as e:
        print(f"[Market Aggregator] Naver DB error: {e}")
        return []


def collect_market_products(keyword: str, limit: int = 10):
    results = []

    # 1) Naver 수집 실행
    if collect_naver_products:
        try:
            collect_naver_products(keyword)
        except Exception as e:
            print(f"[Market Aggregator] Naver collect error: {e}")

    # 2) Naver DB에서 최신 결과 조회
    naver_items = fetch_naver_products_from_db(keyword, limit=limit)
    results.extend(naver_items)

    # 3) Coupang API 조회
    try:
        coupang_items = search_coupang_products(keyword, limit=limit) or []
        results.extend(coupang_items)
    except Exception as e:
        print(f"[Market Aggregator] Coupang error: {e}")

    return results