from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class SessionContext:
    last_query: str = ""
    last_priority: str = ""
    last_fruit: str = ""
    last_clicked_product: str = ""
    last_event_type: str = ""

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, Any] | None,
    ) -> "SessionContext | None":
        if value is None:
            return None

        return cls(
            last_query=str(
                value.get("last_query") or ""
            ),
            last_priority=str(
                value.get("last_priority") or ""
            ),
            last_fruit=str(
                value.get("last_fruit") or ""
            ),
            last_clicked_product=str(
                value.get("last_clicked_product") or ""
            ),
            last_event_type=str(
                value.get("last_event_type") or ""
            ),
        )
