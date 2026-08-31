from __future__ import annotations

from app.db.protocols import BorrowedExecutionConnection


from sqlalchemy import text

from app.services.session_context.models import (
    SessionContext,
)


def update_session_context_record(
    conn: BorrowedExecutionConnection,
    session_id: str,
    query: str = "",
    priority: str = "",
    fruit_name: str = "",
    clicked_product: str = "",
    event_type: str = "search",
) -> None:
    conn.execute(
        text(
            """
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
                last_query = COALESCE(
                    NULLIF(EXCLUDED.last_query, ''),
                    user_session_context.last_query
                ),
                last_priority = COALESCE(
                    NULLIF(EXCLUDED.last_priority, ''),
                    user_session_context.last_priority
                ),
                last_fruit = COALESCE(
                    NULLIF(EXCLUDED.last_fruit, ''),
                    user_session_context.last_fruit
                ),
                last_clicked_product = COALESCE(
                    NULLIF(EXCLUDED.last_clicked_product, ''),
                    user_session_context.last_clicked_product
                ),
                last_event_type = EXCLUDED.last_event_type,
                updated_at = now()
            """
        ),
        {
            "session_id": session_id,
            "last_query": query or "",
            "last_priority": priority or "",
            "last_fruit": fruit_name or "",
            "last_clicked_product": clicked_product or "",
            "last_event_type": event_type or "",
        },
    )


def get_session_context_record(
    conn: BorrowedExecutionConnection,
    session_id: str,
) -> SessionContext | None:
    if not session_id:
        return None

    row = conn.execute(
        text(
            """
            SELECT
                last_query,
                last_priority,
                last_fruit,
                last_clicked_product,
                last_event_type
            FROM user_session_context
            WHERE session_id = :session_id
            """
        ),
        {
            "session_id": session_id,
        },
    ).mappings().first()

    return SessionContext.from_mapping(row)
