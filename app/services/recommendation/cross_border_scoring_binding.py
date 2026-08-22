from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from app.services.recommendation.cross_border_landed_cost_signal import (
    CrossBorderLandedCostAdvantage,
    CrossBorderLandedCostSignal,
)
from app.services.recommendation.cross_border_scoring_readiness import (
    CrossBorderScoringReadiness,
    CrossBorderScoringReadinessState,
)


class CrossBorderScoringDirection(
    str,
    Enum,
):
    FIRST = "first"
    SECOND = "second"
    EQUAL = "equal"


@dataclass(frozen=True)
class BoundCrossBorderScoringInput:
    """
    Recommendation-owned bounded scoring input derived from a
    scoring-ready Cross-Border landed-cost signal.

    This object binds evidence to the future scoring layer but does
    not itself calculate, mutate, or apply any score.

    Direction is observational evidence only and is not equivalent
    to scoring policy or recommendation preference.
    """

    first_candidate_ref: str
    second_candidate_ref: str

    first_landed_cost: Decimal
    second_landed_cost: Decimal

    currency: str

    direction: CrossBorderScoringDirection

    first_evidence_quality: str
    second_evidence_quality: str

    source_schema_id: str
    source_schema_version: str


def bind_cross_border_scoring_input(
    *,
    signal: CrossBorderLandedCostSignal,
    readiness: CrossBorderScoringReadiness,
) -> BoundCrossBorderScoringInput:
    """
    Bind an R1D signal into a Recommendation scoring input only when
    R1E declared the signal scoring-ready.

    No score, weight, rank, preference, selection, or recommendation
    is calculated or applied here.
    """

    if (
        readiness.state
        is not CrossBorderScoringReadinessState.READY
    ):
        raise ValueError(
            "cross-border signal is not scoring-ready"
        )

    direction_map = {
        CrossBorderLandedCostAdvantage.FIRST: (
            CrossBorderScoringDirection.FIRST
        ),
        CrossBorderLandedCostAdvantage.SECOND: (
            CrossBorderScoringDirection.SECOND
        ),
        CrossBorderLandedCostAdvantage.EQUAL: (
            CrossBorderScoringDirection.EQUAL
        ),
    }

    try:
        direction = direction_map[signal.advantage]
    except KeyError as exc:
        raise ValueError(
            "cross-border signal has no bindable scoring direction"
        ) from exc

    return BoundCrossBorderScoringInput(
        first_candidate_ref=signal.first_candidate_ref,
        second_candidate_ref=signal.second_candidate_ref,
        first_landed_cost=signal.first_landed_cost,
        second_landed_cost=signal.second_landed_cost,
        currency=signal.currency,
        direction=direction,
        first_evidence_quality=(
            signal.first_evidence_quality
        ),
        second_evidence_quality=(
            signal.second_evidence_quality
        ),
        source_schema_id=signal.source_schema_id,
        source_schema_version=(
            signal.source_schema_version
        ),
    )
