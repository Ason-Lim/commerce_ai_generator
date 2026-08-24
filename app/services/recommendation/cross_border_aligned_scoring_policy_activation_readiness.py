from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.services.recommendation.cross_border_aligned_scoring_policy_adoption_decision import (
    AlignedCrossBorderPolicyAdoptionDecision,
    AlignedCrossBorderPolicyAdoptionDecisionState,
)
from app.services.recommendation.cross_border_scoring_policy_activation_readiness import (
    CrossBorderPolicyActivationReadiness,
    evaluate_cross_border_policy_activation_readiness,
)


class AlignedCrossBorderPolicyActivationReadinessState(
    str,
    Enum,
):
    AVAILABLE = "available"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class AlignedCrossBorderPolicyActivationReadiness:
    """
    Recommendation-side provenance gate for canonical policy
    activation-readiness evaluation.

    AVAILABLE means a provenance-preserving aligned adoption decision
    was recorded and its exact canonical decision was evaluated by the
    existing canonical activation-readiness authority.

    AVAILABLE does not mean canonical activation readiness is READY.
    The nested canonical readiness owns READY / NOT_READY semantics.

    BLOCKED means no provenance-preserving canonical adoption decision
    was available for activation-readiness evaluation.

    This contract does not:

    - synthesize an adoption decision;
    - reinterpret ADOPT, HOLD, or REJECT;
    - duplicate canonical activation-readiness rules;
    - convert NOT_READY into BLOCKED;
    - authorize production activation;
    - make an activation decision;
    - deploy or activate a policy;
    - mutate scoring;
    - change ranking;
    - produce recommendations;
    - route traffic or execute transactions.
    """

    state: AlignedCrossBorderPolicyActivationReadinessState
    aligned_decision: AlignedCrossBorderPolicyAdoptionDecision
    readiness: CrossBorderPolicyActivationReadiness | None
    reasons: tuple[str, ...]

    @property
    def is_available(self) -> bool:
        return (
            self.state
            is AlignedCrossBorderPolicyActivationReadinessState.AVAILABLE
        )


def evaluate_aligned_cross_border_policy_activation_readiness(
    aligned_decision: AlignedCrossBorderPolicyAdoptionDecision,
) -> AlignedCrossBorderPolicyActivationReadiness:
    """
    Enforce aligned adoption-decision provenance before entering the
    canonical activation-readiness evaluator.

    BLOCKED aligned adoption decisions do not enter the canonical
    evaluator.

    RECORDED aligned adoption decisions delegate their exact nested
    canonical decision unchanged.

    Canonical READY / NOT_READY semantics remain owned by
    evaluate_cross_border_policy_activation_readiness().
    """

    if (
        aligned_decision.state
        is not AlignedCrossBorderPolicyAdoptionDecisionState.RECORDED
    ):
        return AlignedCrossBorderPolicyActivationReadiness(
            state=(
                AlignedCrossBorderPolicyActivationReadinessState.BLOCKED
            ),
            aligned_decision=aligned_decision,
            readiness=None,
            reasons=("aligned_adoption_decision_not_recorded",),
        )

    if aligned_decision.decision is None:
        raise ValueError(
            "recorded aligned adoption decision "
            "must contain canonical decision"
        )

    readiness = evaluate_cross_border_policy_activation_readiness(
        aligned_decision.decision
    )

    return AlignedCrossBorderPolicyActivationReadiness(
        state=(
            AlignedCrossBorderPolicyActivationReadinessState.AVAILABLE
        ),
        aligned_decision=aligned_decision,
        readiness=readiness,
        reasons=(),
    )
