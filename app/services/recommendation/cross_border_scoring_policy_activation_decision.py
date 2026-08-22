from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.services.recommendation.cross_border_scoring_policy_activation_readiness import (
    CrossBorderPolicyActivationReadiness,
    CrossBorderPolicyActivationReadinessState,
)


class CrossBorderPolicyActivationDecisionOutcome(
    str,
    Enum,
):
    AUTHORIZE = "authorize"
    HOLD = "hold"
    DENY = "deny"


@dataclass(frozen=True)
class CrossBorderPolicyActivationAuthority:
    """
    Governance identity permitted to record a production activation
    decision.

    This authority may authorize entry into a later controlled
    activation process.

    It does not itself enable production scoring, deploy policy
    behavior, route traffic, mutate ranking, or execute transactions.
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
class CrossBorderPolicyActivationDecision:
    """
    Canonical governance decision for future production activation.

    AUTHORIZE means only that controlled activation may be considered
    in a later stage.

    It does not perform runtime activation.
    """

    outcome: CrossBorderPolicyActivationDecisionOutcome

    baseline_policy_id: str
    candidate_policy_id: str

    adoption_authority_id: str
    adoption_authority_role: str

    activation_authority_id: str
    activation_authority_role: str

    activation_readiness_confirmed: bool

    reason: str

    production_enabled: bool = False
    rollout_started: bool = False
    traffic_routed: bool = False


def record_cross_border_policy_activation_decision(
    *,
    readiness: CrossBorderPolicyActivationReadiness,
    authority: CrossBorderPolicyActivationAuthority,
    outcome: CrossBorderPolicyActivationDecisionOutcome,
    reason: str,
) -> CrossBorderPolicyActivationDecision:
    """
    Record an explicit production activation governance decision.

    AUTHORIZE requires R1K READY evidence.

    HOLD and DENY may be recorded regardless of readiness.

    No production enablement occurs here.
    """

    normalized_reason = reason.strip()

    if not normalized_reason:
        raise ValueError(
            "reason must not be blank"
        )

    activation_readiness_confirmed = (
        readiness.state
        is CrossBorderPolicyActivationReadinessState.READY
    )

    if (
        outcome
        is CrossBorderPolicyActivationDecisionOutcome.AUTHORIZE
        and not activation_readiness_confirmed
    ):
        raise ValueError(
            "AUTHORIZE requires activation-ready evidence"
        )

    return CrossBorderPolicyActivationDecision(
        outcome=outcome,
        baseline_policy_id=readiness.baseline_policy_id,
        candidate_policy_id=readiness.candidate_policy_id,
        adoption_authority_id=readiness.authority_id,
        adoption_authority_role=readiness.authority_role,
        activation_authority_id=authority.authority_id,
        activation_authority_role=authority.authority_role,
        activation_readiness_confirmed=(
            activation_readiness_confirmed
        ),
        reason=normalized_reason,
        production_enabled=False,
        rollout_started=False,
        traffic_routed=False,
    )
