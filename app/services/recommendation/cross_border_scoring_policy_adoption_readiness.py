from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.services.recommendation.cross_border_scoring_policy_comparison import (
    CrossBorderPolicyComparisonState,
    CrossBorderScoringPolicyComparison,
)


class CrossBorderPolicyAdoptionReadinessState(
    str,
    Enum,
):
    READY = "ready"
    NOT_READY = "not_ready"


@dataclass(frozen=True)
class CrossBorderPolicyAdoptionReadiness:
    """
    Readiness evidence for a future policy-adoption review.

    READY means only that the R1H comparison result is structurally
    sufficient to enter a later adoption-decision process.

    This contract does not:
    - approve a policy;
    - select a policy;
    - adopt a policy;
    - activate a policy;
    - mutate production scoring;
    - change ranking;
    - produce a recommendation.
    """

    state: CrossBorderPolicyAdoptionReadinessState

    baseline_policy_id: str
    candidate_policy_id: str

    comparison_ready: bool
    policy_identity_ready: bool
    delta_evidence_ready: bool
    candidate_identity_ready: bool
    direction_ready: bool
    shadow_evidence_ready: bool
    policy_roles_ready: bool

    reasons: tuple[str, ...]


def evaluate_cross_border_policy_adoption_readiness(
    comparison: CrossBorderScoringPolicyComparison,
) -> CrossBorderPolicyAdoptionReadiness:
    """
    Determine whether an R1H policy comparison is structurally
    ready for a future adoption review.

    This function evaluates evidence sufficiency only.

    It does not interpret positive, zero, or negative delta values
    as proof that a candidate policy should be adopted.
    """

    comparison_ready = (
        comparison.state
        is CrossBorderPolicyComparisonState.COMPARABLE
    )

    baseline_policy_id = (
        comparison.baseline_policy_id.strip()
    )

    candidate_policy_id = (
        comparison.candidate_policy_id.strip()
    )

    policy_identity_ready = (
        bool(baseline_policy_id)
        and bool(candidate_policy_id)
        and baseline_policy_id != candidate_policy_id
    )

    delta_evidence_ready = (
        comparison.first_delta_difference is not None
        and comparison.second_delta_difference is not None
        and comparison.first_delta_difference.is_finite()
        and comparison.second_delta_difference.is_finite()
    )

    candidate_identity_ready = (
        comparison.candidate_identity_aligned is True
        and bool(comparison.first_candidate_ref)
        and bool(comparison.second_candidate_ref)
        and (
            comparison.first_candidate_ref
            != comparison.second_candidate_ref
        )
    )

    direction_ready = (
        comparison.direction_aligned is True
    )

    shadow_evidence_ready = (
        comparison.shadow_mode_aligned is True
    )

    policy_roles_ready = (
        comparison.policy_roles_valid is True
    )

    checks = {
        "comparison": comparison_ready,
        "policy_identity": policy_identity_ready,
        "delta_evidence": delta_evidence_ready,
        "candidate_identity": candidate_identity_ready,
        "direction": direction_ready,
        "shadow_evidence": shadow_evidence_ready,
        "policy_roles": policy_roles_ready,
    }

    reasons = tuple(
        name
        for name, ready in checks.items()
        if not ready
    )

    state = (
        CrossBorderPolicyAdoptionReadinessState.READY
        if not reasons
        else CrossBorderPolicyAdoptionReadinessState.NOT_READY
    )

    return CrossBorderPolicyAdoptionReadiness(
        state=state,
        baseline_policy_id=baseline_policy_id,
        candidate_policy_id=candidate_policy_id,
        comparison_ready=comparison_ready,
        policy_identity_ready=policy_identity_ready,
        delta_evidence_ready=delta_evidence_ready,
        candidate_identity_ready=candidate_identity_ready,
        direction_ready=direction_ready,
        shadow_evidence_ready=shadow_evidence_ready,
        policy_roles_ready=policy_roles_ready,
        reasons=reasons,
    )
