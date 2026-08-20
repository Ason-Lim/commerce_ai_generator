from __future__ import annotations

from typing import Any

from app.services.session_context.models import (
    SessionContext,
)
from app.services.session_context.store import (
    get_session_context_record,
    update_session_context_record,
)


def update_session_context(
    conn: Any,
    session_id: str,
    query: str = "",
    priority: str = "",
    fruit_name: str = "",
    clicked_product: str = "",
    event_type: str = "search",
) -> None:
    """
    Canonical Session Context mutation service.

    Preserves the established Session Context
    write semantics.
    """
    update_session_context_record(
        conn=conn,
        session_id=session_id,
        query=query,
        priority=priority,
        fruit_name=fruit_name,
        clicked_product=clicked_product,
        event_type=event_type,
    )


def get_session_context(
    conn: Any,
    session_id: str,
) -> SessionContext | None:
    """
    Return the canonical Session Context for a
    session.
    """
    return get_session_context_record(
        conn=conn,
        session_id=session_id,
    )
