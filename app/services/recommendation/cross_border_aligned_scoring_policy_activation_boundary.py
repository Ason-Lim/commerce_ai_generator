from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.services.recommendation.cross_border_aligned_scoring_policy_activation_decision import (
    AlignedCrossBorderPolicyActivationDecision,
    AlignedCrossBorderPolicyActivationDecisionState,
)
from app.services.recommendation.cross_border_scoring_policy_activation_boundary import (
    CrossBorderScoringActivationBoundary,
    evaluate_cross_border_scoring_activation_boundary,
)


class AlignedCrossBorderPolicyActivationBoundaryState(
    str,
    Enum,
):
    AVAILABLE = "available"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class AlignedCrossBorderPolicyActivationBoundary:
    """
    Recommendation-side provenance entry contract for canonical
    Cross-Border scoring activation-boundary evaluation.

    AVAILABLE means an aligned activation decision was RECORDED and
    its exact nested canonical activation decision was evaluated by
    the existing canonical activation boundary.

    AVAILABLE does not mean the canonical boundary is ELIGIBLE.
    The nested canonical boundary owns ELIGIBLE / FALLBACK semantics.

    BLOCKED means no provenance-preserving canonical activation
    decision was available for boundary evaluation.

    BLOCKED does not mean canonical FALLBACK. No canonical boundary
    evaluation occurred in that state.

    This contract does not:

    - reinterpret AUTHORIZE / HOLD / DENY;
    - duplicate canonical ELIGIBLE / FALLBACK rules;
    - convert FALLBACK into BLOCKED;
    - convert BLOCKED into FALLBACK;
    - authorize production activation;
    - enable production scoring;
    - start rollout;
    - route traffic;
    - select a fallback target;
    - invoke controlled scoring;
    - mutate scoring or ranking;
    - produce recommendations;
    - execute transactions.
    """

    state: AlignedCrossBorderPolicyActivationBoundaryState
    aligned_decision: AlignedCrossBorderPolicyActivationDecision
    boundary: CrossBorderScoringActivationBoundary | None
    reasons: tuple[str, ...]

    @property
    def is_available(self) -> bool:
        return (
            self.state
            is AlignedCrossBorderPolicyActivationBoundaryState.AVAILABLE
        )


def evaluate_aligned_cross_border_policy_activation_boundary(
    aligned_decision: AlignedCrossBorderPolicyActivationDecision,
) -> AlignedCrossBorderPolicyActivationBoundary:
    """
    Enforce C4W aligned activation-decision provenance before entering
    the existing canonical activation boundary.

    BLOCKED aligned decisions do not invoke the canonical evaluator.

    RECORDED aligned decisions delegate their exact nested canonical
    decision unchanged.

    Canonical ELIGIBLE / FALLBACK semantics remain owned by
    evaluate_cross_border_scoring_activation_boundary().
    """

    if (
        aligned_decision.state
        is not AlignedCrossBorderPolicyActivationDecisionState.RECORDED
    ):
        return AlignedCrossBorderPolicyActivationBoundary(
            state=(
                AlignedCrossBorderPolicyActivationBoundaryState.BLOCKED
            ),
            aligned_decision=aligned_decision,
            boundary=None,
            reasons=("aligned_activation_decision_not_recorded",),
        )

    if aligned_decision.decision is None:
        raise ValueError(
            "recorded aligned activation decision "
            "must contain canonical decision"
        )

    boundary = evaluate_cross_border_scoring_activation_boundary(
        aligned_decision.decision
    )

    return AlignedCrossBorderPolicyActivationBoundary(
        state=(
            AlignedCrossBorderPolicyActivationBoundaryState.AVAILABLE
        ),
        aligned_decision=aligned_decision,
        boundary=boundary,
        reasons=(),
    )
