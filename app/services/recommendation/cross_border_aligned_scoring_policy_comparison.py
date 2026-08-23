from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.services.recommendation.cross_border_aligned_scoring_policy_evaluation import (
    AlignedCrossBorderScoringPolicyEvaluation,
    AlignedCrossBorderScoringPolicyEvaluationState,
)
from app.services.recommendation.cross_border_scoring_policy_comparison import (
    CrossBorderScoringPolicyComparison,
    compare_cross_border_scoring_policies,
)


class AlignedCrossBorderScoringPolicyComparisonState(
    str,
    Enum,
):
    AVAILABLE = "available"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class AlignedCrossBorderScoringPolicyComparison:
    """
    Recommendation-side enforcement result for policy comparison
    after aligned scoring-policy evaluation.

    AVAILABLE means both aligned policy evaluations authorized
    downstream consumption and their exact nested canonical
    evaluations were delegated to the existing comparison authority.

    BLOCKED means at least one aligned policy evaluation prohibited
    downstream comparison.

    This contract does not:

    - reevaluate scoring-policy semantics;
    - duplicate policy-comparison rules;
    - infer policy roles;
    - approve or adopt policies;
    - evaluate adoption readiness;
    - activate production scoring;
    - mutate scoring;
    - rank or recommend candidates;
    - route traffic or execute transactions.
    """

    state: AlignedCrossBorderScoringPolicyComparisonState
    baseline: AlignedCrossBorderScoringPolicyEvaluation
    candidate: AlignedCrossBorderScoringPolicyEvaluation
    comparison: CrossBorderScoringPolicyComparison | None
    reasons: tuple[str, ...]

    @property
    def is_available(self) -> bool:
        return (
            self.state
            is AlignedCrossBorderScoringPolicyComparisonState.AVAILABLE
        )


def compare_aligned_cross_border_scoring_policies(
    *,
    baseline: AlignedCrossBorderScoringPolicyEvaluation,
    candidate: AlignedCrossBorderScoringPolicyEvaluation,
) -> AlignedCrossBorderScoringPolicyComparison:
    """
    Enforce C4R authorization before entering the existing
    Cross-Border policy-comparison boundary.

    If either aligned evaluation is BLOCKED, the canonical comparison
    authority is not invoked.

    If both are AVAILABLE, their exact nested canonical evaluations
    are delegated without modification or reinterpretation.
    """

    reasons: list[str] = []

    if (
        baseline.state
        is not AlignedCrossBorderScoringPolicyEvaluationState.AVAILABLE
    ):
        reasons.append(
            "baseline_policy_evaluation_not_available"
        )

    if (
        candidate.state
        is not AlignedCrossBorderScoringPolicyEvaluationState.AVAILABLE
    ):
        reasons.append(
            "candidate_policy_evaluation_not_available"
        )

    if reasons:
        return AlignedCrossBorderScoringPolicyComparison(
            state=AlignedCrossBorderScoringPolicyComparisonState.BLOCKED,
            baseline=baseline,
            candidate=candidate,
            comparison=None,
            reasons=tuple(reasons),
        )

    if baseline.evaluation is None:
        raise ValueError(
            "available aligned baseline policy evaluation "
            "must contain evaluation"
        )

    if candidate.evaluation is None:
        raise ValueError(
            "available aligned candidate policy evaluation "
            "must contain evaluation"
        )

    comparison = compare_cross_border_scoring_policies(
        baseline=baseline.evaluation,
        candidate=candidate.evaluation,
    )

    return AlignedCrossBorderScoringPolicyComparison(
        state=AlignedCrossBorderScoringPolicyComparisonState.AVAILABLE,
        baseline=baseline,
        candidate=candidate,
        comparison=comparison,
        reasons=(),
    )
