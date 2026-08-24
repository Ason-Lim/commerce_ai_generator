from __future__ import annotations

from app.services.recommendation.cross_border_aligned_scoring_runtime_authority_source import (
    RuntimeAuthoritySource,
    RuntimeAuthoritySourceState,
)
from app.services.recommendation.cross_border_aligned_scoring_runtime_composition import (
    compose_aligned_cross_border_runtime_scorer,
)
from app.services.recommendation.cross_border_controlled_scoring import (
    CandidateScorer,
)
from app.services.recommendation.provider import (
    RecommendationProvider,
)


def compose_production_recommendation_provider(
    authority_source: RuntimeAuthoritySource | None = None,
    *,
    candidate_scorer: CandidateScorer | None = None,
) -> RecommendationProvider:
    """
    Compose the production RecommendationProvider without creating,
    discovering, or re-evaluating runtime authority.

    Missing or BLOCKED runtime authority preserves the existing
    canonical RecommendationProvider construction directly.

    AVAILABLE runtime authority delegates scorer composition to the
    already-established aligned Cross-Border runtime composition
    boundary.

    This boundary does not:

    - create adoption or activation authority;
    - load authority from request, environment, file, or database;
    - reinterpret fallback decisions;
    - create a candidate scorer;
    - authorize candidate scoring;
    - start rollout;
    - route traffic;
    - change public API contracts.
    """

    if (
        authority_source is None
        or authority_source.state
        is RuntimeAuthoritySourceState.BLOCKED
        or authority_source.authority is None
    ):
        return RecommendationProvider()

    scorer = compose_aligned_cross_border_runtime_scorer(
        authority_source.authority,
        candidate_scorer=candidate_scorer,
    )

    return RecommendationProvider(
        scorer=scorer,
    )
