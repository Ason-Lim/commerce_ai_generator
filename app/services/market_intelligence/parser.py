from __future__ import annotations

from typing import Any


def safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """
    Normalize an arbitrary numeric input to float.

    This helper performs input normalization only.
    """
    try:
        if value is None:
            return float(default)

        return float(value)

    except (TypeError, ValueError):
        return float(default)


def normalize_trend_direction(
    trend_direction: str | None,
) -> str:
    """
    Normalize a trend direction to up/down/flat.
    """
    normalized = str(
        trend_direction or "flat"
    ).strip().lower()

    direction_aliases = {
        "up": "up",
        "rise": "up",
        "rising": "up",
        "increase": "up",
        "increasing": "up",
        "상승": "up",

        "down": "down",
        "fall": "down",
        "falling": "down",
        "decrease": "down",
        "decreasing": "down",
        "하락": "down",

        "flat": "flat",
        "stable": "flat",
        "steady": "flat",
        "neutral": "flat",
        "unknown": "flat",
        "보합": "flat",
        "유지": "flat",
    }

    return direction_aliases.get(
        normalized,
        "flat",
    )


def normalize_search_interest(
    value: Any,
) -> float:
    """
    Normalize search interest to the legacy 0-100 range.
    """
    return max(
        0.0,
        min(
            safe_float(
                value,
                50.0,
            ),
            100.0,
        ),
    )
