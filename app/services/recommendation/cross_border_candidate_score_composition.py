from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from app.services.recommendation.cross_border_candidate_component_alignment import (
    AlignedCrossBorderCandidateComponents,
)
from app.services.recommendation.models import (
    RecommendationPriority,
    RecommendationScoreComponents,
    RecommendationScoreResult,
)
from app.services.recommendation.scoring import (
    calculate_recommendation_score,
)


CandidateScoreFunction = Callable[
    [
        RecommendationScoreComponents,
        RecommendationPriority,
    ],
    RecommendationScoreResult,
]


@dataclass(frozen=True)
class PairwiseCrossBorderCandidateScores:
    """
    Independent canonical score results for the two already-aligned
    Cross-Border candidate component sets.

    Candidate references are preserved only as alignment provenance.

    This result does not:

    - compare scores;
    - choose a winner;
    - rank candidates;
    - select a recommendation;
    - evaluate activation authority;
    - route production traffic;
    - execute transactions.
    """

    first_candidate_ref: str
    second_candidate_ref: str
    first_score: RecommendationScoreResult
    second_score: RecommendationScoreResult


def compose_cross_border_candidate_scores(
    *,
    aligned_components: AlignedCrossBorderCandidateComponents,
    priority: RecommendationPriority,
    scorer: CandidateScoreFunction = calculate_recommendation_score,
) -> PairwiseCrossBorderCandidateScores:
    """
    Score each aligned Cross-Border candidate independently.

    The scoring function receives each candidate's own derived
    RecommendationScoreComponents and the same explicit recommendation
    priority.

    No pairwise comparison or winner decision is performed here.
    """

    first_score = scorer(
        aligned_components.first_components,
        priority,
    )

    second_score = scorer(
        aligned_components.second_components,
        priority,
    )

    if not isinstance(
        first_score,
        RecommendationScoreResult,
    ):
        raise TypeError(
            "first candidate scorer result must be RecommendationScoreResult"
        )

    if not isinstance(
        second_score,
        RecommendationScoreResult,
    ):
        raise TypeError(
            "second candidate scorer result must be RecommendationScoreResult"
        )

    return PairwiseCrossBorderCandidateScores(
        first_candidate_ref=(
            aligned_components.first_candidate_ref
        ),
        second_candidate_ref=(
            aligned_components.second_candidate_ref
        ),
        first_score=first_score,
        second_score=second_score,
    )
