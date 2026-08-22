from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from app.services.recommendation.cross_border_scoring_policy_evaluation import (
    CrossBorderScoringPolicyEvaluation,
    CrossBorderScoringPolicyKind,
)


class CrossBorderPolicyComparisonState(
    str,
    Enum,
):
    COMPARABLE = "comparable"
    NOT_COMPARABLE = "not_comparable"


@dataclass(frozen=True)
class CrossBorderScoringPolicyComparison:
    """
    Shadow-only comparison between one baseline policy evaluation
    and one candidate policy evaluation.

    Comparison observes evaluation differences only.

    It does not select a policy, adopt a policy, mutate production
    scoring, rank candidates, or produce a recommendation.
    """

    state: CrossBorderPolicyComparisonState

    baseline_policy_id: str
    candidate_policy_id: str

    first_candidate_ref: str
    second_candidate_ref: str

    first_delta_difference: Decimal | None
    second_delta_difference: Decimal | None

    candidate_identity_aligned: bool
    direction_aligned: bool
    shadow_mode_aligned: bool
    policy_roles_valid: bool

    reasons: tuple[str, ...]


def compare_cross_border_scoring_policies(
    *,
    baseline: CrossBorderScoringPolicyEvaluation,
    candidate: CrossBorderScoringPolicyEvaluation,
) -> CrossBorderScoringPolicyComparison:
    """
    Compare baseline and candidate shadow-policy evaluations.

    Delta differences are exposed only when both evaluations are
    structurally comparable.

    No production scoring or policy adoption authority exists here.
    """

    candidate_identity_aligned = (
        baseline.first_candidate_ref
        == candidate.first_candidate_ref
        and baseline.second_candidate_ref
        == candidate.second_candidate_ref
    )

    direction_aligned = (
        baseline.direction
        is candidate.direction
    )

    shadow_mode_aligned = (
        baseline.shadow_only is True
        and candidate.shadow_only is True
    )

    policy_roles_valid = (
        baseline.policy_kind
        is CrossBorderScoringPolicyKind.BASELINE
        and candidate.policy_kind
        is CrossBorderScoringPolicyKind.CANDIDATE
    )

    checks = {
        "candidate_identity": candidate_identity_aligned,
        "direction": direction_aligned,
        "shadow_mode": shadow_mode_aligned,
        "policy_roles": policy_roles_valid,
    }

    reasons = tuple(
        name
        for name, valid in checks.items()
        if not valid
    )

    if reasons:
        state = (
            CrossBorderPolicyComparisonState.NOT_COMPARABLE
        )

        first_delta_difference = None
        second_delta_difference = None

    else:
        state = (
            CrossBorderPolicyComparisonState.COMPARABLE
        )

        first_delta_difference = (
            candidate.first_delta
            - baseline.first_delta
        )

        second_delta_difference = (
            candidate.second_delta
            - baseline.second_delta
        )

    return CrossBorderScoringPolicyComparison(
        state=state,
        baseline_policy_id=baseline.policy_id,
        candidate_policy_id=candidate.policy_id,
        first_candidate_ref=baseline.first_candidate_ref,
        second_candidate_ref=baseline.second_candidate_ref,
        first_delta_difference=first_delta_difference,
        second_delta_difference=second_delta_difference,
        candidate_identity_aligned=(
            candidate_identity_aligned
        ),
        direction_aligned=direction_aligned,
        shadow_mode_aligned=shadow_mode_aligned,
        policy_roles_valid=policy_roles_valid,
        reasons=reasons,
    )
