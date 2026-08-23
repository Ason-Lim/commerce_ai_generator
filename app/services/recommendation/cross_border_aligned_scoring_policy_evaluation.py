from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.services.recommendation.cross_border_aligned_scoring_binding import (
    AlignedCrossBorderScoringBinding,
    AlignedCrossBorderScoringBindingState,
)
from app.services.recommendation.cross_border_scoring_policy_evaluation import (
    CrossBorderScoringPolicy,
    CrossBorderScoringPolicyEvaluation,
    evaluate_cross_border_scoring_policy,
)


class AlignedCrossBorderScoringPolicyEvaluationState(
    str,
    Enum,
):
    AVAILABLE = "available"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class AlignedCrossBorderScoringPolicyEvaluation:
    """
    Recommendation-side enforcement result for scoring-policy
    evaluation after aligned scoring binding.

    AVAILABLE means C4P authorized downstream consumption and the
    exact bound scoring input was delegated to the existing
    shadow-policy evaluation authority.

    BLOCKED means C4P prohibited downstream policy evaluation.
    In that state no policy evaluation is produced.

    This contract does not:

    - rebuild or reinterpret scoring input;
    - reevaluate candidate alignment;
    - reevaluate scoring readiness;
    - duplicate scoring-policy evaluation rules;
    - compare policies;
    - approve or adopt policies;
    - activate production scoring;
    - mutate scoring;
    - rank or recommend candidates;
    - route traffic or execute transactions.
    """

    state: AlignedCrossBorderScoringPolicyEvaluationState
    aligned_binding: AlignedCrossBorderScoringBinding
    evaluation: CrossBorderScoringPolicyEvaluation | None
    reasons: tuple[str, ...]

    @property
    def is_available(self) -> bool:
        return (
            self.state
            is AlignedCrossBorderScoringPolicyEvaluationState.AVAILABLE
        )


def evaluate_aligned_cross_border_scoring_policy(
    *,
    aligned_binding: AlignedCrossBorderScoringBinding,
    policy: CrossBorderScoringPolicy,
) -> AlignedCrossBorderScoringPolicyEvaluation:
    """
    Enforce C4P authorization before entering the existing
    Cross-Border scoring-policy evaluation boundary.

    BLOCKED aligned bindings never invoke
    evaluate_cross_border_scoring_policy().

    AVAILABLE aligned bindings delegate the exact scoring input
    retained by C4P together with the supplied policy.
    """

    if (
        aligned_binding.state
        is not AlignedCrossBorderScoringBindingState.AVAILABLE
    ):
        return AlignedCrossBorderScoringPolicyEvaluation(
            state=(
                AlignedCrossBorderScoringPolicyEvaluationState.BLOCKED
            ),
            aligned_binding=aligned_binding,
            evaluation=None,
            reasons=(
                "cross_border_scoring_binding_not_available",
            ),
        )

    if aligned_binding.scoring_input is None:
        raise ValueError(
            "available aligned scoring binding must contain scoring input"
        )

    evaluation = evaluate_cross_border_scoring_policy(
        scoring_input=aligned_binding.scoring_input,
        policy=policy,
    )

    return AlignedCrossBorderScoringPolicyEvaluation(
        state=(
            AlignedCrossBorderScoringPolicyEvaluationState.AVAILABLE
        ),
        aligned_binding=aligned_binding,
        evaluation=evaluation,
        reasons=(),
    )
