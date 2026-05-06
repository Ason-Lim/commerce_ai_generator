from sqlalchemy import text
from app.db.database import engine


def log_search(session_id, query, priority, result_count, top_product=None):
    sql = text("""
        INSERT INTO ai_search_log (
            session_id,
            query,
            priority,
            result_count,
            top_product_name,
            top_platform
        )
        VALUES (
            :session_id,
            :query,
            :priority,
            :result_count,
            :top_product_name,
            :top_platform
        )
    """)

    with engine.begin() as conn:
        conn.execute(sql, {
            "session_id": session_id,
            "query": query,
            "priority": priority,
            "result_count": result_count,
            "top_product_name": top_product.get("name") if top_product else None,
            "top_platform": top_product.get("platform_label") if top_product else None,
        })


def log_product_click(session_id, query, product):
    sql = text("""
        INSERT INTO ai_product_click_log (
            session_id,
            query,
            product_name,
            platform_label,
            price,
            price_per_100g
        )
        VALUES (
            :session_id,
            :query,
            :product_name,
            :platform_label,
            :price,
            :price_per_100g
        )
    """)

    with engine.begin() as conn:
        conn.execute(sql, {
            "session_id": session_id,
            "query": query,
            "product_name": product.get("name"),
            "platform_label": product.get("platform_label"),
            "price": product.get("price"),
            "price_per_100g": product.get("price_per_100g"),
        })
