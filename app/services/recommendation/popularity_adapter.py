from __future__ import annotations

import math
from typing import Any, Mapping


def _safe_popularity_score(
    value: Any,
) -> float | None:
    """
    Parse finite derived popularity evidence.

    Missing or invalid evidence remains unavailable.
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


def adapt_canonical_popularity(
    item: Mapping[str, Any],
) -> float | None:
    """
    Adapt existing derived popularity evidence.

    Precedence:
    1. popularity_score
    2. reaction_score

    Explicitly excluded from inline calculation:
    - click_count
    - ctr_pct
    - impression_count
    - review_count
    - rating
    - purchase_count
    - market_signal_score

    This adapter does not create popularity from raw behavioral,
    social-proof, trust, or market-adoption evidence.
    """

    popularity = _safe_popularity_score(
        item.get(
            "popularity_score"
        )
    )

    if popularity is not None:
        return popularity

    reaction = _safe_popularity_score(
        item.get(
            "reaction_score"
        )
    )

    if reaction is not None:
        return reaction

    return None
