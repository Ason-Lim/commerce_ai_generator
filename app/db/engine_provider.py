from __future__ import annotations

from typing import Any


class EngineProviderUnboundError(RuntimeError):
    """Raised when canonical engine access is attempted before bind or after unbind."""


class EngineProviderConflictError(RuntimeError):
    """Raised when a different engine identity is bound while already bound."""


_engine: Any | None = None


def bind_engine(engine: Any) -> None:
    global _engine

    if engine is None:
        raise ValueError("engine must not be None")

    if _engine is None:
        _engine = engine
        return

    if _engine is not engine:
        raise EngineProviderConflictError("a different canonical engine is already bound")


def get_engine() -> Any:
    if _engine is None:
        raise EngineProviderUnboundError("canonical engine is not bound")
    return _engine


def unbind_engine(engine: Any | None = None) -> None:
    global _engine

    if _engine is None:
        return

    if engine is not None and _engine is not engine:
        raise EngineProviderConflictError("cannot unbind a different engine identity")

    _engine = None


def is_bound() -> bool:
    return _engine is not None


__all__ = [
    "EngineProviderConflictError",
    "EngineProviderUnboundError",
    "bind_engine",
    "get_engine",
    "is_bound",
    "unbind_engine",
]
