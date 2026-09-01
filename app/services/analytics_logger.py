from sqlalchemy import text
from app.services.preference import update_user_preference
from app.services.session_context import update_session_context

from app.db.engine_provider import get_engine



def log_search(session_id: str, query: str, priority: str, result_count: int, top_product=None):
    top_product = top_product or {}

    product_name = (
        top_product.get("product_name")
        or top_product.get("name")
    )

    score = (
        top_product.get("score")
        or top_product.get("recommendation_score")
        or top_product.get("trust_first_score")
    )

    with get_engine().begin() as conn:
        conn.execute(
            text("""
                INSERT INTO search_log (
                    session_id,
                    query,
                    priority,
                    result_count,
                    top_product_name,
                    top_product_score
                )
                VALUES (
                    :session_id,
                    :query,
                    :priority,
                    :result_count,
                    :top_product_name,
                    :top_product_score
                )
            """),
            {
                "session_id": session_id,
                "query": query,
                "priority": priority,
                "result_count": result_count,
                "top_product_name": product_name,
                "top_product_score": score,
            },
        )


def log_product_click(session_id: str, query: str, product: dict):
    print("CLICK PRODUCT =", product)

    selected_priority = product.get("selected_priority") or "trust"
    selected_section = product.get("selected_section") or "main"

    recommendation_mode = product.get("recommendation_mode")

    # unknown 저장 금지: 누락 시 ranking으로 보정하고 경고 출력
    if not recommendation_mode or recommendation_mode == "unknown":
        print(
            "WARNING: recommendation_mode missing. "
            f"product_name={product.get('product_name') or product.get('name')}"
        )
        recommendation_mode = "ranking"

    # hero는 추천 모드가 아니라 UI 위치
    if recommendation_mode == "hero":
        selected_section = selected_section or "hero"
        recommendation_mode = "ranking"

    score = (
        product.get("final_recommendation_score")
        or product.get("adaptive_ranking_score")
        or product.get("score")
        or product.get("recommendation_score")
        or product.get("trust_first_score")
    )

    params = {
        "session_id": session_id,
        "query": query,
        "product_id": product.get("product_id") or product.get("id"),
        "product_name": product.get("product_name") or product.get("name"),
        "seller_name": product.get("seller_name"),
        "product_url": product.get("product_url") or product.get("url"),
        "score": score,
        "recommendation_mode": recommendation_mode,
        "selected_priority": selected_priority,
        "selected_section": selected_section,
        "rank": product.get("rank") or product.get("recommendation_rank"),
        "platform": product.get("platform") or product.get("platform_name"),
        "mall_name": product.get("mall_name") or product.get("seller_name"),
        "price": product.get("price"),
    }

    with get_engine().begin() as conn:
        conn.execute(
            text("""
                INSERT INTO product_click_log (
                    session_id,
                    query,
                    product_id,
                    product_name,
                    seller_name,
                    product_url,
                    score,
                    recommendation_mode,
                    selected_priority,
                    selected_section,
                    rank,
                    platform,
                    mall_name,
                    price
                )
                VALUES (
                    :session_id,
                    :query,
                    :product_id,
                    :product_name,
                    :seller_name,
                    :product_url,
                    :score,
                    :recommendation_mode,
                    :selected_priority,
                    :selected_section,
                    :rank,
                    :platform,
                    :mall_name,
                    :price
                )
            """),
            params,
        )

        update_user_preference(
            conn=conn,
            session_id=session_id,
            query=query,
            priority=selected_priority,
            event_type="click",
        )
        
        update_session_context(
            conn=conn,
            session_id=session_id,
            query=query,
            priority=selected_priority,
            fruit_name=product.get("fruit_name") or "",
            clicked_product=params["product_name"] or "",
            event_type="click",
        )
        
        conn.execute(
            text("""
                INSERT INTO user_product_preference (
                    session_id,
                    product_name,
                    seller_name,
                    platform_name,
                    preference_score,
                    click_count,
                    last_clicked_at,
                    updated_at
                )
                VALUES (
                    :session_id,
                    :product_name,
                    :seller_name,
                    :platform_name,
                    1,
                    1,
                    now(),
                    now()
                )
                ON CONFLICT (session_id, product_name)
                DO UPDATE SET
                    preference_score = user_product_preference.preference_score + 1,
                    click_count = user_product_preference.click_count + 1,
                    seller_name = EXCLUDED.seller_name,
                    platform_name = EXCLUDED.platform_name,
                    last_clicked_at = now(),
                    updated_at = now()
            """),
            {
                "session_id": session_id,
                "product_name": params["product_name"],
                "seller_name": params["seller_name"],
                "platform_name": params["platform"],
            },
        )
        
        
        fruit_name = product.get("fruit_name")

        if fruit_name:
            conn.execute(
                text("""
                    INSERT INTO user_fruit_preference (
                        session_id,
                        fruit_name,
                        preference_score,
                        click_count,
                        last_clicked_at,
                        updated_at
                    )
                    VALUES (
                        :session_id,
                        :fruit_name,
                        1,
                        1,
                        now(),
                        now()
                    )
                    ON CONFLICT (session_id, fruit_name)
                    DO UPDATE SET
                        preference_score = user_fruit_preference.preference_score + 1,
                        click_count = user_fruit_preference.click_count + 1,
                        last_clicked_at = now(),
                        updated_at = now()
                """),
                {
                    "session_id": session_id,
                    "fruit_name": fruit_name,
                },
            )