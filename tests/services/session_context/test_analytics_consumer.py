from __future__ import annotations

import inspect

import app.services.analytics_logger as analytics
from app.services.session_context import (
    update_session_context as canonical_update,
)


def test_analytics_uses_canonical_session_context_export() -> None:
    assert (
        analytics.update_session_context
        is canonical_update
    )


def test_analytics_session_context_function_is_canonical() -> None:
    assert (
        analytics.update_session_context.__module__
        == "app.services.session_context.service"
    )


def test_analytics_has_no_legacy_session_context_import() -> None:
    source = inspect.getsource(
        analytics
    )

    assert (
        "app.services.session_context_service"
        not in source
    )


def test_analytics_preserves_session_context_call() -> None:
    source = inspect.getsource(
        analytics
    )

    assert "update_session_context(" in source
