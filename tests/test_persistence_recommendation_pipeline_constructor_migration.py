from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path


PIPELINE_FILE = Path("app/services/recommendation_pipeline.py")


def _tree() -> ast.Module:
    return ast.parse(PIPELINE_FILE.read_text(encoding="utf-8"))


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


def test_recommendation_pipeline_no_longer_owns_db_url() -> None:
    assert "DB_URL" not in _top_level_assignment_names(_tree())


def test_recommendation_pipeline_no_longer_imports_or_calls_create_engine() -> None:
    tree = _tree()

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "sqlalchemy":
            assert "create_engine" not in {alias.name for alias in node.names}
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "create_engine"


def test_recommendation_pipeline_no_longer_exports_local_engine_assignment() -> None:
    assert "engine" not in _top_level_assignment_names(_tree())


def test_recommendation_pipeline_does_not_depend_on_bounded_provider() -> None:
    tree = _tree()

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.module != "app.db.engine_provider"


def test_recommendation_pipeline_has_no_engine_or_db_url_compatibility_proxy() -> None:
    text = PIPELINE_FILE.read_text(encoding="utf-8")
    assert "def get_engine" not in text
    assert "engine =" not in text
    assert "DB_URL =" not in text


def test_recommendation_pipeline_import_remains_non_networking() -> None:
    sys.modules.pop("app.services.recommendation_pipeline", None)
    module = importlib.import_module("app.services.recommendation_pipeline")

    assert not hasattr(module, "engine")
    assert not hasattr(module, "DB_URL")


def test_recommendation_pipeline_public_behavior_symbols_remain_available() -> None:
    sys.modules.pop("app.services.recommendation_pipeline", None)
    module = importlib.import_module("app.services.recommendation_pipeline")

    assert hasattr(module, "resolve_canonical_priority")
