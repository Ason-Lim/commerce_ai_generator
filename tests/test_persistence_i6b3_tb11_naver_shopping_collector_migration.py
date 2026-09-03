from __future__ import annotations

import ast
import hashlib
from pathlib import Path


PRODUCTION = Path("app/services/naver_shopping_api_collector.py")
DDL_SHA256 = "e849c94c9866719a581316b07e751cd63e5bb8453c146008985652ed14e56db8"


def _source() -> str:
    return PRODUCTION.read_text(encoding="utf-8")


def _functions() -> dict[str, str]:
    source = _source()
    tree = ast.parse(source, filename=str(PRODUCTION))
    return {
        node.name: ast.get_source_segment(source, node) or ""
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def test_tb11_has_mixed_legacy_ddl_and_provider_runtime_imports() -> None:
    source = _source()
    assert source.count("from app.db.database import engine") == 1
    assert source.count("from app.db.engine_provider import get_engine") == 1


def test_ddl_function_is_byte_preserved_and_provider_free() -> None:
    ddl = _functions()["ensure_collector_v2_columns"]
    assert hashlib.sha256(ddl.encode()).hexdigest() == DDL_SHA256
    assert "engine.begin()" in ddl
    assert "get_engine()" not in ddl


def test_insert_products_uses_provider_begin_and_preserves_ddl_call() -> None:
    write = _functions()["insert_products"]
    assert "ensure_collector_v2_columns()" in write
    assert "get_engine().begin()" in write
    assert "engine.begin()" not in write
    assert "INSERT INTO online_food_price_snapshot" in write
    assert "ON CONFLICT DO NOTHING" in write


def test_credentials_external_io_and_orchestrator_boundaries_are_preserved() -> None:
    functions = _functions()
    assert "os.getenv(" in functions["get_naver_credentials"]
    assert "requests.get(" in functions["call_naver_api"]
    orchestrator = functions["collect_naver_products"]
    assert "call_naver_api(" in orchestrator
    assert "insert_products(" in orchestrator
    assert "engine.begin()" not in orchestrator
    assert "engine.connect()" not in orchestrator
    assert "get_engine()" not in orchestrator


def test_insert_products_runtime_uses_fake_provider_without_real_resources(monkeypatch) -> None:
    from app.services import naver_shopping_api_collector as subject

    events: list[str] = []
    executions: list[tuple[object, dict[str, object]]] = []

    class FakeConnection:
        def execute(self, statement, parameters):
            executions.append((statement, parameters))

    class FakeBegin:
        def __enter__(self):
            events.append("provider_begin_enter")
            return FakeConnection()

        def __exit__(self, exc_type, exc, traceback):
            events.append("provider_begin_exit")
            return False

    class FakeProviderEngine:
        def begin(self):
            events.append("provider_begin")
            return FakeBegin()

    class ForbiddenLegacyEngine:
        def begin(self):
            raise AssertionError("legacy runtime engine must not be acquired")

    monkeypatch.setattr(subject, "ensure_collector_v2_columns", lambda: events.append("ddl_call_preserved_but_not_executed"))
    monkeypatch.setattr(subject, "get_engine", lambda: FakeProviderEngine())
    monkeypatch.setattr(subject, "engine", ForbiddenLegacyEngine())
    monkeypatch.setattr(subject.requests, "get", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("network must not execute")))

    item = {
        "title": "테스트 사과 1kg",
        "mallName": "테스트몰",
        "lprice": "10000",
        "hprice": "12000",
        "link": "https://example.invalid/item",
        "productId": "P-1",
    }
    subject.insert_products([item], "사과")

    assert events == [
        "ddl_call_preserved_but_not_executed",
        "provider_begin",
        "provider_begin_enter",
        "provider_begin_exit",
    ]
    assert len(executions) == 1
    _statement, parameters = executions[0]
    assert parameters["keyword"] == "사과"
    assert parameters["product_name"] == "테스트 사과 1kg"
    assert parameters["price"] == 10000
    assert parameters["weight_g"] == 1000
    assert parameters["unit_price_per_kg"] == 10000.0


def test_global_legacy_importer_count_remains_nineteen() -> None:
    importers = [
        path
        for path in Path("app").rglob("*.py")
        if "from app.db.database import engine" in path.read_text(encoding="utf-8")
    ]
    assert len(importers) == 19
