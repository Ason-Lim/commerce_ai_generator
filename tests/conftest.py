"""MA-2026-034 Phase 4 I0-A persistence test safety foundation.

This pytest bootstrap installs a non-networking SQLAlchemy engine factory before
application test-target modules are imported.  The returned engine is deliberately
incapable of opening a real database connection.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import sqlalchemy
import sqlalchemy.engine
import sqlalchemy.engine.create


_DENIAL_MESSAGE = (
    "MA-2026-034 I0-A denied real persistence resource access during non-integration tests"
)


@dataclass(frozen=True)
class _DeniedPersistenceEngine:
    """Inert engine-shaped sentinel that cannot acquire a real resource."""

    url: Any = None

    def connect(self, *args: Any, **kwargs: Any) -> Any:
        raise RuntimeError(_DENIAL_MESSAGE)

    def begin(self, *args: Any, **kwargs: Any) -> Any:
        raise RuntimeError(_DENIAL_MESSAGE)

    def raw_connection(self, *args: Any, **kwargs: Any) -> Any:
        raise RuntimeError(_DENIAL_MESSAGE)

    def dispose(self, *args: Any, **kwargs: Any) -> None:
        return None


def _denied_create_engine(url: Any, *args: Any, **kwargs: Any) -> _DeniedPersistenceEngine:
    """Return an inert sentinel instead of constructing a real SQLAlchemy engine."""

    return _DeniedPersistenceEngine(url=url)


# Install before application test-target imports during pytest collection.
sqlalchemy.create_engine = _denied_create_engine
sqlalchemy.engine.create_engine = _denied_create_engine
sqlalchemy.engine.create.create_engine = _denied_create_engine
