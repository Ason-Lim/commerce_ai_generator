from __future__ import annotations

from typing import Any

from app.services.preference.models import (
    PreferenceProfile,
)
from app.services.preference.store import (
    get_preference,
    update_preference,
)


class _FakeMappings:
    def __init__(
        self,
        row: dict[str, Any] | None,
    ) -> None:
        self._row = row

    def first(
        self,
    ) -> dict[str, Any] | None:
        return self._row


class _FakeResult:
    def __init__(
        self,
        row: dict[str, Any] | None = None,
    ) -> None:
        self._row = row

    def mappings(
        self,
    ) -> _FakeMappings:
        return _FakeMappings(
            self._row
        )


class _FakeConnection:
    def __init__(
        self,
        row: dict[str, Any] | None = None,
    ) -> None:
        self.row = row
        self.calls: list[
            tuple[Any, dict[str, Any]]
        ] = []

    def execute(
        self,
        statement: Any,
        params: dict[str, Any],
    ) -> _FakeResult:
        self.calls.append(
            (
                statement,
                params,
            )
        )

        return _FakeResult(
            self.row
        )


def test_update_preference_noop_without_session() -> None:
    conn = _FakeConnection()

    update_preference(
        conn,
        session_id="",
        query="apple",
        priority="price",
    )

    assert conn.calls == []


def test_update_preference_search_semantics() -> None:
    conn = _FakeConnection()

    update_preference(
        conn,
        session_id="session-1",
        query="apple",
        priority="price",
        event_type="search",
    )

    assert len(conn.calls) == 1

    _, params = conn.calls[0]

    assert params == {
        "session_id": "session-1",
        "price_delta": 1,
        "quality_delta": 0,
        "trust_delta": 0,
        "exploration_delta": 0,
        "search_inc": 1,
        "click_inc": 0,
        "query": "apple",
        "priority": "price",
    }


def test_update_preference_click_semantics() -> None:
    conn = _FakeConnection()

    update_preference(
        conn,
        session_id="session-1",
        query="wine",
        priority="exploration",
        event_type="click",
    )

    _, params = conn.calls[0]

    assert params[
        "exploration_delta"
    ] == 1
    assert params["search_inc"] == 0
    assert params["click_inc"] == 1


def test_unknown_priority_has_no_affinity_delta() -> None:
    conn = _FakeConnection()

    update_preference(
        conn,
        session_id="session-1",
        priority="balanced",
        event_type="search",
    )

    _, params = conn.calls[0]

    assert params["price_delta"] == 0
    assert params["quality_delta"] == 0
    assert params["trust_delta"] == 0
    assert params[
        "exploration_delta"
    ] == 0
    assert params["search_inc"] == 1


def test_unknown_event_has_no_counter_increment() -> None:
    conn = _FakeConnection()

    update_preference(
        conn,
        session_id="session-1",
        priority="trust",
        event_type="other",
    )

    _, params = conn.calls[0]

    assert params["trust_delta"] == 1
    assert params["search_inc"] == 0
    assert params["click_inc"] == 0


def test_get_preference_noop_without_session() -> None:
    conn = _FakeConnection()

    result = get_preference(
        conn,
        session_id="",
    )

    assert result is None
    assert conn.calls == []


def test_get_preference_returns_none_when_missing() -> None:
    conn = _FakeConnection(
        row=None
    )

    result = get_preference(
        conn,
        session_id="session-1",
    )

    assert result is None
    assert len(conn.calls) == 1


def test_get_preference_returns_profile() -> None:
    conn = _FakeConnection(
        row={
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
    )

    result = get_preference(
        conn,
        session_id="session-1",
    )

    assert isinstance(
        result,
        PreferenceProfile,
    )
    assert result.session_id == "session-1"
    assert result.price_affinity == 7.0
    assert result.quality_affinity == 3.0
    assert result.trust_affinity == 2.0
    assert (
        result.exploration_affinity
        == 1.0
    )
    assert result.search_count == 9
    assert result.click_count == 4
    assert result.last_query == "wine"
    assert (
        result.last_priority
        == "quality"
    )


def test_store_sql_preserves_upsert_contract() -> None:
    conn = _FakeConnection()

    update_preference(
        conn,
        session_id="session-1",
        priority="quality",
    )

    statement, _ = conn.calls[0]
    sql = str(statement)

    assert (
        "INSERT INTO user_preference_profile"
        in sql
    )
    assert (
        "ON CONFLICT (session_id)"
        in sql
    )
    assert (
        "price_affinity ="
        in sql
    )
    assert (
        "quality_affinity ="
        in sql
    )
    assert (
        "trust_affinity ="
        in sql
    )
    assert (
        "exploration_affinity ="
        in sql
    )
