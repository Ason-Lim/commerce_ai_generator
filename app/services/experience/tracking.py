from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from urllib.parse import urlencode


DEFAULT_TRACKING_URL = (
    "http://127.0.0.1:8000/track-click"
)


def build_tracking_url(
    *,
    product_url: str,
    item: Mapping[str, Any],
    session_id: str = "",
    query: str = "",
    section: str = "main",
    priority: str = "trust",
    base_url: str = DEFAULT_TRACKING_URL,
) -> str:
    """
    Build the existing tracking redirect URL.

    Presentation owns interaction context.
    Experience owns tracking URL composition.
    The existing /track-click endpoint owns logging and redirect behavior.
    """

    if not product_url:
        return ""

    params = {
        "session_id": session_id,
        "query": query,
        "product_name": (
            item.get("product_name")
            or item.get("name")
            or ""
        ),
        "seller_name": (
            item.get("seller_name")
            or ""
        ),
        "product_url": product_url,
        "selected_priority": priority,
        "selected_section": section,
        "recommendation_mode": (
            item.get("recommendation_mode")
            or "ranking"
        ),
        "fruit_name": (
            item.get("fruit_name")
            or ""
        ),
    }

    return (
        f"{base_url}?"
        f"{urlencode(params)}"
    )
