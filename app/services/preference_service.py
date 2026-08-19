"""
Legacy Preference Service compatibility adapter.

The canonical Preference implementation lives under:

    app.services.preference

This module preserves the existing public import path and
calling contract for current consumers during migration.
"""

from __future__ import annotations

from app.services.preference.policy import (
    decide_adaptive_priority as _decide_adaptive_priority,
)
from app.services.preference.service import (
    get_user_preference as _get_user_preference,
)
from app.services.preference.service import (
    update_user_preference as _update_user_preference,
)


def update_user_preference(
    conn,
    session_id: str,
    query: str | None = None,
    priority: str | None = None,
    event_type: str = "search",
):
    """
    Legacy-compatible preference mutation adapter.
    """
    return _update_user_preference(
        conn,
        session_id,
        query=query,
        priority=priority,
        event_type=event_type,
    )


def get_user_preference(
    conn,
    session_id: str,
):
    """
    Legacy-compatible preference retrieval adapter.
    """
    return _get_user_preference(
        conn,
        session_id,
    )


def decide_adaptive_priority(
    user_pref: dict | None,
    default_priority: str = "trust",
):
    """
    Legacy-compatible adaptive priority policy adapter.
    """
    return _decide_adaptive_priority(
        user_pref,
        default_priority=default_priority,
    )


__all__ = [
    "decide_adaptive_priority",
    "get_user_preference",
    "update_user_preference",
]
