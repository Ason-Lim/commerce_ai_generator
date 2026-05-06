import re
from sqlalchemy import text
from app.db.database import engine


def parse_weight_g(text_value):
    if not text_value:
        return None

    text_value = str(text_value).lower().replace(",", "")
    text_value = text_value.replace("㎏", "kg")

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

    if "naver" in source or "네이버" in mall or "smartstore" in mall:
        return "네이버"

    if "coupang" in source or "쿠팡" in mall:
        return "쿠팡"

    if "kurly" in source or "컬리" in mall or "kurly" in mall:
        return "마켓컬리"

    return row.get("mall_name") or row.get("source_type") or "기타"


def fetch_products_from_db(context: str, limit: int = 30):
    keyword = f"%{context}%"

    sql = text("""
        SELECT
            product_name,
            mall_name,
            source_type,
            price,
            original_price,
            discount_rate,
            review_count,
            rating,
            weight_text,
            weight_kg,
            unit_price_per_kg,
            product_url,
            brix_value,
            high_sugar_flag,
            premium_flag,
            gift_flag,
            taste_guarantee_flag
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

        weight_g = parse_weight_g(row.get("weight_text"))

        if not weight_g and row.get("weight_kg") is not None:
            weight_g = int(float(row["weight_kg"]) * 1000)

        products.append(
            {
                "name": row.get("product_name"),
                "platform": platform,
                "price": int(row["price"]) if row.get("price") is not None else None,
                "original_price": int(row["original_price"]) if row.get("original_price") is not None else None,
                "discount_rate": float(row["discount_rate"]) if row.get("discount_rate") is not None else None,
                "weight_g": weight_g,
                "weight_kg": float(row["weight_kg"]) if row.get("weight_kg") is not None else None,
                "unit_price_per_kg": float(row["unit_price_per_kg"]) if row.get("unit_price_per_kg") is not None else None,
                "shipping_fee": 0,
                "description": row.get("product_name") or "",
                "rating": float(row["rating"]) if row.get("rating") is not None else None,
                "review_count": int(row["review_count"]) if row.get("review_count") is not None else None,
                "url": row.get("product_url"),
                "brix_value": float(row["brix_value"]) if row.get("brix_value") is not None else None,
                "high_sugar_flag": bool(row["high_sugar_flag"]) if row.get("high_sugar_flag") is not None else False,
                "premium_flag": bool(row["premium_flag"]) if row.get("premium_flag") is not None else False,
                "gift_flag": bool(row["gift_flag"]) if row.get("gift_flag") is not None else False,
                "taste_guarantee_flag": bool(row["taste_guarantee_flag"]) if row.get("taste_guarantee_flag") is not None else False,
            }
        )

    return products
