from __future__ import annotations

import ast
import inspect
from pathlib import Path
from typing import Any

import pytest

from app.services import coupang_review_matcher as coupang
from app.services import db_product_collector as product_collector


TARGETS = {
    "coupang": Path("app/services/coupang_review_matcher.py"),
    "product": Path("app/services/db_product_collector.py"),
}


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _function(path: Path, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    for node in _tree(path).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    raise AssertionError(f"function not found: {name}")


def _provider_calls(node: ast.AST, attr: str) -> list[ast.Call]:
    calls: list[ast.Call] = []
    for candidate in ast.walk(node):
        if not isinstance(candidate, ast.Call):
            continue
        func = candidate.func
        if not isinstance(func, ast.Attribute) or func.attr != attr:
            continue
        owner = func.value
        if not isinstance(owner, ast.Call):
            continue
        if isinstance(owner.func, ast.Name) and owner.func.id == "get_engine":
            calls.append(candidate)
    return calls


def _legacy_engine_calls(node: ast.AST) -> list[ast.Call]:
    calls: list[ast.Call] = []
    for candidate in ast.walk(node):
        if not isinstance(candidate, ast.Call):
            continue
        func = candidate.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            if func.value.id == "engine":
                calls.append(candidate)
    return calls


class _FakeMappings:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows

    def first(self) -> dict[str, Any] | None:
        return self.rows[0] if self.rows else None

    def all(self) -> list[dict[str, Any]]:
        return self.rows


class _FakeResult:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows

    def mappings(self) -> _FakeMappings:
        return _FakeMappings(self.rows)


class _FakeConnection:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self.executions: list[tuple[str, dict[str, Any]]] = []

    def execute(self, statement: Any, params: dict[str, Any]) -> _FakeResult:
        self.executions.append((str(statement), params))
        return _FakeResult(self.rows)


class _Context:
    def __init__(self, connection: _FakeConnection) -> None:
        self.connection = connection

    def __enter__(self) -> _FakeConnection:
        return self.connection

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> bool:
        return False


class _FakeEngine:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.connection = _FakeConnection(rows)
        self.connect_calls = 0
        self.begin_calls = 0

    def connect(self) -> _Context:
        self.connect_calls += 1
        return _Context(self.connection)

    def begin(self) -> _Context:
        self.begin_calls += 1
        raise AssertionError("transaction ownership is forbidden for TB-05 reads")


def test_each_reader_uses_one_provider_connect_and_no_transaction() -> None:
    targets = (
        (TARGETS["coupang"], "fetch_coupang_review_signal"),
        (TARGETS["product"], "fetch_products_from_db"),
    )

    for path, function_name in targets:
        tree = _tree(path)
        function = _function(path, function_name)
        database_imports: set[str] = set()
        provider_imports: set[str] = set()

        for node in tree.body:
            if isinstance(node, ast.ImportFrom) and node.module == "app.db.database":
                database_imports.update(alias.name for alias in node.names)
            if isinstance(node, ast.ImportFrom) and node.module == "app.db.engine_provider":
                provider_imports.update(alias.name for alias in node.names)

        assert "engine" not in database_imports
        assert "get_engine" in provider_imports
        assert len(_provider_calls(function, "connect")) == 1
        assert _provider_calls(function, "begin") == []
        assert _legacy_engine_calls(function) == []


def test_public_function_signatures_are_preserved() -> None:
    assert str(inspect.signature(coupang.fetch_coupang_review_signal)) == "(keyword: str)"
    assert str(inspect.signature(product_collector.fetch_products_from_db)) == "(context: str, limit: int = 30)"


def test_coupang_reader_preserves_query_parameters_and_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row = {
        "product_name": "사과 1kg",
        "mall_name": "쿠팡",
        "rating": "4.8",
        "review_count": "321",
        "product_url": "https://example.invalid/product",
    }
    engine = _FakeEngine([row])
    monkeypatch.setattr(coupang, "get_engine", lambda: engine)

    result = coupang.fetch_coupang_review_signal("사과")

    assert result == {
        "source": "쿠팡 리뷰 신뢰도",
        "product_name": "사과 1kg",
        "mall_name": "쿠팡",
        "rating": 4.8,
        "review_count": 321,
        "url": "https://example.invalid/product",
    }
    assert engine.connect_calls == 1
    assert engine.begin_calls == 0
    sql, params = engine.connection.executions[0]
    assert "FROM online_food_price_snapshot" in sql
    assert "ORDER BY review_count DESC NULLS LAST" in sql
    assert params == {"keyword": "%사과%"}


def test_coupang_reader_preserves_none_for_no_match(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = _FakeEngine([])
    monkeypatch.setattr(coupang, "get_engine", lambda: engine)

    assert coupang.fetch_coupang_review_signal("없는상품") is None
    assert engine.connect_calls == 1
    assert engine.begin_calls == 0


def test_product_reader_preserves_query_parameters_and_projection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row = {
        "product_name": "사과 1kg",
        "mall_name": "쿠팡",
        "source_type": "coupang",
        "price": 12000,
        "rating": "4.5",
        "review_count": "20",
        "weight_text": "1kg",
        "product_url": "https://example.invalid/product",
    }
    engine = _FakeEngine([row])
    monkeypatch.setattr(product_collector, "get_engine", lambda: engine)

    result = product_collector.fetch_products_from_db("사과", limit=7)

    assert len(result) == 1
    item = result[0]
    assert item["name"] == "사과 1kg"
    assert item["platform"] == "쿠팡"
    assert item["price"] == 12000
    assert item["weight_g"] == 1000
    assert item["rating"] == 4.5
    assert item["review_count"] == 20
    assert item["url"] == "https://example.invalid/product"
    assert engine.connect_calls == 1
    assert engine.begin_calls == 0
    sql, params = engine.connection.executions[0]
    assert "FROM online_food_price_snapshot" in sql
    assert "ORDER BY collected_at DESC NULLS LAST" in sql
    assert params == {"keyword": "%사과%", "limit": 7}
