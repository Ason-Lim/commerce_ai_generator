from __future__ import annotations

from typing import Any

from .parser import (
    normalize_search_interest,
    normalize_trend_direction,
)
from .rules import (
    build_buy_timing,
    build_market_signal,
    classify_market_stage,
)
from .scoring import calculate_market_score


def build_market_intelligence(
    search_interest: Any,
    trend_direction: str | None = "flat",
) -> dict[str, Any]:
    """
    Orchestrate the canonical Market Intelligence flow
    while preserving existing runtime behavior.
    """
    normalized_interest = normalize_search_interest(
        search_interest
    )

    normalized_direction = normalize_trend_direction(
        trend_direction
    )

    market_score = calculate_market_score(
        trend_score=normalized_interest,
        trend_direction=normalized_direction,
    )

    market_stage = classify_market_stage(
        market_score=market_score,
        trend_direction=normalized_direction,
    )

    market_signal, market_message = build_market_signal(
        market_stage
    )

    buy_timing, buy_timing_message = build_buy_timing(
        market_stage
    )

    return {
        "market_score": market_score,
        "market_stage": market_stage,
        "market_signal": market_signal,
        "market_message": market_message,
        "buy_timing": buy_timing,
        "buy_timing_message": buy_timing_message,
        "search_interest": round(
            normalized_interest,
            2,
        ),
        "trend_direction": normalized_direction,
    }
