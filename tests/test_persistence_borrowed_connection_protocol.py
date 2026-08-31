from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

import app.services.preference.service as preference_service
import app.services.preference.store as preference_store
import app.services.session_context.service as session_service
import app.services.session_context.store as session_store


@runtime_checkable
class ExecuteOnlyConnection(Protocol):
    def execute(self, statement: Any, params: dict[str, Any]) -> Any:
        ...


class _ExecuteOnlySentinel:
    def __init__(self) -> None:
        self.calls: list[tuple[Any, dict[str, Any]]] = []

    def execute(self, statement: Any, params: dict[str, Any]) -> Any:
        self.calls.append((statement, params))
        return _ResultSentinel()


class _ResultSentinel:
    def mappings(self) -> "_ResultSentinel":
        return self

    def first(self) -> None:
        return None


def test_execute_only_protocol_accepts_minimal_store_connection() -> None:
    conn = _ExecuteOnlySentinel()

    assert isinstance(conn, ExecuteOnlyConnection)
    assert not hasattr(conn, "begin")
    assert not hasattr(conn, "commit")
    assert not hasattr(conn, "rollback")
    assert not hasattr(conn, "close")
    assert not hasattr(conn, "dispose")


def test_preference_store_requires_only_execute_capability() -> None:
    conn = _ExecuteOnlySentinel()

    preference_store.update_preference(
        conn,
        session_id="session-1",
        query="apple",
        priority="price",
    )
    result = preference_store.get_preference(
        conn,
        session_id="session-1",
    )

    assert result is None
    assert len(conn.calls) == 2


def test_session_context_store_requires_only_execute_capability() -> None:
    conn = _ExecuteOnlySentinel()

    session_store.update_session_context_record(
        conn,
        session_id="session-1",
        query="apple",
    )
    result = session_store.get_session_context_record(
        conn,
        session_id="session-1",
    )

    assert result is None
    assert len(conn.calls) == 2


def test_preference_service_forwards_exact_connection_identity(monkeypatch) -> None:
    conn = object()
    captured: list[Any] = []

    def fake_update(forwarded: Any, **kwargs: Any) -> None:
        captured.append(forwarded)

    def fake_get(forwarded: Any, **kwargs: Any) -> None:
        captured.append(forwarded)
        return None

    monkeypatch.setattr(preference_service, "update_preference", fake_update)
    monkeypatch.setattr(preference_service, "get_preference", fake_get)

    preference_service.update_user_preference(
        conn,
        "session-1",
        query="apple",
    )
    preference_service.get_user_preference(
        conn,
        "session-1",
    )
    preference_service.get_preference_profile(
        conn,
        "session-1",
    )

    assert captured == [conn, conn, conn]


def test_session_context_service_forwards_exact_connection_identity(monkeypatch) -> None:
    conn = object()
    captured: list[Any] = []

    def fake_update(**kwargs: Any) -> None:
        captured.append(kwargs["conn"])

    def fake_get(*, conn: Any, session_id: str) -> None:
        captured.append(conn)
        return None

    monkeypatch.setattr(session_service, "update_session_context_record", fake_update)
    monkeypatch.setattr(session_service, "get_session_context_record", fake_get)

    session_service.update_session_context(
        conn,
        "session-1",
        query="apple",
    )
    session_service.get_session_context(
        conn,
        "session-1",
    )

    assert captured == [conn, conn]


def test_opaque_service_substitute_remains_valid_when_store_is_replaced(monkeypatch) -> None:
    opaque = object()

    monkeypatch.setattr(
        preference_service,
        "get_preference",
        lambda conn, *, session_id: None,
    )
    monkeypatch.setattr(
        session_service,
        "get_session_context_record",
        lambda *, conn, session_id: None,
    )

    assert preference_service.get_user_preference(opaque, "session-1") is None
    assert session_service.get_session_context(opaque, "session-1") is None


def test_nine_current_connection_annotations_remain_migration_targets() -> None:
    targets = [
        preference_store.update_preference,
        preference_store.get_preference,
        preference_service.update_user_preference,
        preference_service.get_user_preference,
        preference_service.get_preference_profile,
        session_store.update_session_context_record,
        session_store.get_session_context_record,
        session_service.update_session_context,
        session_service.get_session_context,
    ]

    assert len(targets) == 9
    for target in targets:
        assert "conn" in target.__annotations__
