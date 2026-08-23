from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.services.recommendation.cross_border_aligned_scoring_policy_comparison import (
    AlignedCrossBorderScoringPolicyComparison,
    AlignedCrossBorderScoringPolicyComparisonState,
)
from app.services.recommendation.cross_border_scoring_policy_adoption_readiness import (
    CrossBorderPolicyAdoptionReadiness,
    evaluate_cross_border_policy_adoption_readiness,
)


class AlignedCrossBorderPolicyAdoptionReadinessState(
    str,
    Enum,
):
    AVAILABLE = "available"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class AlignedCrossBorderPolicyAdoptionReadiness:
    """
    Recommendation-side enforcement result for policy-adoption
    readiness after aligned scoring-policy comparison.

    AVAILABLE means the aligned comparison authorized downstream
    consumption and its exact nested canonical comparison was
    delegated to the existing adoption-readiness authority.

    BLOCKED means the aligned comparison prohibited downstream
    adoption-readiness evaluation.

    This contract does not:

    - compare scoring policies;
    - reinterpret comparison semantics;
    - approve a policy;
    - select a policy;
    - adopt a policy;
    - activate production scoring;
    - mutate scoring;
    - rank or recommend candidates;
    - route traffic or execute transactions.
    """

    state: AlignedCrossBorderPolicyAdoptionReadinessState
    aligned_comparison: AlignedCrossBorderScoringPolicyComparison
    readiness: CrossBorderPolicyAdoptionReadiness | None
    reasons: tuple[str, ...]

    @property
    def is_available(self) -> bool:
        return (
            self.state
            is AlignedCrossBorderPolicyAdoptionReadinessState.AVAILABLE
        )


def evaluate_aligned_cross_border_policy_adoption_readiness(
    aligned_comparison: AlignedCrossBorderScoringPolicyComparison,
) -> AlignedCrossBorderPolicyAdoptionReadiness:
    """
    Enforce C4S authorization before entering the existing
    Cross-Border policy-adoption-readiness boundary.

    If the aligned comparison is BLOCKED, the canonical
    adoption-readiness authority is not invoked.

    If it is AVAILABLE, its exact nested canonical comparison is
    delegated without modification or reinterpretation.
    """

    if (
        aligned_comparison.state
        is not AlignedCrossBorderScoringPolicyComparisonState.AVAILABLE
    ):
        return AlignedCrossBorderPolicyAdoptionReadiness(
            state=AlignedCrossBorderPolicyAdoptionReadinessState.BLOCKED,
            aligned_comparison=aligned_comparison,
            readiness=None,
            reasons=("aligned_policy_comparison_not_available",),
        )

    if aligned_comparison.comparison is None:
        raise ValueError(
            "available aligned policy comparison "
            "must contain comparison"
        )

    readiness = evaluate_cross_border_policy_adoption_readiness(
        aligned_comparison.comparison
    )

    return AlignedCrossBorderPolicyAdoptionReadiness(
        state=AlignedCrossBorderPolicyAdoptionReadinessState.AVAILABLE,
        aligned_comparison=aligned_comparison,
        readiness=readiness,
        reasons=(),
    )
