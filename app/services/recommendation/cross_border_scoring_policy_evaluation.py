from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from app.services.recommendation.cross_border_scoring_binding import (
    BoundCrossBorderScoringInput,
    CrossBorderScoringDirection,
)


class CrossBorderScoringPolicyKind(
    str,
    Enum,
):
    BASELINE = "baseline"
    CANDIDATE = "candidate"


@dataclass(frozen=True)
class CrossBorderScoringPolicy:
    """
    Shadow-only policy definition for Cross-Border scoring research.

    The policy does not mutate production scoring and does not own
    ranking or recommendation authority.
    """

    policy_id: str
    kind: CrossBorderScoringPolicyKind
    directional_delta: Decimal

    def __post_init__(self) -> None:
        policy_id = self.policy_id.strip()

        if not policy_id:
            raise ValueError(
                "policy_id must not be blank"
            )

        directional_delta = Decimal(
            str(self.directional_delta)
        )

        if directional_delta < 0:
            raise ValueError(
                "directional_delta must be non-negative"
            )

        object.__setattr__(
            self,
            "policy_id",
            policy_id,
        )
        object.__setattr__(
            self,
            "directional_delta",
            directional_delta,
        )


@dataclass(frozen=True)
class CrossBorderScoringPolicyEvaluation:
    """
    Shadow evaluation result for one policy and one bound scoring
    input.

    first_delta and second_delta are hypothetical policy effects
    only. They are never applied to production scoring here.
    """

    policy_id: str
    policy_kind: CrossBorderScoringPolicyKind

    first_candidate_ref: str
    second_candidate_ref: str

    first_delta: Decimal
    second_delta: Decimal

    direction: CrossBorderScoringDirection
    shadow_only: bool


def evaluate_cross_border_scoring_policy(
    *,
    scoring_input: BoundCrossBorderScoringInput,
    policy: CrossBorderScoringPolicy,
) -> CrossBorderScoringPolicyEvaluation:
    """
    Evaluate hypothetical scoring deltas without mutating any
    production score, ranking, or recommendation result.
    """

    zero = Decimal("0")

    if (
        policy.kind
        is CrossBorderScoringPolicyKind.BASELINE
    ):
        first_delta = zero
        second_delta = zero

    elif (
        scoring_input.direction
        is CrossBorderScoringDirection.FIRST
    ):
        first_delta = policy.directional_delta
        second_delta = zero

    elif (
        scoring_input.direction
        is CrossBorderScoringDirection.SECOND
    ):
        first_delta = zero
        second_delta = policy.directional_delta

    else:
        first_delta = zero
        second_delta = zero

    return CrossBorderScoringPolicyEvaluation(
        policy_id=policy.policy_id,
        policy_kind=policy.kind,
        first_candidate_ref=(
            scoring_input.first_candidate_ref
        ),
        second_candidate_ref=(
            scoring_input.second_candidate_ref
        ),
        first_delta=first_delta,
        second_delta=second_delta,
        direction=scoring_input.direction,
        shadow_only=True,
    )
