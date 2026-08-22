from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable

from app.services.recommendation.cross_border_scoring_policy_fallback import (
    CrossBorderScoringFallbackDecision,
    CrossBorderScoringFallbackTarget,
)
from app.services.recommendation.models import (
    RecommendationPriority,
    RecommendationScoreComponents,
    RecommendationScoreResult,
)
from app.services.recommendation.scoring import (
    calculate_recommendation_score,
)


class ControlledScoringPath(
    str,
    Enum,
):
    BASELINE = "baseline"
    CANDIDATE = "candidate"


@dataclass(frozen=True)
class ControlledScoringResult:
    """
    Result of the controlled production scoring boundary.

    This object records which scoring path produced the score.

    It does not rank candidates, select a recommendation,
    route traffic, start rollout, or execute transactions.
    """

    score: RecommendationScoreResult
    path: ControlledScoringPath
    fallback_applied: bool
    fallback_reason: str | None


CandidateScorer = Callable[
    [
        RecommendationScoreComponents,
        RecommendationPriority,
    ],
    RecommendationScoreResult,
]


def calculate_controlled_recommendation_score(
    components: RecommendationScoreComponents,
    priority: RecommendationPriority,
    *,
    fallback: CrossBorderScoringFallbackDecision | None = None,
    candidate_scorer: CandidateScorer | None = None,
) -> ControlledScoringResult:
    """
    Execute recommendation scoring through a fail-closed boundary.

    Baseline scoring remains authoritative when:

    - no Cross-Border fallback decision exists;
    - the fallback contract selects BASELINE;
    - candidate activation is not allowed;
    - no candidate scorer is supplied;
    - candidate scoring raises an exception;
    - candidate scoring returns an invalid result type.

    Only an explicitly authorized CANDIDATE decision together with
    a valid candidate scorer may produce the candidate path.

    This function does not perform ranking or recommendation
    selection.
    """

    def baseline(
        reason: str | None,
    ) -> ControlledScoringResult:
        score = calculate_recommendation_score(
            components,
            priority,
        )

        return ControlledScoringResult(
            score=score,
            path=ControlledScoringPath.BASELINE,
            fallback_applied=(
                fallback is not None
            ),
            fallback_reason=reason,
        )

    if fallback is None:
        return baseline(
            None
        )

    if (
        fallback.target
        is not CrossBorderScoringFallbackTarget.CANDIDATE
    ):
        return baseline(
            fallback.fallback_reason
            or "baseline_target"
        )

    if fallback.activation_allowed is not True:
        return baseline(
            "activation_not_allowed"
        )

    if fallback.fallback_required is True:
        return baseline(
            fallback.fallback_reason
            or "fallback_required"
        )

    if candidate_scorer is None:
        return baseline(
            "candidate_scorer_unavailable"
        )

    try:
        score = candidate_scorer(
            components,
            priority,
        )
    except Exception:
        return baseline(
            "candidate_scorer_error"
        )

    if not isinstance(
        score,
        RecommendationScoreResult,
    ):
        return baseline(
            "invalid_candidate_result"
        )

    return ControlledScoringResult(
        score=score,
        path=ControlledScoringPath.CANDIDATE,
        fallback_applied=False,
        fallback_reason=None,
    )
