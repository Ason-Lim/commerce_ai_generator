from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.services.recommendation.cross_border_aligned_scoring_policy_adoption_readiness import (
    AlignedCrossBorderPolicyAdoptionReadiness,
    AlignedCrossBorderPolicyAdoptionReadinessState,
)
from app.services.recommendation.cross_border_scoring_policy_adoption_decision import (
    CrossBorderPolicyAdoptionAuthority,
    CrossBorderPolicyAdoptionDecision,
    CrossBorderPolicyAdoptionDecisionOutcome,
    record_cross_border_policy_adoption_decision,
)


class AlignedCrossBorderPolicyAdoptionDecisionState(
    str,
    Enum,
):
    RECORDED = "recorded"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class AlignedCrossBorderPolicyAdoptionDecision:
    """
    Recommendation-side entry-enforcement result for an explicit
    policy-adoption governance decision.

    RECORDED means aligned readiness provenance was available and the
    exact canonical readiness plus the caller-supplied governance
    authority, requested outcome, and reason were delegated to the
    existing canonical adoption-decision authority.

    BLOCKED means aligned readiness provenance was unavailable. In
    that state no canonical adoption decision is recorded.

    This contract deliberately separates provenance enforcement from
    governance decision authority.

    It does not:

    - choose ADOPT, HOLD, or REJECT;
    - synthesize adoption readiness;
    - reinterpret READY or NOT_READY;
    - duplicate the canonical ADOPT-readiness rule;
    - create a fallback governance outcome;
    - authorize production activation;
    - deploy or activate a policy;
    - mutate scoring;
    - change ranking;
    - produce a recommendation;
    - route traffic or execute transactions.
    """

    state: AlignedCrossBorderPolicyAdoptionDecisionState
    aligned_readiness: AlignedCrossBorderPolicyAdoptionReadiness
    decision: CrossBorderPolicyAdoptionDecision | None
    reasons: tuple[str, ...]

    @property
    def is_recorded(self) -> bool:
        return (
            self.state
            is AlignedCrossBorderPolicyAdoptionDecisionState.RECORDED
        )


def record_aligned_cross_border_policy_adoption_decision(
    *,
    aligned_readiness: AlignedCrossBorderPolicyAdoptionReadiness,
    authority: CrossBorderPolicyAdoptionAuthority,
    outcome: CrossBorderPolicyAdoptionDecisionOutcome,
    reason: str,
) -> AlignedCrossBorderPolicyAdoptionDecision:
    """
    Enforce aligned readiness provenance before entering the
    canonical policy-adoption decision authority.

    If aligned readiness is BLOCKED, the canonical decision authority
    is not invoked and no governance outcome is synthesized.

    If aligned readiness is AVAILABLE, the exact nested canonical
    readiness and all explicit governance inputs are delegated
    unchanged.

    All ADOPT / HOLD / REJECT semantics remain owned by
    record_cross_border_policy_adoption_decision().
    """

    if (
        aligned_readiness.state
        is not AlignedCrossBorderPolicyAdoptionReadinessState.AVAILABLE
    ):
        return AlignedCrossBorderPolicyAdoptionDecision(
            state=AlignedCrossBorderPolicyAdoptionDecisionState.BLOCKED,
            aligned_readiness=aligned_readiness,
            decision=None,
            reasons=("aligned_adoption_readiness_not_available",),
        )

    if aligned_readiness.readiness is None:
        raise ValueError(
            "available aligned adoption readiness "
            "must contain canonical readiness"
        )

    decision = record_cross_border_policy_adoption_decision(
        readiness=aligned_readiness.readiness,
        authority=authority,
        outcome=outcome,
        reason=reason,
    )

    return AlignedCrossBorderPolicyAdoptionDecision(
        state=AlignedCrossBorderPolicyAdoptionDecisionState.RECORDED,
        aligned_readiness=aligned_readiness,
        decision=decision,
        reasons=(),
    )
