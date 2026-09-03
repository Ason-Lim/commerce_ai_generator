from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import pytest

from app.services import naver_datalab_service as datalab


TARGET = Path("app/services/naver_datalab_service.py")


def _tree() -> ast.Module:
    return ast.parse(TARGET.read_text(encoding="utf-8"))


def _function(name: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    for node in _tree().body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    raise AssertionError(f"function not found: {name}")


def _provider_attribute_calls(node: ast.AST, attr: str) -> list[ast.Call]:
    calls: list[ast.Call] = []
    for candidate in ast.walk(node):
        if not isinstance(candidate, ast.Call):
            continue
        func = candidate.func
        if not isinstance(func, ast.Attribute):
            continue
        provider = func.value
        if not isinstance(provider, ast.Call):
            continue
        if not isinstance(provider.func, ast.Name):
            continue
        if provider.func.id == "get_engine" and func.attr == attr:
            calls.append(candidate)
    return calls


def _legacy_engine_calls(node: ast.AST) -> list[ast.Call]:
    calls: list[ast.Call] = []
    for candidate in ast.walk(node):
        if not isinstance(candidate, ast.Call):
            continue
        func = candidate.func
        if (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id == "engine"
        ):
            calls.append(candidate)
    return calls


class _FakeMappings:
    def __init__(self, row: dict[str, Any] | None) -> None:
        self.row = row

    def first(self) -> dict[str, Any] | None:
        return self.row


class _FakeResult:
    def __init__(self, row: dict[str, Any] | None) -> None:
        self.row = row

    def mappings(self) -> _FakeMappings:
        return _FakeMappings(self.row)


class _FakeConnection:
    def __init__(self, row: dict[str, Any] | None = None) -> None:
        self.row = row
        self.executions: list[tuple[str, dict[str, Any]]] = []

    def execute(self, statement: Any, params: dict[str, Any]) -> _FakeResult:
        self.executions.append((str(statement), params))
        return _FakeResult(self.row)


class _Context:
    def __init__(self, connection: _FakeConnection) -> None:
        self.connection = connection

    def __enter__(self) -> _FakeConnection:
        return self.connection

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> bool:
        return False


class _FakeEngine:
    def __init__(self, row: dict[str, Any] | None = None) -> None:
        self.connection = _FakeConnection(row)
        self.connect_calls = 0
        self.begin_calls = 0

    def connect(self) -> _Context:
        self.connect_calls += 1
        return _Context(self.connection)

    def begin(self) -> _Context:
        self.begin_calls += 1
        return _Context(self.connection)


def _deny_network(*args: Any, **kwargs: Any) -> None:
    raise AssertionError("external network access is forbidden in I5-B3 tests")


def test_module_imports_provider_not_legacy_database_engine() -> None:
    database_imports: set[str] = set()
    provider_imports: set[str] = set()

    for node in _tree().body:
        if isinstance(node, ast.ImportFrom) and node.module == "app.db.database":
            database_imports.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module == "app.db.engine_provider":
            provider_imports.update(alias.name for alias in node.names)

    assert "engine" not in database_imports
    assert "get_engine" in provider_imports


def test_cached_read_static_boundary_is_connect_only() -> None:
    fn = _function("get_cached_keyword_trend")

    assert len(_provider_attribute_calls(fn, "connect")) == 1
    assert _provider_attribute_calls(fn, "begin") == []
    assert _legacy_engine_calls(fn) == []


def test_cached_write_static_boundary_is_begin_only() -> None:
    fn = _function("save_keyword_trend_cache")

    assert len(_provider_attribute_calls(fn, "begin")) == 1
    assert _provider_attribute_calls(fn, "connect") == []
    assert _legacy_engine_calls(fn) == []


def test_cached_read_preserves_select_parameters_and_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row = {
        "keyword": "사과",
        "trend_score": 73.5,
        "trend_direction": "up",
        "searched_at": "2026-09-02",
        "raw_payload": {"source": "fake"},
    }
    engine = _FakeEngine(row)
    monkeypatch.setattr(datalab, "get_engine", lambda: engine)
    monkeypatch.setattr(datalab.requests, "post", _deny_network)

    result = datalab.get_cached_keyword_trend("사과")

    assert result == row
    assert engine.connect_calls == 1
    assert engine.begin_calls == 0
    assert len(engine.connection.executions) == 1
    sql, params = engine.connection.executions[0]
    assert "SELECT keyword, trend_score, trend_direction, searched_at, raw_payload" in sql
    assert "FROM keyword_trend_cache" in sql
    assert params == {"keyword": "사과"}


def test_cached_read_preserves_none_for_cache_miss(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = _FakeEngine(None)
    monkeypatch.setattr(datalab, "get_engine", lambda: engine)
    monkeypatch.setattr(datalab.requests, "post", _deny_network)

    assert datalab.get_cached_keyword_trend("없는검색어") is None
    assert engine.connect_calls == 1
    assert engine.begin_calls == 0


def test_cached_write_preserves_upsert_parameters_and_transaction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = _FakeEngine()
    monkeypatch.setattr(datalab, "get_engine", lambda: engine)
    monkeypatch.setattr(datalab.requests, "post", _deny_network)
    payload = {"title": "사과", "한글": True}

    result = datalab.save_keyword_trend_cache(
        "사과",
        {"latest_ratio": 81.25, "trend_direction": "up"},
        payload,
    )

    assert result is None
    assert engine.connect_calls == 0
    assert engine.begin_calls == 1
    assert len(engine.connection.executions) == 1
    sql, params = engine.connection.executions[0]
    assert "INSERT INTO keyword_trend_cache" in sql
    assert "ON CONFLICT (keyword) DO UPDATE SET" in sql
    assert params == {
        "keyword": "사과",
        "trend_score": 81.25,
        "trend_direction": "up",
        "raw_payload": json.dumps(payload, ensure_ascii=False),
    }
