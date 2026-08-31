from __future__ import annotations

from app.db.protocols import BorrowedExecutionConnection


from sqlalchemy import text

from app.services.preference.models import (
    PreferenceProfile,
)


def update_preference(
    conn: BorrowedExecutionConnection,
    *,
    session_id: str,
    query: str | None = None,
    priority: str | None = None,
    event_type: str = "search",
) -> None:
    """
    Persist cumulative preference state.

    This function preserves the legacy
    user_preference_profile mutation semantics.
    """
    if not session_id:
        return

    price_delta = 0
    quality_delta = 0
    trust_delta = 0
    exploration_delta = 0

    if priority == "price":
        price_delta = 1
    elif priority == "quality":
        quality_delta = 1
    elif priority == "trust":
        trust_delta = 1
    elif priority == "exploration":
        exploration_delta = 1

    search_inc = (
        1
        if event_type == "search"
        else 0
    )

    click_inc = (
        1
        if event_type == "click"
        else 0
    )

    conn.execute(
        text(
            """
            INSERT INTO user_preference_profile (
                session_id,
                price_affinity,
                quality_affinity,
                trust_affinity,
                exploration_affinity,
                search_count,
                click_count,
                last_query,
                last_priority,
                updated_at
            )
            VALUES (
                :session_id,
                :price_delta,
                :quality_delta,
                :trust_delta,
                :exploration_delta,
                :search_inc,
                :click_inc,
                :query,
                :priority,
                now()
            )
            ON CONFLICT (session_id)
            DO UPDATE SET
                price_affinity =
                    user_preference_profile.price_affinity
                    + EXCLUDED.price_affinity,
                quality_affinity =
                    user_preference_profile.quality_affinity
                    + EXCLUDED.quality_affinity,
                trust_affinity =
                    user_preference_profile.trust_affinity
                    + EXCLUDED.trust_affinity,
                exploration_affinity =
                    user_preference_profile.exploration_affinity
                    + EXCLUDED.exploration_affinity,
                search_count =
                    user_preference_profile.search_count
                    + EXCLUDED.search_count,
                click_count =
                    user_preference_profile.click_count
                    + EXCLUDED.click_count,
                last_query = EXCLUDED.last_query,
                last_priority = EXCLUDED.last_priority,
                updated_at = now()
            """
        ),
        {
            "session_id": session_id,
            "price_delta": price_delta,
            "quality_delta": quality_delta,
            "trust_delta": trust_delta,
            "exploration_delta": (
                exploration_delta
            ),
            "search_inc": search_inc,
            "click_inc": click_inc,
            "query": query,
            "priority": priority,
        },
    )


def get_preference(
    conn: BorrowedExecutionConnection,
    *,
    session_id: str,
) -> PreferenceProfile | None:
    """
    Load canonical preference state.

    Returns None when session_id is empty or
    no persisted profile exists.
    """
    if not session_id:
        return None

    result = conn.execute(
        text(
            """
            SELECT
                session_id,
                price_affinity,
                quality_affinity,
                trust_affinity,
                exploration_affinity,
                search_count,
                click_count,
                last_query,
                last_priority
            FROM user_preference_profile
            WHERE session_id = :session_id
            """
        ),
        {
            "session_id": session_id,
        },
    ).mappings().first()

    if not result:
        return None

    return PreferenceProfile.from_mapping(
        result
    )


__all__ = [
    "get_preference",
    "update_preference",
]
