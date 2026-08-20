"""
Legacy Session Context compatibility adapter.

The canonical Session Context implementation lives under:

    app.services.session_context

This module preserves the existing public import path and
calling contract during consumer migration.
"""

from __future__ import annotations

from app.services.session_context import (
    update_session_context as _update_session_context,
)


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
    Legacy-compatible Session Context mutation adapter.
    """
    return _update_session_context(
        conn=conn,
        session_id=session_id,
        query=query,
        priority=priority,
        fruit_name=fruit_name,
        clicked_product=clicked_product,
        event_type=event_type,
    )


__all__ = [
    "update_session_context",
]
