from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.services.recommendation.cross_border_scoring_policy_activation_decision import (
    CrossBorderPolicyActivationDecision,
    CrossBorderPolicyActivationDecisionOutcome,
)


class CrossBorderActivationBoundaryState(
    str,
    Enum,
):
    ELIGIBLE = "eligible"
    FALLBACK = "fallback"


@dataclass(frozen=True)
class CrossBorderScoringActivationBoundary:
    """
    Fail-closed activation boundary for Cross-Border scoring.

    ELIGIBLE means only that the request may enter a later
    controlled binding stage.

    FALLBACK means existing production scoring must remain in use.

    This contract does not:
    - mutate scoring;
    - enable production policy behavior;
    - route traffic;
    - start rollout;
    - rank candidates;
    - produce recommendations;
    - execute transactions.
    """

    state: CrossBorderActivationBoundaryState

    baseline_policy_id: str
    candidate_policy_id: str

    activation_authority_id: str
    activation_authority_role: str

    authorization_ready: bool
    policy_identity_ready: bool
    authority_identity_ready: bool
    activation_state_safe: bool

    reasons: tuple[str, ...]


def evaluate_cross_border_scoring_activation_boundary(
    decision: CrossBorderPolicyActivationDecision,
) -> CrossBorderScoringActivationBoundary:
    """
    Evaluate whether an R1L activation decision is eligible to enter
    a later controlled production binding stage.

    Any invalid or incomplete state fails closed to FALLBACK.
    """

    baseline_policy_id = (
        decision.baseline_policy_id.strip()
    )

    candidate_policy_id = (
        decision.candidate_policy_id.strip()
    )

    activation_authority_id = (
        decision.activation_authority_id.strip()
    )

    activation_authority_role = (
        decision.activation_authority_role.strip()
    )

    authorization_ready = (
        decision.outcome
        is CrossBorderPolicyActivationDecisionOutcome.AUTHORIZE
        and decision.activation_readiness_confirmed is True
    )

    policy_identity_ready = (
        bool(baseline_policy_id)
        and bool(candidate_policy_id)
        and baseline_policy_id != candidate_policy_id
    )

    authority_identity_ready = (
        bool(activation_authority_id)
        and bool(activation_authority_role)
    )

    activation_state_safe = (
        decision.production_enabled is False
        and decision.rollout_started is False
        and decision.traffic_routed is False
    )

    checks = {
        "authorization": authorization_ready,
        "policy_identity": policy_identity_ready,
        "authority_identity": authority_identity_ready,
        "activation_state": activation_state_safe,
    }

    reasons = tuple(
        name
        for name, ready in checks.items()
        if not ready
    )

    state = (
        CrossBorderActivationBoundaryState.ELIGIBLE
        if not reasons
        else CrossBorderActivationBoundaryState.FALLBACK
    )

    return CrossBorderScoringActivationBoundary(
        state=state,
        baseline_policy_id=baseline_policy_id,
        candidate_policy_id=candidate_policy_id,
        activation_authority_id=activation_authority_id,
        activation_authority_role=activation_authority_role,
        authorization_ready=authorization_ready,
        policy_identity_ready=policy_identity_ready,
        authority_identity_ready=authority_identity_ready,
        activation_state_safe=activation_state_safe,
        reasons=reasons,
    )
