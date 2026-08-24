from __future__ import annotations

from collections.abc import Callable

from app.services.recommendation.cross_border_aligned_controlled_scoring import (
    calculate_aligned_controlled_recommendation_score,
)
from app.services.recommendation.cross_border_aligned_scoring_policy_fallback import (
    AlignedCrossBorderScoringFallback,
    AlignedCrossBorderScoringFallbackState,
)
from app.services.recommendation.cross_border_controlled_scoring import (
    CandidateScorer,
)
from app.services.recommendation.models import (
    RecommendationPriority,
    RecommendationScoreComponents,
    RecommendationScoreResult,
)
from app.services.recommendation.scoring import (
    calculate_recommendation_score,
)


RuntimeScorer = Callable[
    [
        RecommendationScoreComponents,
        RecommendationPriority,
    ],
    RecommendationScoreResult,
]


def compose_aligned_cross_border_runtime_scorer(
    aligned_fallback: AlignedCrossBorderScoringFallback,
    *,
    candidate_scorer: CandidateScorer | None = None,
) -> RuntimeScorer:
    """
    Compose a Provider-compatible scorer from already-established
    aligned Cross-Border runtime authority.

    BLOCKED authority preserves the canonical baseline scorer directly.

    AVAILABLE authority delegates execution to the existing C5A
    aligned controlled-scoring boundary and adapts only its nested
    canonical score result to the Provider scorer contract.

    This composition boundary does not:
    - evaluate adoption;
    - evaluate activation readiness;
    - create activation authority;
    - reinterpret fallback decisions;
    - modify production routing.
    """

    if (
        aligned_fallback.state
        is AlignedCrossBorderScoringFallbackState.BLOCKED
    ):
        return calculate_recommendation_score

    def scorer(
        components: RecommendationScoreComponents,
        priority: RecommendationPriority,
    ) -> RecommendationScoreResult:
        aligned_result = (
            calculate_aligned_controlled_recommendation_score(
                components,
                priority,
                aligned_fallback=aligned_fallback,
                candidate_scorer=candidate_scorer,
            )
        )

        return aligned_result.controlled_result.score

    return scorer
