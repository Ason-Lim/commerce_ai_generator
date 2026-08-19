from __future__ import annotations

from typing import Any

import app.services.preference.service as service
from app.services.preference.models import (
    PreferenceProfile,
)


def test_update_user_preference_delegates(
    monkeypatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_update(
        conn: Any,
        *,
        session_id: str,
        query: str | None = None,
        priority: str | None = None,
        event_type: str = "search",
    ) -> None:
        captured.update(
            {
                "conn": conn,
                "session_id": session_id,
                "query": query,
                "priority": priority,
                "event_type": event_type,
            }
        )

    monkeypatch.setattr(
        service,
        "update_preference",
        fake_update,
    )

    conn = object()

    service.update_user_preference(
        conn,
        "session-1",
        query="wine",
        priority="quality",
        event_type="click",
    )

    assert captured == {
        "conn": conn,
        "session_id": "session-1",
        "query": "wine",
        "priority": "quality",
        "event_type": "click",
    }


def test_get_user_preference_returns_none(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        service,
        "get_preference",
        lambda conn, *, session_id: None,
    )

    assert (
        service.get_user_preference(
            object(),
            "session-1",
        )
        is None
    )


def test_get_user_preference_returns_legacy_dict(
    monkeypatch,
) -> None:
    profile = PreferenceProfile(
        session_id="session-1",
        price_affinity=7,
        quality_affinity=3,
        trust_affinity=2,
        exploration_affinity=1,
        search_count=9,
        click_count=4,
        last_query="wine",
        last_priority="quality",
    )

    monkeypatch.setattr(
        service,
        "get_preference",
        lambda conn, *, session_id: profile,
    )

    result = service.get_user_preference(
        object(),
        "session-1",
    )

    assert result == {
        "session_id": "session-1",
        "price_affinity": 7,
        "quality_affinity": 3,
        "trust_affinity": 2,
        "exploration_affinity": 1,
        "search_count": 9,
        "click_count": 4,
        "last_query": "wine",
        "last_priority": "quality",
    }


def test_get_preference_profile_returns_model(
    monkeypatch,
) -> None:
    profile = PreferenceProfile(
        session_id="session-1"
    )

    monkeypatch.setattr(
        service,
        "get_preference",
        lambda conn, *, session_id: profile,
    )

    result = service.get_preference_profile(
        object(),
        "session-1",
    )

    assert result is profile


def test_profile_to_dict_rejects_invalid_type() -> None:
    try:
        service.preference_profile_to_dict(
            {}  # type: ignore[arg-type]
        )
    except TypeError as exc:
        assert (
            str(exc)
            == "profile must be PreferenceProfile"
        )
    else:
        raise AssertionError(
            "TypeError was not raised"
        )


def test_canonical_policy_is_exported() -> None:
    assert (
        service.decide_adaptive_priority(
            {
                "price_affinity": 10,
                "quality_affinity": 0,
                "trust_affinity": 0,
                "exploration_affinity": 0,
            }
        )
        == "price_adaptive"
    )
