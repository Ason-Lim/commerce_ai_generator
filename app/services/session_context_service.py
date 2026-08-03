from sqlalchemy import text


def update_session_context(
    conn,
    session_id: str,
    query: str = "",
    priority: str = "",
    fruit_name: str = "",
    clicked_product: str = "",
    event_type: str = "search",
):
    """
    사용자의 최근 탐색 흐름을 저장합니다.
    - 검색 시: last_query, last_priority, last_fruit 저장
    - 클릭 시: last_clicked_product 저장
    """

    conn.execute(
        text("""
            INSERT INTO user_session_context (
                session_id,
                last_query,
                last_priority,
                last_fruit,
                last_clicked_product,
                last_event_type,
                updated_at
            )
            VALUES (
                :session_id,
                :last_query,
                :last_priority,
                :last_fruit,
                :last_clicked_product,
                :last_event_type,
                now()
            )
            ON CONFLICT (session_id)
            DO UPDATE SET
                last_query = COALESCE(NULLIF(EXCLUDED.last_query, ''), user_session_context.last_query),
                last_priority = COALESCE(NULLIF(EXCLUDED.last_priority, ''), user_session_context.last_priority),
                last_fruit = COALESCE(NULLIF(EXCLUDED.last_fruit, ''), user_session_context.last_fruit),
                last_clicked_product = COALESCE(NULLIF(EXCLUDED.last_clicked_product, ''), user_session_context.last_clicked_product),
                last_event_type = EXCLUDED.last_event_type,
                updated_at = now()
        """),
        {
            "session_id": session_id,
            "last_query": query or "",
            "last_priority": priority or "",
            "last_fruit": fruit_name or "",
            "last_clicked_product": clicked_product or "",
            "last_event_type": event_type or "",
        },
    )