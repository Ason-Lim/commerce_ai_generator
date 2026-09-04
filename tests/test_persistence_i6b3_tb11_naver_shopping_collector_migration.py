from __future__ import annotations

import ast
from pathlib import Path

PRODUCTION = Path("app/services/naver_shopping_api_collector.py")
def _source(): return PRODUCTION.read_text(encoding="utf-8")
def _functions():
    source = _source(); tree = ast.parse(source, filename=str(PRODUCTION))
    return {node.name: ast.get_source_segment(source, node) or "" for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}

def test_tb11_has_detached_ddl_and_provider_runtime_import():
    source = _source()
    assert source.count("from app.db.database import engine") == 0
    assert source.count("from app.db.engine_provider import get_engine") == 1

def test_ddl_function_is_detached():
    assert "ensure_collector_v2_columns" not in _functions()

def test_insert_products_uses_provider_begin_without_ddl_call():
    write = _functions()["insert_products"]
    assert "ensure_collector_v2_columns()" not in write
    assert "get_engine().begin()" in write and "engine.begin()" not in write
    assert "INSERT INTO online_food_price_snapshot" in write and "ON CONFLICT DO NOTHING" in write

def test_credentials_external_io_and_orchestrator_boundaries_are_preserved():
    functions = _functions()
    assert "os.getenv(" in functions["get_naver_credentials"]
    assert "requests.get(" in functions["call_naver_api"]
    orchestrator = functions["collect_naver_products"]
    assert "call_naver_api(" in orchestrator and "insert_products(" in orchestrator
    assert "engine.begin()" not in orchestrator and "engine.connect()" not in orchestrator and "get_engine()" not in orchestrator

def test_insert_products_runtime_uses_fake_provider_without_real_resources(monkeypatch):
    from app.services import naver_shopping_api_collector as subject
    events = []; executions = []
    class FakeConnection:
        def execute(self, statement, parameters): executions.append((statement, parameters))
    class FakeBegin:
        def __enter__(self): events.append("provider_begin_enter"); return FakeConnection()
        def __exit__(self, exc_type, exc, traceback): events.append("provider_begin_exit"); return False
    class FakeProviderEngine:
        def begin(self): events.append("provider_begin"); return FakeBegin()
    monkeypatch.setattr(subject, "get_engine", lambda: FakeProviderEngine())
    monkeypatch.setattr(subject.requests, "get", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("network must not execute")))
    item = {"title": "테스트 사과 1kg", "mallName": "테스트몰", "lprice": "10000", "hprice": "12000", "link": "https://example.invalid/item", "productId": "P-1"}
    subject.insert_products([item], "사과")
    assert events == ["provider_begin", "provider_begin_enter", "provider_begin_exit"]
    assert len(executions) == 1
    parameters = executions[0][1]
    assert parameters["keyword"] == "사과" and parameters["product_name"] == "테스트 사과 1kg"
    assert parameters["price"] == 10000 and parameters["weight_g"] == 1000 and parameters["unit_price_per_kg"] == 10000.0

def test_global_legacy_importer_count_is_six():
    importers = [path for path in Path("app").rglob("*.py") if "from app.db.database import engine" in path.read_text(encoding="utf-8")]
    assert len(importers) == 6
