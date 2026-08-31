from __future__ import annotations

import os
from collections.abc import Mapping

from dotenv import load_dotenv


DATABASE_URL_ENV_NAMES = (
    "DATABASE_URL",
    "COMMERCE_DB_URL",
    "FRUIT_DB_URL",
)
DEFAULT_DATABASE_URL = "postgresql+psycopg2://mom@localhost:5432/dashboard_db"


class DatabaseUrlConflictError(RuntimeError):
    """Raised when configured database URL aliases disagree."""


def _normalized_database_url(
    environ: Mapping[str, str],
    name: str,
) -> str | None:
    value = environ.get(name)
    if value is None:
        return None

    normalized = value.strip()
    if not normalized:
        return None

    return normalized


def resolve_database_url(
    environ: Mapping[str, str] | None = None,
) -> str:
    """Resolve the canonical database URL without exposing configured values."""

    source = os.environ if environ is None else environ

    configured = [
        (name, value)
        for name in DATABASE_URL_ENV_NAMES
        if (value := _normalized_database_url(source, name)) is not None
    ]

    if not configured:
        return DEFAULT_DATABASE_URL

    distinct_values = {value for _, value in configured}
    if len(distinct_values) > 1:
        names = ", ".join(name for name, _ in configured)
        raise DatabaseUrlConflictError(
            f"conflicting database URL environment variables: {names}"
        )

    return configured[0][1]


load_dotenv()

DATABASE_URL = resolve_database_url()


__all__ = [
    "DATABASE_URL",
    "DATABASE_URL_ENV_NAMES",
    "DEFAULT_DATABASE_URL",
    "DatabaseUrlConflictError",
    "resolve_database_url",
]
