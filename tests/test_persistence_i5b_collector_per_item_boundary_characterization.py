from __future__ import annotations

import ast
from pathlib import Path


COLLECTOR_V4 = Path("app/services/collector_v4_runner.py")
DATALAB = Path("app/services/naver_datalab_service.py")
NAVER_SHOPPING = Path("app/services/naver_shopping_api_collector.py")


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _function(tree: ast.Module, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    raise AssertionError(f"function not found: {name}")


def _engine_calls(node: ast.AST, attr: str) -> list[ast.Call]:
    calls: list[ast.Call] = []
    for candidate in ast.walk(node):
        if not isinstance(candidate, ast.Call):
            continue
        func = candidate.func
        if (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id == "engine"
            and func.attr == attr
        ):
            calls.append(candidate)
    return calls


def _provider_engine_calls(node: ast.AST, attr: str) -> list[ast.Call]:
    calls: list[ast.Call] = []
    for candidate in ast.walk(node):
        if not isinstance(candidate, ast.Call):
            continue
        func = candidate.func
        if not isinstance(func, ast.Attribute):
            continue
        provider_call = func.value
        if not isinstance(provider_call, ast.Call):
            continue
        if not isinstance(provider_call.func, ast.Name):
            continue
        if provider_call.func.id == "get_engine" and func.attr == attr:
            calls.append(candidate)
    return calls


def _attribute_calls(node: ast.AST, attr: str) -> list[ast.Call]:
    calls: list[ast.Call] = []
    for candidate in ast.walk(node):
        if not isinstance(candidate, ast.Call):
            continue
        func = candidate.func
        if isinstance(func, ast.Attribute) and func.attr == attr:
            calls.append(candidate)
    return calls


def _direct_calls(node: ast.AST, name: str) -> list[ast.Call]:
    calls: list[ast.Call] = []
    for candidate in ast.walk(node):
        if (
            isinstance(candidate, ast.Call)
            and isinstance(candidate.func, ast.Name)
            and candidate.func.id == name
        ):
            calls.append(candidate)
    return calls


def _loops(node: ast.AST) -> list[ast.For | ast.AsyncFor]:
    return [
        candidate
        for candidate in ast.walk(node)
        if isinstance(candidate, (ast.For, ast.AsyncFor))
    ]


def test_tb06_collector_fetch_uses_direct_read_acquisition() -> None:
    fn = _function(_tree(COLLECTOR_V4), "fetch_targets")

    assert len(_provider_engine_calls(fn, "connect")) == 1
    assert _provider_engine_calls(fn, "begin") == []
    assert _engine_calls(fn, "connect") == []
    assert _engine_calls(fn, "begin") == []
    assert len(_attribute_calls(fn, "execute")) >= 1


def test_tb07_collector_update_owns_per_call_transaction() -> None:
    fn = _function(_tree(COLLECTOR_V4), "update_snapshot")

    assert len(_provider_engine_calls(fn, "begin")) == 1
    assert _provider_engine_calls(fn, "connect") == []
    assert _engine_calls(fn, "begin") == []
    assert _engine_calls(fn, "connect") == []
    assert len(_attribute_calls(fn, "execute")) >= 1


def test_collector_orchestrator_has_loop_and_invokes_per_item_update() -> None:
    fn = _function(_tree(COLLECTOR_V4), "run_collector_v4")

    assert len(_loops(fn)) >= 1
    assert len(_direct_calls(fn, "update_snapshot")) >= 1


def test_collector_orchestrator_does_not_own_direct_engine_transaction() -> None:
    fn = _function(_tree(COLLECTOR_V4), "run_collector_v4")

    assert _engine_calls(fn, "begin") == []
    assert _engine_calls(fn, "connect") == []


def test_tb10_cached_read_uses_bounded_provider_read_scope() -> None:
    fn = _function(_tree(DATALAB), "get_cached_keyword_trend")

    assert len(_provider_engine_calls(fn, "connect")) == 1
    assert _provider_engine_calls(fn, "begin") == []
    assert _engine_calls(fn, "connect") == []
    assert _engine_calls(fn, "begin") == []
    assert len(_attribute_calls(fn, "execute")) >= 1


def test_tb10_cached_write_owns_bounded_provider_transaction() -> None:
    fn = _function(_tree(DATALAB), "save_keyword_trend_cache")

    assert len(_provider_engine_calls(fn, "begin")) == 1
    assert _provider_engine_calls(fn, "connect") == []
    assert _engine_calls(fn, "begin") == []
    assert _engine_calls(fn, "connect") == []
    assert len(_attribute_calls(fn, "execute")) >= 1


def test_tb10_uses_provider_without_module_level_legacy_engine_authority() -> None:
    tree = _tree(DATALAB)
    database_imports = set()
    provider_imports = set()

    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "app.db.database":
            database_imports.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module == "app.db.engine_provider":
            provider_imports.update(alias.name for alias in node.names)

    assert "engine" not in database_imports
    assert "get_engine" in provider_imports


# 2026-11-11: 실행 중 DDL(ensure_collector_v2_columns)은 8ae055c(I7-B2)에서 수집기 밖으로 분리됐다.
# 예전 두 테스트(DDL 함수가 수집기 안에 있다고 가정)는 그 결정과 맞지 않아, 분리가 유지되는지만 확인한다.
def test_runtime_ddl_stays_detached_from_the_collector() -> None:
    names = {
        node.name
        for node in _tree(NAVER_SHOPPING).body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    assert "ensure_collector_v2_columns" not in names
    assert "ALTER TABLE" not in NAVER_SHOPPING.read_text(encoding="utf-8").upper()
