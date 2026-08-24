from __future__ import annotations

from collections.abc import Sequence

from app.services.recommendation.cross_border_bound_price_signal_composition import (
    compose_bound_cross_border_price_signals,
)
from app.services.recommendation.cross_border_candidate_component_alignment import (
    align_cross_border_candidate_components,
)
from app.services.recommendation.cross_border_candidate_component_binding import (
    bind_cross_border_candidate_components,
)
from app.services.recommendation.cross_border_candidate_reference_binding_set import (
    CrossBorderCandidateReferenceBindingSet,
)
from app.services.recommendation.cross_border_candidate_score_composition import (
    compose_cross_border_candidate_scores,
)
from app.services.recommendation.cross_border_provider_adjacent_result_orchestration import (
    compose_cross_border_provider_adjacent_result,
)
from app.services.recommendation.cross_border_scoring_binding import (
    BoundCrossBorderScoringInput,
)
from app.services.recommendation.models import (
    RecommendationCandidate,
    RecommendationContext,
    RecommendationResult,
)


def compose_cross_border_upstream_result(
    *,
    context: RecommendationContext,
    reference_binding_set: CrossBorderCandidateReferenceBindingSet,
    candidates: Sequence[RecommendationCandidate],
    scoring_input: BoundCrossBorderScoringInput,
) -> RecommendationResult:
    """
    Compose already-established Cross-Border scoring inputs into the
    sealed provider-adjacent canonical RecommendationResult.

    The caller must explicitly supply the canonical candidate sequence
    whose positions correspond to candidate_position values 1 and 2.

    Authority flow:

    - candidate_position joins supplied candidates to component bindings;
    - BoundCrossBorderScoringInput owns landed-cost scoring evidence;
    - RecommendationCandidate.score.components owns base components;
    - RecommendationContext.priority owns scoring and ranking priority;
    - provider-adjacent orchestration owns canonical result composition.

    Binding-set tuple order is not positional authority. Component
    bindings are normalized by each binding's explicit candidate_position
    before first/second Cross-Border alignment.

    This boundary does not:

    - accept or validate a raw Cross-Border handoff;
    - derive landed-cost evidence;
    - infer product identity from candidate_ref;
    - collect, deduplicate, normalize, or enrich candidates;
    - create Recommendation candidates;
    - reinterpret priority;
    - create winner or selection authority;
    - modify RecommendationProvider;
    - activate production routing;
    - execute transactions.
    """

    component_bindings = bind_cross_border_candidate_components(
        reference_bindings=reference_binding_set,
        candidates=candidates,
    )

    components_by_position = {
        reference_binding.candidate_position: component_binding
        for reference_binding, component_binding in zip(
            reference_binding_set.bindings,
            component_bindings,
        )
    }

    first_component_binding = components_by_position[1]
    second_component_binding = components_by_position[2]

    price_signals = compose_bound_cross_border_price_signals(
        scoring_input
    )

    aligned_components = align_cross_border_candidate_components(
        price_signals=price_signals,
        first_binding=first_component_binding,
        second_binding=second_component_binding,
    )

    scores = compose_cross_border_candidate_scores(
        aligned_components=aligned_components,
        priority=context.priority,
    )

    return compose_cross_border_provider_adjacent_result(
        context=context,
        reference_binding_set=reference_binding_set,
        candidates=candidates,
        scores=scores,
        price_signals=price_signals,
        aligned_components=aligned_components,
    )
