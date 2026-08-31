from __future__ import annotations

from typing import Any, Protocol


class BorrowedExecutionConnection(Protocol):
    """Minimal structural capability for caller-owned persistence connections."""

    def execute(
        self,
        statement: Any,
        params: dict[str, Any],
    ) -> Any:
        ...


__all__ = [
    "BorrowedExecutionConnection",
]
