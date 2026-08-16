from __future__ import annotations

from typing import Any

from .parser import (
    normalize_trend_direction,
    safe_float,
)


def calculate_market_score(
    trend_score: Any,
    trend_direction: str | None = "flat",
) -> float:
    """
    Calculate the legacy market score on a 0-100 scale.
    """
    search_interest = max(
        0.0,
        min(
            safe_float(
                trend_score,
                50.0,
            ),
            100.0,
        ),
    )

    direction = normalize_trend_direction(
        trend_direction
    )

    direction_adjustment = {
        "up": 10.0,
        "flat": 3.0,
        "down": -10.0,
    }.get(
        direction,
        0.0,
    )

    market_score = (
        search_interest
        + direction_adjustment
    )

    return round(
        max(
            0.0,
            min(
                market_score,
                100.0,
            ),
        ),
        2,
    )
