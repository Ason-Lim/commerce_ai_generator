from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.services.recommendation.cross_border_aligned_consumption_gate import (
    AlignedCrossBorderConsumptionGate,
    AlignedCrossBorderConsumptionState,
)
from app.services.recommendation.cross_border_evaluation_readiness import (
    CrossBorderEvaluationReadiness,
    evaluate_cross_border_readiness,
)


class AlignedCrossBorderEvaluationState(
    str,
    Enum,
):
    AVAILABLE = "available"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class AlignedCrossBorderEvaluationReadiness:
    """
    Recommendation-side enforcement result for the first downstream
    consumption boundary after C4G alignment.

    AVAILABLE means the C4G gate explicitly authorized consumption
    and the existing Cross-Border evaluation-readiness authority was
    invoked with the exact canonical evidence retained by that gate.

    BLOCKED means C4G rejected consumption. In that case readiness is
    intentionally absent; rejected alignment is not reinterpreted as
    structural NOT_READY evidence.

    This contract does not:

    - duplicate or reinterpret evaluation-readiness rules;
    - modify canonical evidence;
    - infer candidate or product identity;
    - build a landed-cost signal;
    - evaluate scoring readiness;
    - bind scoring input;
    - calculate or modify a score;
    - rank or recommend candidates;
    - select routes or execute transactions.
    """

    state: AlignedCrossBorderEvaluationState
    gate: AlignedCrossBorderConsumptionGate
    readiness: CrossBorderEvaluationReadiness | None
    reasons: tuple[str, ...]

    @property
    def is_available(self) -> bool:
        return (
            self.state
            is AlignedCrossBorderEvaluationState.AVAILABLE
        )


def evaluate_aligned_cross_border_readiness(
    gate: AlignedCrossBorderConsumptionGate,
) -> AlignedCrossBorderEvaluationReadiness:
    """
    Enforce C4G alignment before entering the existing structural
    evaluation-readiness boundary.

    REJECTED gates never invoke evaluate_cross_border_readiness().

    ALIGNED gates delegate the exact immutable gate.evidence object
    to the existing readiness authority without modifying or
    reinterpreting that authority.
    """

    if (
        gate.state
        is not AlignedCrossBorderConsumptionState.ALIGNED
    ):
        return AlignedCrossBorderEvaluationReadiness(
            state=AlignedCrossBorderEvaluationState.BLOCKED,
            gate=gate,
            readiness=None,
            reasons=(
                "cross_border_consumption_not_aligned",
            ),
        )

    readiness = evaluate_cross_border_readiness(
        gate.evidence
    )

    return AlignedCrossBorderEvaluationReadiness(
        state=AlignedCrossBorderEvaluationState.AVAILABLE,
        gate=gate,
        readiness=readiness,
        reasons=(),
    )
