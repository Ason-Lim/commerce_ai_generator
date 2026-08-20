from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.session_context.models import (
    SessionContext,
)


def calculate_session_context_boost(
    session_context: SessionContext | Mapping[str, Any] | None,
    item: Mapping[str, Any],
    base_priority: str,
) -> int:
    if session_context is None:
        return 0

    if isinstance(
        session_context,
        SessionContext,
    ):
        last_fruit = session_context.last_fruit
        last_clicked_product = (
            session_context.last_clicked_product
        )
        last_priority = (
            session_context.last_priority
        )
    else:
        last_fruit = str(
            session_context.get("last_fruit") or ""
        )
        last_clicked_product = str(
            session_context.get(
                "last_clicked_product"
            )
            or ""
        )
        last_priority = str(
            session_context.get(
                "last_priority"
            )
            or ""
        )

    boost = 0

    if (
        last_fruit
        and last_fruit
        == (item.get("fruit_name") or "")
    ):
        boost += 2

    if (
        last_clicked_product
        and last_clicked_product
        == (item.get("product_name") or "")
    ):
        boost += 5

    if (
        last_priority
        and last_priority == base_priority
    ):
        boost += 1

    return boost
