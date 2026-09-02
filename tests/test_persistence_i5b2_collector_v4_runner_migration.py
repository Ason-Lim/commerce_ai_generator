from __future__ import annotations

import ast
from pathlib import Path


TARGET = Path("app/services/collector_v4_runner.py")


def _tree() -> ast.Module:
    return ast.parse(TARGET.read_text(encoding="utf-8"))


def _function(name: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    for node in _tree().body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    raise AssertionError(f"function not found: {name}")


def _direct_import_names(module: str) -> set[str]:
    names: set[str] = set()
    for node in _tree().body:
        if isinstance(node, ast.ImportFrom) and node.module == module:
            names.update(alias.name for alias in node.names)
    return names


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


def _legacy_engine_attribute_calls(node: ast.AST, attr: str) -> list[ast.Call]:
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


def _direct_calls(node: ast.AST, name: str) -> list[ast.Call]:
    return [
        candidate
        for candidate in ast.walk(node)
        if isinstance(candidate, ast.Call)
        and isinstance(candidate.func, ast.Name)
        and candidate.func.id == name
    ]


def _loops(node: ast.AST) -> list[ast.For | ast.AsyncFor]:
    return [
        candidate
        for candidate in ast.walk(node)
        if isinstance(candidate, (ast.For, ast.AsyncFor))
    ]


def test_collector_v4_uses_bounded_provider_not_legacy_database_engine() -> None:
    assert "engine" not in _direct_import_names("app.db.database")
    assert "get_engine" in _direct_import_names("app.db.engine_provider")


def test_fetch_targets_preserves_nontransactional_read_acquisition() -> None:
    fn = _function("fetch_targets")

    assert len(_provider_attribute_calls(fn, "connect")) == 1
    assert _provider_attribute_calls(fn, "begin") == []
    assert _legacy_engine_attribute_calls(fn, "connect") == []
    assert _legacy_engine_attribute_calls(fn, "begin") == []


def test_update_snapshot_preserves_per_call_transaction() -> None:
    fn = _function("update_snapshot")

    assert len(_provider_attribute_calls(fn, "begin")) == 1
    assert _provider_attribute_calls(fn, "connect") == []
    assert _legacy_engine_attribute_calls(fn, "begin") == []
    assert _legacy_engine_attribute_calls(fn, "connect") == []


def test_orchestrator_preserves_loop_and_per_item_update_call() -> None:
    fn = _function("run_collector_v4")

    assert len(_loops(fn)) >= 1
    assert len(_direct_calls(fn, "update_snapshot")) >= 1


def test_orchestrator_does_not_acquire_database_boundary_directly() -> None:
    fn = _function("run_collector_v4")

    assert _provider_attribute_calls(fn, "connect") == []
    assert _provider_attribute_calls(fn, "begin") == []
    assert _legacy_engine_attribute_calls(fn, "connect") == []
    assert _legacy_engine_attribute_calls(fn, "begin") == []


def test_module_does_not_export_assigned_engine_symbol() -> None:
    assigned: set[str] = set()
    for node in _tree().body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assigned.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            assigned.add(node.target.id)

    assert "engine" not in assigned
