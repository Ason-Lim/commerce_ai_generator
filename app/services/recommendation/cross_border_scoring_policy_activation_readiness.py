from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.services.recommendation.cross_border_scoring_policy_adoption_decision import (
    CrossBorderPolicyAdoptionDecision,
    CrossBorderPolicyAdoptionDecisionOutcome,
)


class CrossBorderPolicyActivationReadinessState(
    str,
    Enum,
):
    READY = "ready"
    NOT_READY = "not_ready"


@dataclass(frozen=True)
class CrossBorderPolicyActivationReadiness:
    """
    Evidence that an adopted Cross-Border scoring policy is
    structurally ready to enter a later production activation
    process.

    READY does not activate production scoring.

    This contract does not:
    - mutate scoring;
    - enable a policy;
    - deploy a policy;
    - route traffic;
    - change ranking;
    - produce recommendations;
    - execute transactions.
    """

    state: CrossBorderPolicyActivationReadinessState

    baseline_policy_id: str
    candidate_policy_id: str

    authority_id: str
    authority_role: str

    adoption_decision_ready: bool
    readiness_evidence_ready: bool
    policy_identity_ready: bool
    authority_identity_ready: bool
    activation_boundary_ready: bool

    reasons: tuple[str, ...]


def evaluate_cross_border_policy_activation_readiness(
    decision: CrossBorderPolicyAdoptionDecision,
) -> CrossBorderPolicyActivationReadiness:
    """
    Determine whether an R1J adoption decision is structurally
    sufficient to enter a future production activation stage.

    No production activation occurs here.
    """

    baseline_policy_id = (
        decision.baseline_policy_id.strip()
    )

    candidate_policy_id = (
        decision.candidate_policy_id.strip()
    )

    authority_id = (
        decision.authority_id.strip()
    )

    authority_role = (
        decision.authority_role.strip()
    )

    adoption_decision_ready = (
        decision.outcome
        is CrossBorderPolicyAdoptionDecisionOutcome.ADOPT
    )

    readiness_evidence_ready = (
        decision.readiness_confirmed is True
    )

    policy_identity_ready = (
        bool(baseline_policy_id)
        and bool(candidate_policy_id)
        and baseline_policy_id != candidate_policy_id
    )

    authority_identity_ready = (
        bool(authority_id)
        and bool(authority_role)
    )

    activation_boundary_ready = (
        decision.production_activation_authorized
        is False
    )

    checks = {
        "adoption_decision": adoption_decision_ready,
        "readiness_evidence": readiness_evidence_ready,
        "policy_identity": policy_identity_ready,
        "authority_identity": authority_identity_ready,
        "activation_boundary": activation_boundary_ready,
    }

    reasons = tuple(
        name
        for name, ready in checks.items()
        if not ready
    )

    state = (
        CrossBorderPolicyActivationReadinessState.READY
        if not reasons
        else CrossBorderPolicyActivationReadinessState.NOT_READY
    )

    return CrossBorderPolicyActivationReadiness(
        state=state,
        baseline_policy_id=baseline_policy_id,
        candidate_policy_id=candidate_policy_id,
        authority_id=authority_id,
        authority_role=authority_role,
        adoption_decision_ready=adoption_decision_ready,
        readiness_evidence_ready=readiness_evidence_ready,
        policy_identity_ready=policy_identity_ready,
        authority_identity_ready=authority_identity_ready,
        activation_boundary_ready=activation_boundary_ready,
        reasons=reasons,
    )
