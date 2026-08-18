from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping


@dataclass(frozen=True)
class TrustObservation:
    """
    Canonical trust evidence observation.

    score:
        Trust evidence in the canonical [0, 100] range.

    available:
        Whether authoritative/acceptable trust evidence exists.

    source:
        Evidence source selected by the adapter.
    """

    score: float = 0.0
    available: bool = False
    source: str | None = None


def _safe_trust_score(
    value: Any,
) -> float | None:
    """
    Parse finite numeric trust evidence.

    Missing or invalid evidence remains unavailable.
    Observed zero is valid evidence.
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


def adapt_trust_evidence(
    item: Mapping[str, Any],
) -> TrustObservation:
    """
    Adapt existing trust-specific evidence into canonical trust.

    Precedence:
    1. explicit trust_score
    2. explicit platform_trust_score

    Explicitly excluded:
    - platform_boost_score
    - v7_platform_score
    - v8_platform_score
    - identity_score
    - popularity / reaction fields

    The adapter does not calculate trust from rating/review data.
    That would be a separate trust-production policy.
    """

    explicit = _safe_trust_score(
        item.get(
            "trust_score"
        )
    )

    if explicit is not None:
        return TrustObservation(
            score=explicit,
            available=True,
            source="trust_score",
        )

    platform_trust = _safe_trust_score(
        item.get(
            "platform_trust_score"
        )
    )

    if platform_trust is not None:
        return TrustObservation(
            score=platform_trust,
            available=True,
            source="platform_trust_score",
        )

    return TrustObservation()
