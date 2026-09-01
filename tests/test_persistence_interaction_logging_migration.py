from __future__ import annotations

import ast
from pathlib import Path

import pytest

from app.db import engine_provider


LOGGER_FILES = (
    Path("app/services/analytics_logger.py"),
    Path("app/services/context_logger.py"),
    Path("app/services/impression_logger.py"),
)


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _function(path: Path, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    tree = _tree(path)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    raise AssertionError(f"function not found: {path}:{name}")


def _engine_begin_count(fn: ast.AST) -> int:
    count = 0
    for node in ast.walk(fn):
        if not isinstance(node, ast.With):
            continue
        for item in node.items:
            expr = item.context_expr
            if (
                isinstance(expr, ast.Call)
                and isinstance(expr.func, ast.Attribute)
                and expr.func.attr == "begin"
            ):
                count += 1
    return count


def _kw_name(call: ast.Call, key: str) -> str | None:
    for kw in call.keywords:
        if kw.arg == key and isinstance(kw.value, ast.Name):
            return kw.value.id
    return None


def test_provider_fails_closed_while_unbound() -> None:
    engine_provider.unbind_engine()

    assert engine_provider.is_bound() is False
    with pytest.raises(engine_provider.EngineProviderUnboundError):
        engine_provider.get_engine()


def test_provider_binds_one_exact_engine_identity() -> None:
    engine_provider.unbind_engine()
    sentinel = object()

    engine_provider.bind_engine(sentinel)

    assert engine_provider.is_bound() is True
    assert engine_provider.get_engine() is sentinel

    engine_provider.unbind_engine(sentinel)


def test_provider_rejects_conflicting_rebind() -> None:
    engine_provider.unbind_engine()
    first = object()
    second = object()

    engine_provider.bind_engine(first)

    with pytest.raises(engine_provider.EngineProviderConflictError):
        engine_provider.bind_engine(second)

    assert engine_provider.get_engine() is first
    engine_provider.unbind_engine(first)


def test_provider_unbind_restores_fail_closed_state() -> None:
    engine_provider.unbind_engine()
    sentinel = object()

    engine_provider.bind_engine(sentinel)
    engine_provider.unbind_engine(sentinel)

    assert engine_provider.is_bound() is False
    with pytest.raises(engine_provider.EngineProviderUnboundError):
        engine_provider.get_engine()


def test_logger_local_engine_constructors_are_removed() -> None:
    for path in LOGGER_FILES:
        text = path.read_text(encoding="utf-8")
        assert "create_engine(" not in text
        assert "DB_URL" not in text


def test_logger_public_signatures_remain_unchanged() -> None:
    expected = {
        (LOGGER_FILES[0], "log_search"): ["session_id", "query", "priority", "result_count", "top_product"],
        (LOGGER_FILES[0], "log_product_click"): ["session_id", "query", "product"],
        (LOGGER_FILES[1], "log_user_context"): ["session_id", "intent_data"],
        (LOGGER_FILES[2], "log_recommendation_impressions"): [
            "session_id",
            "query",
            "items",
            "selected_section",
        ],
    }

    for (path, name), args in expected.items():
        fn = _function(path, name)
        assert [arg.arg for arg in fn.args.args] == args


def test_transaction_owners_remain_in_logger_functions() -> None:
    assert _engine_begin_count(_function(LOGGER_FILES[0], "log_search")) == 1
    assert _engine_begin_count(_function(LOGGER_FILES[0], "log_product_click")) == 1
    assert _engine_begin_count(_function(LOGGER_FILES[1], "log_user_context")) == 1
    assert _engine_begin_count(_function(LOGGER_FILES[2], "log_recommendation_impressions")) == 1


def test_tb03_same_connection_forwarding_is_preserved() -> None:
    fn = _function(LOGGER_FILES[0], "log_product_click")
    calls: dict[str, ast.Call] = {}

    for node in ast.walk(fn):
        if not isinstance(node, ast.Call):
            continue
        target = node.func
        if isinstance(target, ast.Name) and target.id in {
            "update_user_preference",
            "update_session_context",
        }:
            calls[target.id] = node

    assert set(calls) == {"update_user_preference", "update_session_context"}
    assert _kw_name(calls["update_user_preference"], "conn") == "conn"
    assert _kw_name(calls["update_session_context"], "conn") == "conn"


def test_loggers_resolve_engine_through_bounded_provider() -> None:
    for path in LOGGER_FILES:
        text = path.read_text(encoding="utf-8")
        assert "from app.db.engine_provider import get_engine" in text
        assert "get_engine().begin()" in text


def test_fastapi_lifespan_binds_and_unbinds_provider() -> None:
    text = Path("app/main.py").read_text(encoding="utf-8")

    assert "from app.db.engine_provider import bind_engine, unbind_engine" in text
    assert "bind_engine(engine_lifecycle.engine)" in text
    assert "unbind_engine(engine_lifecycle.engine)" in text

    bind_offset = text.index("bind_engine(engine_lifecycle.engine)")
    yield_offset = text.index("yield")
    unbind_offset = text.index("unbind_engine(engine_lifecycle.engine)")

    assert bind_offset < yield_offset < unbind_offset


def test_streamlit_cms008_uses_bounded_provider_and_preserves_transaction_shape() -> None:
    text = Path("app/ui/streamlit_app.py").read_text(encoding="utf-8")

    assert "from app.services.analytics_logger import log_search, log_product_click, engine" not in text
    assert "from app.services.analytics_logger import log_search, log_product_click" in text
    assert "from app.db.engine_provider import get_engine" in text
    assert text.count("with get_engine().connect() as conn:") == 1
    assert text.count("with get_engine().begin() as conn:") == 1
    assert "with engine.connect() as conn:" not in text
    assert "with engine.begin() as conn:" not in text


def test_loggers_do_not_export_raw_engine_or_dead_db_url_configuration() -> None:
    for path in LOGGER_FILES:
        text = path.read_text(encoding="utf-8")
        tree = _tree(path)

        module_names: set[str] = set()
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        module_names.add(target.id)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                module_names.add(node.target.id)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                module_names.add(node.name)

        assert "engine" not in module_names
        assert "DB_URL" not in text
