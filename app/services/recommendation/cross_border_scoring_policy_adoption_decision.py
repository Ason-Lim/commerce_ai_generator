from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.services.recommendation.cross_border_scoring_policy_adoption_readiness import (
    CrossBorderPolicyAdoptionReadiness,
    CrossBorderPolicyAdoptionReadinessState,
)


class CrossBorderPolicyAdoptionDecisionOutcome(
    str,
    Enum,
):
    ADOPT = "adopt"
    HOLD = "hold"
    REJECT = "reject"


@dataclass(frozen=True)
class CrossBorderPolicyAdoptionAuthority:
    """
    Governance identity authorized to issue a policy-adoption
    decision record.

    Authority here permits decision recording only.

    It does not grant production activation, deployment, scoring
    mutation, ranking, recommendation, or transaction authority.
    """

    authority_id: str
    authority_role: str

    def __post_init__(self) -> None:
        authority_id = self.authority_id.strip()
        authority_role = self.authority_role.strip()

        if not authority_id:
            raise ValueError(
                "authority_id must not be blank"
            )

        if not authority_role:
            raise ValueError(
                "authority_role must not be blank"
            )

        object.__setattr__(
            self,
            "authority_id",
            authority_id,
        )

        object.__setattr__(
            self,
            "authority_role",
            authority_role,
        )


@dataclass(frozen=True)
class CrossBorderPolicyAdoptionDecision:
    """
    Canonical governance decision for one candidate scoring policy.

    ADOPT records an authorized adoption decision only.

    No production activation or score mutation occurs through this
    contract.
    """

    outcome: CrossBorderPolicyAdoptionDecisionOutcome

    baseline_policy_id: str
    candidate_policy_id: str

    authority_id: str
    authority_role: str

    readiness_confirmed: bool

    reason: str

    production_activation_authorized: bool = False


def record_cross_border_policy_adoption_decision(
    *,
    readiness: CrossBorderPolicyAdoptionReadiness,
    authority: CrossBorderPolicyAdoptionAuthority,
    outcome: CrossBorderPolicyAdoptionDecisionOutcome,
    reason: str,
) -> CrossBorderPolicyAdoptionDecision:
    """
    Record an explicit governance decision.

    ADOPT requires R1I READY evidence.

    HOLD and REJECT may be recorded regardless of readiness because
    governance may conservatively defer or reject a policy.

    This function never activates production scoring.
    """

    normalized_reason = reason.strip()

    if not normalized_reason:
        raise ValueError(
            "reason must not be blank"
        )

    readiness_confirmed = (
        readiness.state
        is CrossBorderPolicyAdoptionReadinessState.READY
    )

    if (
        outcome
        is CrossBorderPolicyAdoptionDecisionOutcome.ADOPT
        and not readiness_confirmed
    ):
        raise ValueError(
            "ADOPT requires adoption-ready evidence"
        )

    return CrossBorderPolicyAdoptionDecision(
        outcome=outcome,
        baseline_policy_id=(
            readiness.baseline_policy_id
        ),
        candidate_policy_id=(
            readiness.candidate_policy_id
        ),
        authority_id=authority.authority_id,
        authority_role=authority.authority_role,
        readiness_confirmed=readiness_confirmed,
        reason=normalized_reason,
        production_activation_authorized=False,
    )
