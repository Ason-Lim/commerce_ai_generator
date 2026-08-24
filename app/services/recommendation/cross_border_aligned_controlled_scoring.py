from __future__ import annotations

from dataclasses import dataclass

from app.services.recommendation.cross_border_aligned_scoring_policy_fallback import (
    AlignedCrossBorderScoringFallback,
)
from app.services.recommendation.cross_border_controlled_scoring import (
    CandidateScorer,
    ControlledScoringResult,
    calculate_controlled_recommendation_score,
)
from app.services.recommendation.models import (
    RecommendationPriority,
    RecommendationScoreComponents,
)


@dataclass(frozen=True)
class AlignedControlledScoringResult:
    """
    Recommendation-side provenance-preserving result for controlled
    Cross-Border scoring.

    aligned_fallback preserves the complete aligned governance /
    fallback provenance entering scoring.

    controlled_result is the exact result produced by the existing
    canonical controlled-scoring authority.

    This contract does not:

    - reinterpret CANDIDATE / BASELINE fallback decisions;
    - synthesize a fallback decision when aligned fallback is BLOCKED;
    - reinterpret activation_allowed or fallback_required;
    - replace baseline scoring;
    - implement candidate scoring policy;
    - rank candidates;
    - select recommendations;
    - bind RecommendationProvider;
    - route traffic;
    - execute transactions.
    """

    aligned_fallback: AlignedCrossBorderScoringFallback
    controlled_result: ControlledScoringResult


def calculate_aligned_controlled_recommendation_score(
    components: RecommendationScoreComponents,
    priority: RecommendationPriority,
    *,
    aligned_fallback: AlignedCrossBorderScoringFallback,
    candidate_scorer: CandidateScorer | None = None,
) -> AlignedControlledScoringResult:
    """
    Preserve aligned fallback provenance while delegating scoring
    execution to the existing canonical controlled-scoring boundary.

    If the aligned fallback contains no canonical fallback decision,
    None is delegated unchanged. Canonical controlled scoring owns the
    resulting fail-closed baseline behavior.

    If a canonical fallback decision exists, the exact nested decision
    is delegated unchanged.

    Candidate / baseline path selection remains entirely owned by
    calculate_controlled_recommendation_score().
    """

    controlled_result = calculate_controlled_recommendation_score(
        components,
        priority,
        fallback=aligned_fallback.fallback,
        candidate_scorer=candidate_scorer,
    )

    return AlignedControlledScoringResult(
        aligned_fallback=aligned_fallback,
        controlled_result=controlled_result,
    )
