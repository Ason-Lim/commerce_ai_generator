from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
STREAMLIT = ROOT / "app/ui/streamlit_app.py"
RENDERER = ROOT / "app/ui/hero_renderer_v3.py"
PACKAGE = ROOT / "app/services/recommendation/__init__.py"


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _tree(path: Path) -> ast.Module:
    return ast.parse(_source(path), filename=str(path))


def _imported_names(path: Path, module: str) -> list[str]:
    names: list[str] = []
    for node in ast.walk(_tree(path)):
        if isinstance(node, ast.ImportFrom) and node.module == module:
            names.extend(alias.name for alias in node.names)
    return names


def _calls(path: Path, name: str) -> list[ast.Call]:
    return [
        node
        for node in ast.walk(_tree(path))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == name
    ]


def _definitions(path: Path, name: str) -> list[ast.FunctionDef]:
    return [
        node
        for node in ast.walk(_tree(path))
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]


def test_story_v61_direct_import_has_exactly_one_ui_callsite():
    imported = _imported_names(
        STREAMLIT,
        "app.services.recommendation_story_engine_v61",
    )
    assert imported.count("build_recommendation_story_v61") == 1
    assert len(_calls(STREAMLIT, "build_recommendation_story_v61")) == 1


def test_compare_v62_direct_import_is_dormant_with_zero_ui_calls():
    imported = _imported_names(
        STREAMLIT,
        "app.services.recommendation_compare_engine_v62",
    )
    assert imported.count("build_hero_compare_v62") == 1
    assert _calls(STREAMLIT, "build_hero_compare_v62") == []


def test_local_hero_compare_has_one_definition_and_one_runtime_callsite():
    assert len(_definitions(STREAMLIT, "build_user_friendly_hero_compare")) == 1
    assert len(_calls(STREAMLIT, "build_user_friendly_hero_compare")) == 1


def test_renderer_consumes_story_v61_output_contract():
    source = _source(RENDERER)
    for key in (
        '"story_title"',
        '"story_summary"',
        '"story_bullets"',
        '"caution_story"',
    ):
        assert key in source
    assert "hero_story_v61" in source


def test_renderer_consumes_local_compare_output_contract():
    source = _source(RENDERER)
    assert 'hero_compare_v62.get("compare_summary")' in source
    assert 'hero_compare_v62.get("compare_bullets")' in source


def test_canonical_compare_responsibility_remains_distinct():
    imported = _imported_names(STREAMLIT, "app.services.recommendation")
    assert "build_compare_message" in imported
    assert "build_info_chips" in imported
    package_source = _source(PACKAGE)
    assert "build_recommendation_story_v61" not in package_source
    assert "build_hero_compare_v62" not in package_source
    assert "build_user_friendly_hero_compare" not in package_source
