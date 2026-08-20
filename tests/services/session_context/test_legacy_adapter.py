from __future__ import annotations

from typing import Any

import app.services.session_context_service as legacy


def test_legacy_update_delegates_to_canonical(
    monkeypatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_update(
        *,
        conn: Any,
        session_id: str,
        query: str = "",
        priority: str = "",
        fruit_name: str = "",
        clicked_product: str = "",
        event_type: str = "search",
    ) -> None:
        captured.update(
            {
                "conn": conn,
                "session_id": session_id,
                "query": query,
                "priority": priority,
                "fruit_name": fruit_name,
                "clicked_product": clicked_product,
                "event_type": event_type,
            }
        )

    monkeypatch.setattr(
        legacy,
        "_update_session_context",
        fake_update,
    )

    conn = object()

    legacy.update_session_context(
        conn,
        "session-1",
        query="apple",
        priority="quality",
        fruit_name="apple",
        clicked_product="product-a",
        event_type="click",
    )

    assert captured == {
        "conn": conn,
        "session_id": "session-1",
        "query": "apple",
        "priority": "quality",
        "fruit_name": "apple",
        "clicked_product": "product-a",
        "event_type": "click",
    }


def test_legacy_default_contract(
    monkeypatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_update(
        *,
        conn: Any,
        session_id: str,
        query: str = "",
        priority: str = "",
        fruit_name: str = "",
        clicked_product: str = "",
        event_type: str = "search",
    ) -> None:
        captured.update(
            {
                "query": query,
                "priority": priority,
                "fruit_name": fruit_name,
                "clicked_product": clicked_product,
                "event_type": event_type,
            }
        )

    monkeypatch.setattr(
        legacy,
        "_update_session_context",
        fake_update,
    )

    legacy.update_session_context(
        object(),
        "session-1",
    )

    assert captured == {
        "query": "",
        "priority": "",
        "fruit_name": "",
        "clicked_product": "",
        "event_type": "search",
    }


def test_legacy_public_contract_name() -> None:
    assert callable(
        legacy.update_session_context
    )
