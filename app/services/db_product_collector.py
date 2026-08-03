import re
from sqlalchemy import text
from app.db.database import engine


def parse_weight_g(text_value):
    if not text_value:
        return None
    text_value = str(text_value).lower().replace(",", "").replace("㎏", "kg")
    kg_match = re.search(r"(\d+\.?\d*)\s*kg", text_value)
    if kg_match:
        return int(float(kg_match.group(1)) * 1000)
    g_match = re.search(r"(\d+\.?\d*)\s*g", text_value)
    if g_match:
        return int(float(g_match.group(1)))
    return None


def normalize_platform(row):
    source = (row.get("source_type") or "").lower()
    mall = (row.get("mall_name") or "").lower()
    url = (row.get("product_url") or row.get("redirect_url") or row.get("raw_link") or "").lower()
    if "kurly" in source or "컬리" in mall or "kurly" in mall or "kurly" in url:
        return "마켓컬리"
    if "coupang" in source or "쿠팡" in mall or "coupang" in url:
        return "쿠팡"
    if "naver" in source or "네이버" in mall or "smartstore" in mall or "shopping.naver" in url:
        return "네이버"
    return row.get("mall_name") or row.get("source_type") or "기타"


def choose_best_url(row):
    for key in ["redirect_url", "product_url", "raw_link", "search_url"]:
        if row.get(key):
            return row.get(key)
    return None


def fetch_products_from_db(context: str, limit: int = 30):
    keyword = f"%{context}%"
    sql = text("""
        SELECT product_name, mall_name, source_type, price, original_price, discount_rate,
               member_price, benefit_price, max_benefit_price, review_count, rating,
               weight_text, weight_g, weight_kg, unit_price_per_kg, price_per_100g,
               product_url, raw_link, redirect_url, search_url, thumbnail_url, brand, maker,
               category1, category2, category3, category4, mall_product_id, product_identity_key,
               brix_value, high_sugar_flag, premium_flag, gift_flag, taste_guarantee_flag
        FROM online_food_price_snapshot
        WHERE product_name ILIKE :keyword
        ORDER BY collected_at DESC NULLS LAST, price ASC NULLS LAST
        LIMIT :limit
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql, {"keyword": keyword, "limit": limit}).mappings().all()
    products = []
    for row in rows:
        row = dict(row)
        platform = normalize_platform(row)
        if platform not in ["네이버", "쿠팡", "마켓컬리"]:
            continue
        weight_g = row.get("weight_g") or parse_weight_g(row.get("weight_text"))
        if not weight_g and row.get("weight_kg") is not None:
            weight_g = int(float(row["weight_kg"]) * 1000)
        price = int(row["price"]) if row.get("price") is not None else None
        product_url = choose_best_url(row)
        products.append({
            "name": row.get("product_name"), "product_name": row.get("product_name"),
            "platform": platform, "platform_name": platform, "mall_name": row.get("mall_name"),
            "seller_name": row.get("mall_name"), "price": price, "sale_price": price,
            "original_price": int(row["original_price"]) if row.get("original_price") is not None else None,
            "discount_rate": float(row["discount_rate"]) if row.get("discount_rate") is not None else None,
            "member_price": int(row["member_price"]) if row.get("member_price") is not None else None,
            "benefit_price": int(row["benefit_price"]) if row.get("benefit_price") is not None else None,
            "max_benefit_price": int(row["max_benefit_price"]) if row.get("max_benefit_price") is not None else None,
            "weight_text": row.get("weight_text"), "weight_g": int(weight_g) if weight_g else None,
            "weight_kg": float(row["weight_kg"]) if row.get("weight_kg") is not None else None,
            "unit_price_per_kg": float(row["unit_price_per_kg"]) if row.get("unit_price_per_kg") is not None else None,
            "price_per_100g": float(row["price_per_100g"]) if row.get("price_per_100g") is not None else None,
            "shipping_fee": 0, "description": row.get("product_name") or "",
            "rating": float(row["rating"]) if row.get("rating") is not None else None,
            "review_count": int(row["review_count"]) if row.get("review_count") is not None else None,
            "url": product_url, "product_url": product_url,
            "raw_link": row.get("raw_link"), "redirect_url": row.get("redirect_url"), "search_url": row.get("search_url"),
            "thumbnail_url": row.get("thumbnail_url"), "image": row.get("thumbnail_url"),
            "brand": row.get("brand"), "maker": row.get("maker"), "category1": row.get("category1"),
            "category2": row.get("category2"), "category3": row.get("category3"), "category4": row.get("category4"),
            "mall_product_id": row.get("mall_product_id"), "product_identity_key": row.get("product_identity_key"),
            "brix_value": float(row["brix_value"]) if row.get("brix_value") is not None else None,
            "brix": float(row["brix_value"]) if row.get("brix_value") is not None else None,
            "high_sugar_flag": bool(row["high_sugar_flag"]) if row.get("high_sugar_flag") is not None else False,
            "is_high_brix": bool(row["high_sugar_flag"]) if row.get("high_sugar_flag") is not None else False,
            "premium_flag": bool(row["premium_flag"]) if row.get("premium_flag") is not None else False,
            "gift_flag": bool(row["gift_flag"]) if row.get("gift_flag") is not None else False,
            "taste_guarantee_flag": bool(row["taste_guarantee_flag"]) if row.get("taste_guarantee_flag") is not None else False,
        })
    return products
