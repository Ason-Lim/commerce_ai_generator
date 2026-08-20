from __future__ import annotations

from typing import Any

import app.services.session_context.service as service
from app.services.session_context import (
    SessionContext,
)


def test_update_delegates_to_store(
    monkeypatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_update(**kwargs) -> None:
        captured.update(kwargs)

    monkeypatch.setattr(
        service,
        "update_session_context_record",
        fake_update,
    )

    conn = object()

    service.update_session_context(
        conn=conn,
        session_id="session-1",
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


def test_get_delegates_to_store(
    monkeypatch,
) -> None:
    expected = SessionContext(
        last_query="apple",
    )

    def fake_get(
        conn,
        session_id,
    ):
        assert session_id == "session-1"
        return expected

    monkeypatch.setattr(
        service,
        "get_session_context_record",
        fake_get,
    )

    result = service.get_session_context(
        object(),
        "session-1",
    )

    assert result is expected
