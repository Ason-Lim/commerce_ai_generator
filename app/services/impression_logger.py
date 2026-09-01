from sqlalchemy import text


from app.db.engine_provider import get_engine



def log_recommendation_impressions(
    session_id: str,
    query: str,
    items: list[dict],
    selected_section: str = "main",
):
    if not items:
        return

    with get_engine().begin() as conn:
        for item in items:
            conn.execute(
                text("""
                    INSERT INTO impression_log (
                        session_id,
                        query,
                        product_id,
                        product_name,
                        product_url,
                        rank,
                        recommendation_mode,
                        selected_priority,
                        selected_section,
                        platform,
                        mall_name,
                        price
                    )
                    VALUES (
                        :session_id,
                        :query,
                        :product_id,
                        :product_name,
                        :product_url,
                        :rank,
                        :recommendation_mode,
                        :selected_priority,
                        :selected_section,
                        :platform,
                        :mall_name,
                        :price
                    )
                """),
                {
                    "session_id": session_id,
                    "query": query,
                    "product_id": item.get("product_id") or item.get("id"),
                    "product_name": item.get("product_name") or item.get("name"),
                    "product_url": item.get("product_url") or item.get("url"),
                    "rank": item.get("rank"),
                    "recommendation_mode": item.get("recommendation_mode"),
                    "selected_priority": item.get("selected_priority"),
                    "selected_section": item.get("selected_section") or selected_section,
                    "platform": item.get("platform") or item.get("platform_name"),
                    "mall_name": item.get("mall_name") or item.get("seller_name"),
                    "price": item.get("price"),
                },
            )