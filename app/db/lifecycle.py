from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy import create_engine

from app.core.config import resolve_database_url


EngineFactory = Callable[..., Any]
DatabaseUrlResolver = Callable[[], str]


class EngineLifecycleDisposedError(RuntimeError):
    """Raised when initialization is attempted after terminal disposal."""


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
        self._disposed = False

    @property
    def engine(self) -> Any | None:
        return self._engine

    @property
    def initialized(self) -> bool:
        return self._engine is not None

    @property
    def disposed(self) -> bool:
        return self._disposed

    def initialize(self) -> Any:
        if self._disposed:
            raise EngineLifecycleDisposedError(
                "engine lifecycle has been disposed"
            )

        if self._engine is not None:
            return self._engine

        url = self._resolver()
        candidate = self._factory(url, pool_pre_ping=True)
        self._engine = candidate
        return candidate

    def dispose(self) -> None:
        if self._disposed:
            return

        if self._engine is None:
            return

        engine = self._engine
        engine.dispose()
        self._engine = None
        self._disposed = True


__all__ = [
    "DatabaseUrlResolver",
    "EngineFactory",
    "EngineLifecycle",
    "EngineLifecycleDisposedError",
]
