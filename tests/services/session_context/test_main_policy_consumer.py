from __future__ import annotations

from pathlib import Path


MAIN_PATH = Path("app/main.py")


def _source() -> str:
    return MAIN_PATH.read_text(
        encoding="utf-8"
    )


def test_main_imports_canonical_session_context_policy() -> None:
    source = _source()

    assert (
        "calculate_session_context_boost"
        in source
    )

    assert (
        "from app.services.session_context import ("
        in source
    )


def test_main_calls_canonical_session_context_policy() -> None:
    source = _source()

    expected = (
        "session_context_boost = "
        "calculate_session_context_boost("
    )

    assert expected in source


def test_main_passes_canonical_policy_inputs() -> None:
    source = _source()

    expected = (
        "calculate_session_context_boost(\n"
        "            session_context,\n"
        "            item,\n"
        "            base_priority,\n"
        "        )"
    )

    assert expected in source


def test_main_has_no_inline_session_context_boost_rules() -> None:
    source = _source()

    assert "session_context_boost += 2" not in source
    assert "session_context_boost += 5" not in source
    assert "session_context_boost += 1" not in source


def test_main_preserves_session_context_boost_usage() -> None:
    source = _source()

    assert "session_context_boost" in source
