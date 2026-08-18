from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any, TypeVar

from .models import RecommendationPriority


T = TypeVar("T")

ScoreAccessor = Callable[[T], Any]


def _safe_number(
    value: Any,
    default: float = 0.0,
) -> float:
    """
    Convert an already-selected ranking signal to float.

    Ranking does not discover or calculate signals.
    It only normalizes accessor output for ordering.
    """
    try:
        if value is None or value == "":
            return float(default)

        return float(value)

    except (TypeError, ValueError):
        return float(default)


def _price_sort_value(
    value: Any,
) -> float:
    """
    Preserve the current pipeline convention:
    missing / false-like price values sort after valid prices.
    """
    if not value:
        return 999999999.0

    return _safe_number(
        value,
        999999999.0,
    )


def rank_candidates(
    candidates: Iterable[T],
    priority: RecommendationPriority,
    *,
    final_score: ScoreAccessor,
    price: ScoreAccessor | None = None,
    quality_score: ScoreAccessor | None = None,
    trust_signal: ScoreAccessor | None = None,
) -> list[T]:
    """
    Pure canonical recommendation ordering.

    Responsibilities:
    - order already-scored candidates;
    - preserve current priority-specific sort semantics;
    - preserve Python stable ordering for complete ties.

    Non-responsibilities:
    - scoring;
    - score calculation;
    - candidate mutation;
    - rank-field mutation;
    - deduplication;
    - parsing;
    - Marketplace or Market Intelligence lookup;
    - personalization persistence;
    - explanation generation;
    - legacy alias normalization.

    Accessors intentionally isolate canonical ranking from legacy
    field names such as v7_* or v8_*.
    """

    items = list(candidates)

    if priority is RecommendationPriority.PRICE:
        if price is None:
            raise ValueError(
                "price accessor is required for PRICE ranking"
            )

        return sorted(
            items,
            key=lambda item: (
                _price_sort_value(
                    price(item)
                ),
                -_safe_number(
                    final_score(item)
                ),
            ),
        )

    if priority is RecommendationPriority.QUALITY:
        if quality_score is None:
            raise ValueError(
                "quality_score accessor is required for QUALITY ranking"
            )

        return sorted(
            items,
            key=lambda item: (
                _safe_number(
                    quality_score(item)
                ),
                _safe_number(
                    final_score(item)
                ),
            ),
            reverse=True,
        )

    if priority is RecommendationPriority.TRUST:
        if trust_signal is None:
            raise ValueError(
                "trust_signal accessor is required for TRUST ranking"
            )

        return sorted(
            items,
            key=lambda item: (
                _safe_number(
                    trust_signal(item)
                ),
                _safe_number(
                    final_score(item)
                ),
            ),
            reverse=True,
        )

    # MIX, EXPLORATION, DISCOVERY, and REVISIT currently share
    # the production default final-score ordering contract.
    return sorted(
        items,
        key=lambda item: _safe_number(
            final_score(item)
        ),
        reverse=True,
    )
