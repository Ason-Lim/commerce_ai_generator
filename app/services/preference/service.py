from __future__ import annotations

from typing import Any

from app.services.preference.models import (
    PreferenceProfile,
)
from app.services.preference.policy import (
    decide_adaptive_priority,
)
from app.services.preference.store import (
    get_preference,
    update_preference,
)


def update_user_preference(
    conn: Any,
    session_id: str,
    query: str | None = None,
    priority: str | None = None,
    event_type: str = "search",
) -> None:
    """
    Canonical preference mutation service.

    Preserves the established Preference public
    calling semantics.
    """
    update_preference(
        conn,
        session_id=session_id,
        query=query,
        priority=priority,
        event_type=event_type,
    )


def get_user_preference(
    conn: Any,
    session_id: str,
) -> dict[str, Any] | None:
    """
    Canonical compatibility-facing read service.

    The persistence boundary uses PreferenceProfile,
    while this public service preserves the legacy
    dict | None return contract.
    """
    profile = get_preference(
        conn,
        session_id=session_id,
    )

    if profile is None:
        return None

    return preference_profile_to_dict(
        profile
    )


def get_preference_profile(
    conn: Any,
    session_id: str,
) -> PreferenceProfile | None:
    """
    Canonical typed read interface.
    """
    return get_preference(
        conn,
        session_id=session_id,
    )


def preference_profile_to_dict(
    profile: PreferenceProfile,
) -> dict[str, Any]:
    """
    Convert canonical PreferenceProfile to the exact
    legacy-compatible mapping shape.
    """
    if not isinstance(
        profile,
        PreferenceProfile,
    ):
        raise TypeError(
            "profile must be PreferenceProfile"
        )

    return {
        "session_id": profile.session_id,
        "price_affinity": (
            profile.price_affinity
        ),
        "quality_affinity": (
            profile.quality_affinity
        ),
        "trust_affinity": (
            profile.trust_affinity
        ),
        "exploration_affinity": (
            profile.exploration_affinity
        ),
        "search_count": profile.search_count,
        "click_count": profile.click_count,
        "last_query": profile.last_query,
        "last_priority": (
            profile.last_priority
        ),
    }


__all__ = [
    "decide_adaptive_priority",
    "get_preference_profile",
    "get_user_preference",
    "preference_profile_to_dict",
    "update_user_preference",
]
