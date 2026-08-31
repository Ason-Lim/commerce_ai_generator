from __future__ import annotations

import importlib
import sys

import pytest
import sqlalchemy


_DENIAL_MATCH = "MA-2026-034 I0-A denied real persistence resource access"


def test_sqlalchemy_create_engine_is_replaced_by_non_networking_sentinel() -> None:
    engine = sqlalchemy.create_engine("postgresql://example.invalid/test")

    assert engine.__class__.__name__ == "_DeniedPersistenceEngine"

    with pytest.raises(RuntimeError, match=_DENIAL_MATCH):
        engine.connect()

    with pytest.raises(RuntimeError, match=_DENIAL_MATCH):
        engine.begin()

    with pytest.raises(RuntimeError, match=_DENIAL_MATCH):
        engine.raw_connection()


def test_application_database_module_import_cannot_create_real_engine() -> None:
    sys.modules.pop("app.db.database", None)

    module = importlib.import_module("app.db.database")

    assert module.engine.__class__.__name__ == "_DeniedPersistenceEngine"

    with pytest.raises(RuntimeError, match=_DENIAL_MATCH):
        module.engine.connect()


def test_analytics_logger_import_remains_non_networking() -> None:
    sys.modules.pop("app.services.analytics_logger", None)

    module = importlib.import_module("app.services.analytics_logger")

    assert module.engine.__class__.__name__ == "_DeniedPersistenceEngine"

    with pytest.raises(RuntimeError, match=_DENIAL_MATCH):
        module.engine.begin()


def test_denied_engine_dispose_is_local_noop() -> None:
    engine = sqlalchemy.create_engine("postgresql://example.invalid/test")

    assert engine.dispose() is None
