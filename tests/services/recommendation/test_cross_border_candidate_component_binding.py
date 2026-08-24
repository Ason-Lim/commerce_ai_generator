import pytest

from app.services.recommendation.cross_border_candidate_component_binding import (
    bind_cross_border_candidate_components,
)
from app.services.recommendation.cross_border_candidate_reference_binding import (
    bind_cross_border_candidate_reference,
)
from app.services.recommendation.cross_border_candidate_reference_binding_set import (
    CrossBorderCandidateReferenceBindingSet,
)
from app.services.recommendation.models import (
    RecommendationCandidate,
    RecommendationPriority,
    RecommendationScoreComponents,
    RecommendationScoreResult,
)


def _candidate(
    *,
    product_id: str,
    components: RecommendationScoreComponents,
    rank: int,
) -> RecommendationCandidate:
    return RecommendationCandidate(
        item={
            "product_id": product_id,
        },
        score=RecommendationScoreResult(
            final_score=80.0,
            priority=RecommendationPriority.MIX,
            components=components,
        ),
        rank=rank,
    )


def _reference_bindings(
    *,
    first_ref: str = "cross-border-ref-B",
    second_ref: str = "cross-border-ref-A",
) -> CrossBorderCandidateReferenceBindingSet:
    return CrossBorderCandidateReferenceBindingSet(
        bindings=(
            bind_cross_border_candidate_reference(
                candidate_ref=first_ref,
                candidate_position=1,
                binding_source="test",
            ),
            bind_cross_border_candidate_reference(
                candidate_ref=second_ref,
                candidate_position=2,
                binding_source="test",
            ),
        )
    )


def test_binds_refs_to_candidate_score_components_by_position():
    first_components = RecommendationScoreComponents(
        quality=91.0,
        price=61.0,
    )
    second_components = RecommendationScoreComponents(
        quality=72.0,
        price=88.0,
    )

    first_candidate = _candidate(
        product_id="product-A",
        components=first_components,
        rank=1,
    )
    second_candidate = _candidate(
        product_id="product-B",
        components=second_components,
        rank=2,
    )

    first, second = bind_cross_border_candidate_components(
        reference_bindings=_reference_bindings(),
        candidates=(
            first_candidate,
            second_candidate,
        ),
    )

    assert first.candidate_ref == "cross-border-ref-B"
    assert second.candidate_ref == "cross-border-ref-A"

    assert (
        first.base_components
        is first_candidate.score.components
    )
    assert (
        second.base_components
        is second_candidate.score.components
    )


def test_does_not_join_candidate_ref_to_product_identity():
    first_candidate = _candidate(
        product_id="cross-border-ref-A",
        components=RecommendationScoreComponents(
            quality=90.0,
        ),
        rank=1,
    )
    second_candidate = _candidate(
        product_id="cross-border-ref-B",
        components=RecommendationScoreComponents(
            quality=70.0,
        ),
        rank=2,
    )

    first, second = bind_cross_border_candidate_components(
        reference_bindings=_reference_bindings(
            first_ref="cross-border-ref-B",
            second_ref="cross-border-ref-A",
        ),
        candidates=(
            first_candidate,
            second_candidate,
        ),
    )

    assert (
        first.base_components
        is first_candidate.score.components
    )
    assert (
        second.base_components
        is second_candidate.score.components
    )


@pytest.mark.parametrize(
    "candidates",
    [
        (),
        (
            _candidate(
                product_id="only",
                components=RecommendationScoreComponents(),
                rank=1,
            ),
        ),
        (
            _candidate(
                product_id="A",
                components=RecommendationScoreComponents(),
                rank=1,
            ),
            _candidate(
                product_id="B",
                components=RecommendationScoreComponents(),
                rank=2,
            ),
            _candidate(
                product_id="C",
                components=RecommendationScoreComponents(),
                rank=3,
            ),
        ),
    ],
)
def test_requires_exactly_two_candidates(candidates):
    with pytest.raises(
        ValueError,
        match="exactly two recommendation candidates are required",
    ):
        bind_cross_border_candidate_components(
            reference_bindings=_reference_bindings(),
            candidates=candidates,
        )
