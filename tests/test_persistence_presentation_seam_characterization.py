from __future__ import annotations

import ast
from pathlib import Path


ADMIN_FILE = Path("app/ui/admin_dashboard.py")
STREAMLIT_FILE = Path("app/ui/streamlit_app.py")


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _function(tree: ast.Module, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    raise AssertionError(f"function not found: {name}")


def _direct_imported_names(tree: ast.Module, module: str) -> set[str]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == module:
            names.update(alias.name for alias in node.names)
    return names


def _name_attribute_calls(node: ast.AST, owner: str, attr: str) -> list[ast.Call]:
    calls: list[ast.Call] = []
    for candidate in ast.walk(node):
        if not isinstance(candidate, ast.Call):
            continue
        func = candidate.func
        if not isinstance(func, ast.Attribute):
            continue
        if not isinstance(func.value, ast.Name):
            continue
        if func.value.id == owner and func.attr == attr:
            calls.append(candidate)
    return calls


def _provider_attribute_calls(node: ast.AST, attr: str) -> list[ast.Call]:
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


def test_admin_dashboard_remains_the_legacy_presentation_seam() -> None:
    tree = _tree(ADMIN_FILE)

    assert "engine" in _direct_imported_names(tree, "app.db.database")
    assert "get_engine" not in _direct_imported_names(tree, "app.db.engine_provider")


def test_admin_dashboard_owns_exactly_two_legacy_read_acquisitions() -> None:
    tree = _tree(ADMIN_FILE)

    assert len(_name_attribute_calls(tree, "engine", "connect")) == 2
    assert _name_attribute_calls(tree, "engine", "begin") == []


def test_admin_load_df_owns_one_legacy_read_acquisition() -> None:
    fn = _function(_tree(ADMIN_FILE), "load_df")

    assert len(_name_attribute_calls(fn, "engine", "connect")) == 1
    assert _name_attribute_calls(fn, "engine", "begin") == []


def test_admin_load_view_owns_one_legacy_read_acquisition() -> None:
    fn = _function(_tree(ADMIN_FILE), "load_view")

    assert len(_name_attribute_calls(fn, "engine", "connect")) == 1
    assert _name_attribute_calls(fn, "engine", "begin") == []


def test_streamlit_app_uses_bounded_provider_instead_of_legacy_engine_import() -> None:
    tree = _tree(STREAMLIT_FILE)

    assert "engine" not in _direct_imported_names(tree, "app.db.database")
    assert "get_engine" in _direct_imported_names(tree, "app.db.engine_provider")


def test_streamlit_app_preserves_bounded_read_acquisition() -> None:
    tree = _tree(STREAMLIT_FILE)

    assert len(_provider_attribute_calls(tree, "connect")) >= 1


def test_streamlit_app_preserves_bounded_transaction_acquisition() -> None:
    tree = _tree(STREAMLIT_FILE)

    assert len(_provider_attribute_calls(tree, "begin")) >= 1


def test_presentation_seams_do_not_share_the_same_persistence_authority_shape() -> None:
    admin_tree = _tree(ADMIN_FILE)
    streamlit_tree = _tree(STREAMLIT_FILE)

    assert "engine" in _direct_imported_names(admin_tree, "app.db.database")
    assert "engine" not in _direct_imported_names(streamlit_tree, "app.db.database")
    assert "get_engine" not in _direct_imported_names(admin_tree, "app.db.engine_provider")
    assert "get_engine" in _direct_imported_names(streamlit_tree, "app.db.engine_provider")
