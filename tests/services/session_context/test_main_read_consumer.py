from __future__ import annotations

from pathlib import Path


MAIN_PATH = Path("app/main.py")


def _source() -> str:
    return MAIN_PATH.read_text(
        encoding="utf-8"
    )


def test_main_imports_canonical_session_context_read() -> None:
    source = _source()

    assert (
        "from app.services.session_context import ("
        in source
    )
    assert "get_session_context," in source


def test_main_has_no_direct_session_context_table_read() -> None:
    source = _source()

    assert (
        "FROM user_session_context"
        not in source
    )


def test_main_uses_canonical_session_context_read() -> None:
    source = _source()

    assert (
        "session_context = get_session_context("
        in source
    )


def test_main_preserves_session_context_object_flow() -> None:
    source = _source()

    assert (
        "session_context = None"
        in source
    )
    assert (
        "session_context,"
        in source
    )


def test_main_has_no_mapping_access_for_session_context() -> None:
    source = _source()

    assert (
        'session_context.get("last_fruit")'
        not in source
    )
    assert (
        'session_context.get("last_clicked_product")'
        not in source
    )
    assert (
        'session_context.get("last_priority")'
        not in source
    )


def test_main_does_not_own_session_context_policy_fields() -> None:
    source = _source()

    assert "session_context.last_fruit" not in source
    assert (
        "session_context.last_clicked_product"
        not in source
    )
    assert "session_context.last_priority" not in source
