from __future__ import annotations

from typing import Any

from .parser import (
    normalize_trend_direction,
    safe_float,
)


DEFAULT_MARKET_INTELLIGENCE: dict[str, Any] = {
    "market_score": 50.0,
    "market_stage": "stable",
    "market_signal": "📊 안정적인 관심",
    "market_message": "검색 관심도가 안정적인 수준을 유지하고 있어요.",
    "buy_timing": "천천히 비교해볼 시점",
    "buy_timing_message": (
        "급격한 시장 변화는 크지 않아 "
        "가격과 품질을 충분히 비교해도 좋아요."
    ),
    "search_interest": 50.0,
    "trend_direction": "flat",
}


def normalize_market_intelligence(
    value: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Preserve the current legacy Market Intelligence
    runtime payload contract.
    """
    normalized = dict(
        DEFAULT_MARKET_INTELLIGENCE
    )

    if isinstance(value, dict):
        normalized.update(
            {
                key: field_value
                for key, field_value in value.items()
                if field_value is not None
            }
        )

    normalized["market_score"] = round(
        max(
            0.0,
            min(
                safe_float(
                    normalized.get(
                        "market_score"
                    ),
                    50.0,
                ),
                100.0,
            ),
        ),
        2,
    )

    normalized["search_interest"] = round(
        max(
            0.0,
            min(
                safe_float(
                    normalized.get(
                        "search_interest"
                    ),
                    50.0,
                ),
                100.0,
            ),
        ),
        2,
    )

    normalized["trend_direction"] = (
        normalize_trend_direction(
            normalized.get(
                "trend_direction"
            )
        )
    )

    return normalized
