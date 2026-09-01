from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path


MARKET_FILE = Path("app/services/market/collector.py")
PROVIDER_FILE = Path("app/db/engine_provider.py")
MAIN_FILE = Path("app/main.py")


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _function(tree: ast.Module, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    raise AssertionError(f"function not found: {name}")


def _top_level_assignment_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


def _get_engine_connect_calls(node: ast.AST) -> list[ast.Call]:
    calls: list[ast.Call] = []
    for candidate in ast.walk(node):
        if not isinstance(candidate, ast.Call):
            continue
        func = candidate.func
        if not isinstance(func, ast.Attribute) or func.attr != "connect":
            continue
        owner = func.value
        if not isinstance(owner, ast.Call):
            continue
        if isinstance(owner.func, ast.Name) and owner.func.id == "get_engine":
            calls.append(candidate)
    return calls


def _get_engine_begin_calls(node: ast.AST) -> list[ast.Call]:
    calls: list[ast.Call] = []
    for candidate in ast.walk(node):
        if not isinstance(candidate, ast.Call):
            continue
        func = candidate.func
        if not isinstance(func, ast.Attribute) or func.attr != "begin":
            continue
        owner = func.value
        if not isinstance(owner, ast.Call):
            continue
        if isinstance(owner.func, ast.Name) and owner.func.id == "get_engine":
            calls.append(candidate)
    return calls


def test_market_collector_no_longer_owns_db_url_or_local_engine() -> None:
    names = _top_level_assignment_names(_tree(MARKET_FILE))
    assert "DB_URL" not in names
    assert "engine" not in names


def test_market_collector_no_longer_imports_or_calls_create_engine() -> None:
    tree = _tree(MARKET_FILE)

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "sqlalchemy":
            assert "create_engine" not in {alias.name for alias in node.names}
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "create_engine"


def test_market_collector_imports_bounded_get_engine() -> None:
    tree = _tree(MARKET_FILE)
    hits = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "app.db.engine_provider"
        and "get_engine" in {alias.name for alias in node.names}
    ]
    assert len(hits) == 1


def test_fetch_naver_uses_exactly_one_bounded_read_acquisition() -> None:
    fn = _function(_tree(MARKET_FILE), "fetch_naver_products_from_db")
    assert len(_get_engine_connect_calls(fn)) == 1
    assert _get_engine_begin_calls(fn) == []


def test_fetch_naver_executes_through_borrowed_connection() -> None:
    fn = _function(_tree(MARKET_FILE), "fetch_naver_products_from_db")

    with_nodes = [node for node in ast.walk(fn) if isinstance(node, ast.With)]
    matching = []

    for node in with_nodes:
        for item in node.items:
            expr = item.context_expr
            if (
                isinstance(expr, ast.Call)
                and isinstance(expr.func, ast.Attribute)
                and expr.func.attr == "connect"
                and isinstance(expr.func.value, ast.Call)
                and isinstance(expr.func.value.func, ast.Name)
                and expr.func.value.func.id == "get_engine"
                and isinstance(item.optional_vars, ast.Name)
                and item.optional_vars.id == "conn"
            ):
                matching.append(node)

    assert len(matching) == 1

    execute_lines = [
        node.lineno
        for node in ast.walk(matching[0])
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "conn"
        and node.func.attr == "execute"
    ]
    assert execute_lines


def test_market_collector_has_no_engine_or_db_url_compatibility_proxy() -> None:
    text = MARKET_FILE.read_text(encoding="utf-8")
    assert "DB_URL =" not in text
    assert "engine =" not in text
    assert "def get_engine" not in text


def test_provider_and_app_main_are_not_part_of_i4b2_migration() -> None:
    provider = PROVIDER_FILE.read_text(encoding="utf-8")
    main = MAIN_FILE.read_text(encoding="utf-8")

    assert "def get_engine" in provider
    assert "bind_engine(engine_lifecycle.engine)" in main
    assert "unbind_engine(engine_lifecycle.engine)" in main


def test_market_collector_import_remains_non_networking() -> None:
    sys.modules.pop("app.services.market.collector", None)
    module = importlib.import_module("app.services.market.collector")

    assert not hasattr(module, "engine")
    assert not hasattr(module, "DB_URL")
    assert hasattr(module, "fetch_naver_products_from_db")
