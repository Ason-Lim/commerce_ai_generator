from __future__ import annotations

import inspect

import app.services.analytics_logger as analytics
from app.services.preference import (
    update_user_preference as canonical_update,
)


def test_analytics_uses_canonical_preference_export() -> None:
    assert (
        analytics.update_user_preference
        is canonical_update
    )


def test_analytics_preference_function_module_is_canonical() -> None:
    assert (
        analytics.update_user_preference.__module__
        == "app.services.preference.service"
    )


def test_analytics_source_has_no_legacy_preference_import() -> None:
    source = inspect.getsource(
        analytics
    )

    assert (
        "app.services.preference_service"
        not in source
    )
