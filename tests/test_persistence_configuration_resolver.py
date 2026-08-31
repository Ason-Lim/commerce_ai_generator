from __future__ import annotations

import importlib
import sys

import pytest

from app.core.config import (
    DEFAULT_DATABASE_URL,
    DatabaseUrlConflictError,
    resolve_database_url,
)


def test_no_aliases_uses_canonical_local_default() -> None:
    assert resolve_database_url({}) == DEFAULT_DATABASE_URL


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("DATABASE_URL", "postgresql://canonical/db"),
        ("COMMERCE_DB_URL", "postgresql://commerce/db"),
        ("FRUIT_DB_URL", "postgresql://fruit/db"),
    ],
)
def test_each_alias_can_resolve_independently(name: str, value: str) -> None:
    assert resolve_database_url({name: value}) == value


def test_empty_and_whitespace_values_are_absent() -> None:
    environ = {
        "DATABASE_URL": "   ",
        "COMMERCE_DB_URL": "",
        "FRUIT_DB_URL": "postgresql://fruit/db",
    }

    assert resolve_database_url(environ) == "postgresql://fruit/db"


def test_equal_duplicate_aliases_are_accepted_with_precedence_identity() -> None:
    value = "postgresql://shared/db"
    environ = {
        "FRUIT_DB_URL": value,
        "COMMERCE_DB_URL": value,
        "DATABASE_URL": value,
    }

    resolved = resolve_database_url(environ)

    assert resolved == value


def test_equal_alias_values_are_normalized_before_comparison() -> None:
    environ = {
        "DATABASE_URL": "  postgresql://shared/db  ",
        "COMMERCE_DB_URL": "postgresql://shared/db",
    }

    assert resolve_database_url(environ) == "postgresql://shared/db"


def test_conflicting_aliases_fail_closed() -> None:
    with pytest.raises(DatabaseUrlConflictError) as exc_info:
        resolve_database_url(
            {
                "DATABASE_URL": "postgresql://canonical/db",
                "COMMERCE_DB_URL": "postgresql://commerce/db",
            }
        )

    message = str(exc_info.value)
    assert "DATABASE_URL" in message
    assert "COMMERCE_DB_URL" in message


def test_conflict_error_redacts_credential_bearing_values() -> None:
    first = "postgresql://alice:super-secret@db-one.example/app"
    second = "postgresql://bob:another-secret@db-two.example/app"

    with pytest.raises(DatabaseUrlConflictError) as exc_info:
        resolve_database_url(
            {
                "DATABASE_URL": first,
                "FRUIT_DB_URL": second,
            }
        )

    message = str(exc_info.value)

    assert first not in message
    assert second not in message
    assert "super-secret" not in message
    assert "another-secret" not in message
    assert "DATABASE_URL" in message
    assert "FRUIT_DB_URL" in message


def test_compatibility_aliases_are_not_removed() -> None:
    assert resolve_database_url({"COMMERCE_DB_URL": "postgresql://commerce/db"}) == (
        "postgresql://commerce/db"
    )
    assert resolve_database_url({"FRUIT_DB_URL": "postgresql://fruit/db"}) == (
        "postgresql://fruit/db"
    )


def test_import_remains_non_networking_and_free_of_engine_construction(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("COMMERCE_DB_URL", raising=False)
    monkeypatch.delenv("FRUIT_DB_URL", raising=False)

    sys.modules.pop("app.core.config", None)
    module = importlib.import_module("app.core.config")

    assert module.DATABASE_URL == module.DEFAULT_DATABASE_URL
    assert not hasattr(module, "engine")
