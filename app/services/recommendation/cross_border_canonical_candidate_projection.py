from __future__ import annotations

from app.services.recommendation.cross_border_ranked_original_candidate import (
    CrossBorderRankedOriginalCandidate,
)
from app.services.recommendation.models import (
    RecommendationCandidate,
)


def project_cross_border_ranked_candidate(
    candidate: CrossBorderRankedOriginalCandidate,
) -> RecommendationCandidate:
    """
    Project one already-ranked Cross-Border original candidate into the
    canonical RecommendationCandidate contract.

    This function does not score, rescore, rank, rerank, choose a winner,
    select a recommendation, activate production behavior, route traffic,
    or execute transactions.

    Canonical Recommendation ranking authority is preserved by mapping
    rank_position directly to RecommendationCandidate.rank.

    The existing RecommendationScoreResult object is reused unchanged.

    Cross-Border correlation and positional evidence remain bounded
    provenance inside candidate metadata.
    """

    return RecommendationCandidate(
        item=candidate.item,
        score=candidate.score,
        rank=candidate.rank_position,
        metadata={
            "cross_border": {
                "candidate_ref": candidate.candidate_ref,
                "candidate_position": candidate.candidate_position,
                "landed_cost": candidate.landed_cost,
            },
        },
    )
