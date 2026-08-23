from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.services.recommendation.cross_border_aligned_landed_cost_signal import (
    AlignedCrossBorderLandedCostSignal,
    AlignedCrossBorderLandedCostSignalState,
)
from app.services.recommendation.cross_border_scoring_readiness import (
    CrossBorderScoringReadiness,
    evaluate_cross_border_scoring_readiness,
)


class AlignedCrossBorderScoringReadinessState(
    str,
    Enum,
):
    AVAILABLE = "available"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class AlignedCrossBorderScoringReadiness:
    """
    Recommendation-side enforcement result for the scoring-readiness
    boundary after aligned landed-cost signal authorization.

    AVAILABLE means C4L authorized access to the existing
    scoring-readiness authority.

    BLOCKED means C4L prohibited downstream consumption. In that
    state scoring readiness is intentionally absent.

    AVAILABLE does not imply that the nested scoring-readiness result
    is READY. The existing scoring-readiness authority remains solely
    responsible for READY / NOT_READY semantics.

    This contract does not:

    - rebuild or reinterpret the landed-cost signal;
    - reevaluate alignment;
    - reevaluate structural evidence readiness;
    - duplicate scoring-readiness rules;
    - bind scoring input;
    - calculate or modify scores;
    - define scoring weights;
    - rank candidates;
    - select or recommend candidates;
    - select routes or execute transactions.
    """

    state: AlignedCrossBorderScoringReadinessState
    aligned_signal: AlignedCrossBorderLandedCostSignal
    readiness: CrossBorderScoringReadiness | None
    reasons: tuple[str, ...]

    @property
    def is_available(self) -> bool:
        return (
            self.state
            is AlignedCrossBorderScoringReadinessState.AVAILABLE
        )


def evaluate_aligned_cross_border_scoring_readiness(
    aligned_signal: AlignedCrossBorderLandedCostSignal,
) -> AlignedCrossBorderScoringReadiness:
    """
    Enforce C4L authorization before entering the existing
    Cross-Border scoring-readiness boundary.

    BLOCKED aligned signals never invoke
    evaluate_cross_border_scoring_readiness().

    AVAILABLE aligned signals delegate the exact nested signal
    retained by C4L without modifying or reinterpreting it.
    """

    if (
        aligned_signal.state
        is not AlignedCrossBorderLandedCostSignalState.AVAILABLE
    ):
        return AlignedCrossBorderScoringReadiness(
            state=AlignedCrossBorderScoringReadinessState.BLOCKED,
            aligned_signal=aligned_signal,
            readiness=None,
            reasons=(
                "cross_border_landed_cost_signal_not_available",
            ),
        )

    if aligned_signal.signal is None:
        raise ValueError(
            "available aligned landed-cost signal must contain signal"
        )

    readiness = evaluate_cross_border_scoring_readiness(
        aligned_signal.signal
    )

    return AlignedCrossBorderScoringReadiness(
        state=AlignedCrossBorderScoringReadinessState.AVAILABLE,
        aligned_signal=aligned_signal,
        readiness=readiness,
        reasons=(),
    )
