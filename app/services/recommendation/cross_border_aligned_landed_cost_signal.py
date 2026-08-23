from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.services.recommendation.cross_border_aligned_evaluation_readiness import (
    AlignedCrossBorderEvaluationReadiness,
    AlignedCrossBorderEvaluationState,
)
from app.services.recommendation.cross_border_landed_cost_signal import (
    CrossBorderLandedCostSignal,
    build_cross_border_landed_cost_signal,
)


class AlignedCrossBorderLandedCostSignalState(
    str,
    Enum,
):
    AVAILABLE = "available"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class AlignedCrossBorderLandedCostSignal:
    """
    Recommendation-side enforcement result for the landed-cost
    signal boundary after aligned evaluation readiness.

    AVAILABLE means downstream signal construction was authorized by
    C4J and delegated to the existing landed-cost signal authority.

    BLOCKED means C4J prohibited downstream consumption. In that
    state no landed-cost signal is built.

    AVAILABLE does not imply that the nested signal itself is
    AVAILABLE. Structural NOT_READY evidence remains the
    responsibility of the existing landed-cost signal authority and
    may therefore produce an UNAVAILABLE signal.

    This contract does not:

    - reevaluate alignment;
    - reevaluate structural readiness;
    - reconstruct canonical evidence;
    - calculate or recalculate landed cost;
    - reinterpret landed-cost advantage;
    - evaluate scoring readiness;
    - bind scoring input;
    - calculate or modify scores;
    - rank or recommend candidates;
    - select routes or execute transactions.
    """

    state: AlignedCrossBorderLandedCostSignalState
    evaluation: AlignedCrossBorderEvaluationReadiness
    signal: CrossBorderLandedCostSignal | None
    reasons: tuple[str, ...]

    @property
    def is_available(self) -> bool:
        return (
            self.state
            is AlignedCrossBorderLandedCostSignalState.AVAILABLE
        )


def build_aligned_cross_border_landed_cost_signal(
    evaluation: AlignedCrossBorderEvaluationReadiness,
) -> AlignedCrossBorderLandedCostSignal:
    """
    Enforce C4J before entering the existing landed-cost signal
    boundary.

    BLOCKED evaluations never invoke
    build_cross_border_landed_cost_signal().

    AVAILABLE evaluations delegate the exact gate evidence and the
    exact readiness object retained by C4J.
    """

    if (
        evaluation.state
        is not AlignedCrossBorderEvaluationState.AVAILABLE
    ):
        return AlignedCrossBorderLandedCostSignal(
            state=AlignedCrossBorderLandedCostSignalState.BLOCKED,
            evaluation=evaluation,
            signal=None,
            reasons=(
                "cross_border_evaluation_not_available",
            ),
        )

    if evaluation.readiness is None:
        raise ValueError(
            "available aligned evaluation must contain readiness"
        )

    signal = build_cross_border_landed_cost_signal(
        evidence=evaluation.gate.evidence,
        readiness=evaluation.readiness,
    )

    return AlignedCrossBorderLandedCostSignal(
        state=AlignedCrossBorderLandedCostSignalState.AVAILABLE,
        evaluation=evaluation,
        signal=signal,
        reasons=(),
    )
