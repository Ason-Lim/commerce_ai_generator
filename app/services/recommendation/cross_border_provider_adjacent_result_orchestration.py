from __future__ import annotations

from collections.abc import Sequence

from app.services.recommendation.cross_border_bound_price_signal_composition import (
    BoundCrossBorderPriceSignals,
)
from app.services.recommendation.cross_border_candidate_component_alignment import (
    AlignedCrossBorderCandidateComponents,
)
from app.services.recommendation.cross_border_candidate_ranking import (
    rank_cross_border_candidate_pair,
)
from app.services.recommendation.cross_border_candidate_reference_binding_set import (
    CrossBorderCandidateReferenceBindingSet,
)
from app.services.recommendation.cross_border_candidate_score_composition import (
    PairwiseCrossBorderCandidateScores,
)
from app.services.recommendation.cross_border_canonical_result_composition import (
    compose_cross_border_canonical_result,
)
from app.services.recommendation.cross_border_original_candidate_binding_set import (
    bind_cross_border_original_candidate_set,
)
from app.services.recommendation.cross_border_ranked_original_candidate import (
    reconcile_cross_border_ranked_original_candidates,
)
from app.services.recommendation.models import (
    RecommendationCandidate,
    RecommendationContext,
    RecommendationResult,
)


def compose_cross_border_provider_adjacent_result(
    *,
    context: RecommendationContext,
    reference_binding_set: CrossBorderCandidateReferenceBindingSet,
    candidates: Sequence[RecommendationCandidate],
    scores: PairwiseCrossBorderCandidateScores,
    price_signals: BoundCrossBorderPriceSignals,
    aligned_components: AlignedCrossBorderCandidateComponents,
) -> RecommendationResult:
    """
    Compose already-established Cross-Border Recommendation surfaces
    into one canonical RecommendationResult beside, but not inside,
    the production RecommendationProvider.

    Canonical authority flow:

    - RecommendationContext owns priority;
    - candidate_position owns original-item positional binding;
    - canonical Cross-Border ranking owns rank order;
    - candidate_ref correlates established Cross-Border surfaces;
    - canonical result composition owns representation projection.

    This orchestration boundary does not:

    - accept or validate raw Cross-Border handoff contracts;
    - derive landed-cost evidence;
    - calculate aligned components;
    - calculate candidate scores;
    - define or reinterpret priority;
    - define a new ranking policy;
    - infer product identity from candidate_ref;
    - create winner-selection authority;
    - select a recommendation;
    - modify RecommendationProvider;
    - activate production routing;
    - execute transactions.
    """

    original_bindings = (
        bind_cross_border_original_candidate_set(
            reference_binding_set=reference_binding_set,
            candidates=candidates,
        )
    )

    ranked_candidates = (
        rank_cross_border_candidate_pair(
            scores=scores,
            price_signals=price_signals,
            aligned_components=aligned_components,
            priority=context.priority,
        )
    )

    ranked_pair = (
        reconcile_cross_border_ranked_original_candidates(
            original_bindings=original_bindings,
            ranked_candidates=ranked_candidates,
        )
    )

    return compose_cross_border_canonical_result(
        context=context,
        ranked_pair=ranked_pair,
    )
