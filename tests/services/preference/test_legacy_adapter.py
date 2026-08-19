from __future__ import annotations

from typing import Any

import app.services.preference_service as legacy


def test_legacy_update_delegates_to_canonical(
    monkeypatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_update(
        conn: Any,
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
        legacy,
        "_update_user_preference",
        fake_update,
    )

    conn = object()

    legacy.update_user_preference(
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


def test_legacy_get_delegates_to_canonical(
    monkeypatch,
) -> None:
    expected = {
        "session_id": "session-1",
        "price_affinity": 3.0,
    }

    def fake_get(
        conn: Any,
        session_id: str,
    ):
        assert session_id == "session-1"
        return expected

    monkeypatch.setattr(
        legacy,
        "_get_user_preference",
        fake_get,
    )

    result = legacy.get_user_preference(
        object(),
        "session-1",
    )

    assert result is expected


def test_legacy_policy_delegates_to_canonical(
    monkeypatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_decide(
        user_pref,
        default_priority: str = "trust",
    ) -> str:
        captured["user_pref"] = user_pref
        captured[
            "default_priority"
        ] = default_priority

        return "quality_adaptive"

    monkeypatch.setattr(
        legacy,
        "_decide_adaptive_priority",
        fake_decide,
    )

    pref = {
        "quality_affinity": 10,
    }

    result = legacy.decide_adaptive_priority(
        pref,
        default_priority="price",
    )

    assert result == "quality_adaptive"
    assert captured == {
        "user_pref": pref,
        "default_priority": "price",
    }


def test_legacy_public_contract_names() -> None:
    assert callable(
        legacy.update_user_preference
    )
    assert callable(
        legacy.get_user_preference
    )
    assert callable(
        legacy.decide_adaptive_priority
    )


def test_legacy_empty_session_semantics() -> None:
    assert (
        legacy.get_user_preference(
            object(),
            "",
        )
        is None
    )
