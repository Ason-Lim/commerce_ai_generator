from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy import create_engine

from app.core.config import resolve_database_url


EngineFactory = Callable[..., Any]
DatabaseUrlResolver = Callable[[], str]


class EngineLifecycle:
    """Explicit, lazy lifecycle authority for one canonical engine instance."""

    def __init__(
        self,
        *,
        resolver: DatabaseUrlResolver = resolve_database_url,
        factory: EngineFactory = create_engine,
    ) -> None:
        self._resolver = resolver
        self._factory = factory
        self._engine: Any | None = None

    @property
    def engine(self) -> Any | None:
        return self._engine

    @property
    def initialized(self) -> bool:
        return self._engine is not None

    def initialize(self) -> Any:
        if self._engine is not None:
            return self._engine

        url = self._resolver()
        candidate = self._factory(url, pool_pre_ping=True)
        self._engine = candidate
        return candidate


__all__ = [
    "DatabaseUrlResolver",
    "EngineFactory",
    "EngineLifecycle",
]
