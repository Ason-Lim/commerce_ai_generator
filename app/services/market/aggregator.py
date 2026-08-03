from __future__ import annotations

from collections import Counter
from typing import Any, Dict, Iterable

from app.services.market.deduplicator import (
    deduplicate_market_items,
)
from app.services.market.normalizer import (
    normalize_market_items,
)


def aggregate_market_items(
    raw_items: Iterable[Dict[str, Any]],
    platform_hint: str | None = None,
) -> Dict[str, Any]:
    """
    Commerce AI V8 Market Aggregator

    Raw Items
        ↓
    Normalize
        ↓
    Deduplicate
        ↓
    Statistics
    """

    normalized_items = normalize_market_items(
        raw_items,
        platform_hint=platform_hint,
        preserve_raw=True,
    )

    grouped_items = deduplicate_market_items(
        normalized_items,
    )

    platform_counter = Counter(
        item.get("platform")
        for item in normalized_items
        if item.get("platform")
    )

    statistics = {
        "raw_item_count": len(list(raw_items))
        if not isinstance(raw_items, list)
        else len(raw_items),

        "normalized_item_count": len(
            normalized_items
        ),

        "group_count": len(
            grouped_items
        ),

        "platform_count": len(
            platform_counter
        ),

        "platform_distribution": dict(
            platform_counter
        ),
    }

    return {
        "normalized_items": normalized_items,
        "grouped_items": grouped_items,
        "statistics": statistics,
    }