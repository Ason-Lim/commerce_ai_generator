from __future__ import annotations

import math
from typing import Any, Mapping


def _safe_market_score(
    value: Any,
) -> float | None:
    """
    Parse canonical market evidence.

    Missing, invalid, and non-finite evidence remains unavailable.
    Observed zero remains valid evidence.
    """

    if value is None or value == "":
        return None

    try:
        number = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):
        return None

    if not math.isfinite(
        number
    ):
        return None

    return round(
        max(
            0.0,
            min(
                100.0,
                number,
            ),
        ),
        1,
    )


def adapt_canonical_market(
    item: Mapping[str, Any],
) -> float | None:
    """
    Adapt canonical Market Intelligence evidence.

    Accepted:
    - market_score

    Explicitly excluded from direct adaptation:
    - trend_score
    - trend_direction
    - market_signal_score
    - market_signal_score_final
    - propagated_market_signal_score
    - market_stage
    - rating / review_count / purchase_count

    Market interpretation remains owned by 31_Market Intelligence.
    32_Recommendation Engine consumes the canonical market_score only.
    """

    return _safe_market_score(
        item.get(
            "market_score"
        )
    )
