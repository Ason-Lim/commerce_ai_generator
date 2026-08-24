from __future__ import annotations

from app.services.recommendation.cross_border_canonical_candidate_projection import (
    project_cross_border_ranked_candidate,
)
from app.services.recommendation.cross_border_canonical_result_projection import (
    project_cross_border_canonical_result,
)
from app.services.recommendation.cross_border_ranked_original_candidate import (
    CrossBorderRankedOriginalCandidatePair,
)
from app.services.recommendation.models import (
    RecommendationContext,
    RecommendationResult,
)


def compose_cross_border_canonical_result(
    *,
    context: RecommendationContext,
    ranked_pair: CrossBorderRankedOriginalCandidatePair,
) -> RecommendationResult:
    """
    Compose one already-ranked Cross-Border candidate pair into the
    canonical RecommendationResult contract.

    Composition order:

    1. preserve the canonical Cross-Border ranking order;
    2. project each ranked original candidate to RecommendationCandidate;
    3. project the ordered canonical candidates to RecommendationResult.

    This boundary delegates representation conversion to the already
    established candidate and result projection contracts.

    It does not:

    - calculate or modify candidate scores;
    - rerank candidates;
    - infer product identity from candidate_ref;
    - create winner-selection authority;
    - select a recommendation;
    - activate production policy;
    - route production traffic;
    - execute checkout, payment, purchase, or dispatch.
    """

    candidates = tuple(
        project_cross_border_ranked_candidate(candidate)
        for candidate in ranked_pair.ranked
    )

    return project_cross_border_canonical_result(
        context=context,
        candidates=candidates,
    )
