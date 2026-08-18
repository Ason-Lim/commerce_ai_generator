from __future__ import annotations

import math
from typing import Any, Mapping


def _safe_identity_score(
    value: Any,
) -> float | None:
    """
    Parse finite identity evidence into canonical [0, 100].

    Missing or invalid evidence remains unavailable.
    Observed zero remains valid evidence.
    """

    if value is None or value == "":
        return None

    try:
        number = float(value)
    except (
        TypeError,
        ValueError,
    ):
        return None

    if not math.isfinite(number):
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


def adapt_canonical_identity(
    item: Mapping[str, Any],
) -> float | None:
    """
    Adapt existing identity evidence into canonical identity.

    Precedence:
    1. identity_score
    2. _identity_score
    3. _identity_validation["identity_score"]

    This adapter does not calculate identity and does not reinterpret
    trust, quality, cluster confidence, family confidence, or other
    cross-axis evidence as identity.
    """

    primary = _safe_identity_score(
        item.get(
            "identity_score"
        )
    )

    if primary is not None:
        return primary

    legacy = _safe_identity_score(
        item.get(
            "_identity_score"
        )
    )

    if legacy is not None:
        return legacy

    validation = item.get(
        "_identity_validation"
    )

    if isinstance(
        validation,
        Mapping,
    ):
        nested = _safe_identity_score(
            validation.get(
                "identity_score"
            )
        )

        if nested is not None:
            return nested

    return None
