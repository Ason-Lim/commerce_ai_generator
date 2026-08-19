from __future__ import annotations

from pathlib import Path


STREAMLIT_PATH = Path(
    "app/ui/streamlit_app.py"
)


def _source() -> str:
    return STREAMLIT_PATH.read_text(
        encoding="utf-8"
    )


def test_presentation_imports_canonical_preference() -> None:
    source = _source()

    assert (
        "from app.services.preference import ("
        in source
    )


def test_presentation_has_no_legacy_preference_import() -> None:
    source = _source()

    assert (
        "from app.services.preference_service import"
        not in source
    )


def test_presentation_preserves_preference_calls() -> None:
    source = _source()

    assert "get_user_preference(" in source
    assert "decide_adaptive_priority(" in source
    assert "update_user_preference(" in source


def test_presentation_imports_all_three_contracts() -> None:
    source = _source()

    expected = [
        "update_user_preference,",
        "get_user_preference,",
        "decide_adaptive_priority,",
    ]

    for item in expected:
        assert item in source
