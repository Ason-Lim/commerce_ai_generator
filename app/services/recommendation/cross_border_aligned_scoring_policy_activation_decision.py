from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.services.recommendation.cross_border_aligned_scoring_policy_activation_readiness import (
    AlignedCrossBorderPolicyActivationReadiness,
    AlignedCrossBorderPolicyActivationReadinessState,
)
from app.services.recommendation.cross_border_scoring_policy_activation_decision import (
    CrossBorderPolicyActivationAuthority,
    CrossBorderPolicyActivationDecision,
    CrossBorderPolicyActivationDecisionOutcome,
    record_cross_border_policy_activation_decision,
)


class AlignedCrossBorderPolicyActivationDecisionState(
    str,
    Enum,
):
    RECORDED = "recorded"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class AlignedCrossBorderPolicyActivationDecision:
    """
    Recommendation-side provenance gate for canonical activation
    decision recording.

    RECORDED means the exact canonical activation readiness nested
    inside an AVAILABLE aligned readiness was passed unchanged to the
    existing canonical activation-decision recorder.

    BLOCKED means aligned activation readiness provenance was not
    available, so canonical activation-decision recording was not
    entered.

    RECORDED does not mean AUTHORIZE. The nested canonical decision
    owns AUTHORIZE / HOLD / DENY semantics.

    This contract does not:

    - synthesize activation readiness;
    - reinterpret canonical READY / NOT_READY;
    - choose or override AUTHORIZE, HOLD, or DENY;
    - create activation authority;
    - duplicate canonical activation-decision rules;
    - enable production scoring;
    - start rollout;
    - route traffic;
    - enter the activation boundary;
    - mutate scoring or ranking;
    - produce recommendations;
    - execute transactions.
    """

    state: AlignedCrossBorderPolicyActivationDecisionState
    aligned_readiness: AlignedCrossBorderPolicyActivationReadiness
    decision: CrossBorderPolicyActivationDecision | None
    reasons: tuple[str, ...]

    @property
    def is_recorded(self) -> bool:
        return (
            self.state
            is AlignedCrossBorderPolicyActivationDecisionState.RECORDED
        )


def record_aligned_cross_border_policy_activation_decision(
    *,
    aligned_readiness: AlignedCrossBorderPolicyActivationReadiness,
    authority: CrossBorderPolicyActivationAuthority,
    outcome: CrossBorderPolicyActivationDecisionOutcome,
    reason: str,
) -> AlignedCrossBorderPolicyActivationDecision:
    """
    Enforce aligned activation-readiness provenance before entering
    the canonical activation-decision recorder.

    BLOCKED aligned readiness does not enter the canonical recorder.

    AVAILABLE aligned readiness delegates its exact nested canonical
    readiness unchanged.

    Canonical READY / NOT_READY and AUTHORIZE / HOLD / DENY semantics
    remain owned by record_cross_border_policy_activation_decision().
    """

    if (
        aligned_readiness.state
        is not AlignedCrossBorderPolicyActivationReadinessState.AVAILABLE
    ):
        return AlignedCrossBorderPolicyActivationDecision(
            state=(
                AlignedCrossBorderPolicyActivationDecisionState.BLOCKED
            ),
            aligned_readiness=aligned_readiness,
            decision=None,
            reasons=("aligned_activation_readiness_not_available",),
        )

    if aligned_readiness.readiness is None:
        raise ValueError(
            "available aligned activation readiness "
            "must contain canonical readiness"
        )

    decision = record_cross_border_policy_activation_decision(
        readiness=aligned_readiness.readiness,
        authority=authority,
        outcome=outcome,
        reason=reason,
    )

    return AlignedCrossBorderPolicyActivationDecision(
        state=(
            AlignedCrossBorderPolicyActivationDecisionState.RECORDED
        ),
        aligned_readiness=aligned_readiness,
        decision=decision,
        reasons=(),
    )
