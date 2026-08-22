from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from app.services.cross_border.landed_cost_aggregation import (
    LandedCostAggregationQuality,
)
from app.services.cross_border.landed_cost_candidate_comparison import (
    LandedCostCandidateComparison,
    LandedCostCandidateComparisonState,
    LandedCostCandidateRelation,
)
from app.services.cross_border.landed_cost_comparison_binding import (
    bind_landed_cost_comparison_candidates,
)
from app.services.recommendation.cross_border_bound_evidence_alignment import (
    CrossBorderBoundEvidenceAlignment,
    align_cross_border_bound_evidence,
)
from app.services.recommendation.cross_border_candidate_reference_binding import (
    bind_cross_border_candidate_reference,
)
from app.services.recommendation.cross_border_candidate_reference_binding_set import (
    validate_cross_border_candidate_reference_bindings,
)


def _binding(
    candidate_ref: str,
    candidate_position: int,
):
    return bind_cross_border_candidate_reference(
        candidate_ref=candidate_ref,
        candidate_position=candidate_position,
        binding_source="cross_border_handoff",
    )


def _binding_set(*, reversed_order: bool = False):
    first = _binding(
        "candidate:first",
        1,
    )
    second = _binding(
        "candidate:second",
        2,
    )
    bindings = (
        (second, first)
        if reversed_order
        else (first, second)
    )
    return validate_cross_border_candidate_reference_bindings(
        bindings
    )


def _comparison():
    return LandedCostCandidateComparison(
        state=LandedCostCandidateComparisonState.COMPARED,
        relation=LandedCostCandidateRelation.FIRST_LESS,
        first_total=Decimal("100"),
        second_total=Decimal("120"),
        currency="USD",
        context=None,
        first_quality=LandedCostAggregationQuality.KNOWN,
        second_quality=LandedCostAggregationQuality.ESTIMATED,
        reason="bounded comparison",
    )


def _bound_comparison(
    *,
    first_ref: str = "candidate:first",
    second_ref: str = "candidate:second",
):
    return bind_landed_cost_comparison_candidates(
        first_candidate_ref=first_ref,
        second_candidate_ref=second_ref,
        comparison=_comparison(),
    )


def test_exact_positional_alignment_is_accepted():
    result = align_cross_border_bound_evidence(
        binding_set=_binding_set(),
        bound_comparison=_bound_comparison(),
    )

    assert isinstance(
        result,
        CrossBorderBoundEvidenceAlignment,
    )
    assert result.first_candidate_ref == "candidate:first"
    assert result.second_candidate_ref == "candidate:second"


def test_binding_tuple_order_does_not_define_alignment():
    result = align_cross_border_bound_evidence(
        binding_set=_binding_set(
            reversed_order=True
        ),
        bound_comparison=_bound_comparison(),
    )

    assert (
        result.position_one_binding.candidate_position
        == 1
    )
    assert (
        result.position_two_binding.candidate_position
        == 2
    )
    assert result.first_candidate_ref == "candidate:first"
    assert result.second_candidate_ref == "candidate:second"


def test_position_one_mismatch_is_rejected():
    with pytest.raises(
        ValueError,
        match=(
            "candidate position 1 must match "
            "bound comparison first candidate"
        ),
    ):
        align_cross_border_bound_evidence(
            binding_set=_binding_set(),
            bound_comparison=_bound_comparison(
                first_ref="candidate:wrong",
            ),
        )


def test_position_two_mismatch_is_rejected():
    with pytest.raises(
        ValueError,
        match=(
            "candidate position 2 must match "
            "bound comparison second candidate"
        ),
    ):
        align_cross_border_bound_evidence(
            binding_set=_binding_set(),
            bound_comparison=_bound_comparison(
                second_ref="candidate:wrong",
            ),
        )


def test_swapped_cross_border_refs_are_rejected():
    with pytest.raises(
        ValueError,
        match="candidate position 1",
    ):
        align_cross_border_bound_evidence(
            binding_set=_binding_set(),
            bound_comparison=_bound_comparison(
                first_ref="candidate:second",
                second_ref="candidate:first",
            ),
        )


def test_bound_comparison_is_preserved_by_identity():
    bound = _bound_comparison()

    result = align_cross_border_bound_evidence(
        binding_set=_binding_set(),
        bound_comparison=bound,
    )

    assert result.bound_comparison is bound
    assert (
        result.bound_comparison.comparison
        is bound.comparison
    )


def test_comparison_semantics_are_not_reinterpreted():
    bound = _bound_comparison()

    result = align_cross_border_bound_evidence(
        binding_set=_binding_set(),
        bound_comparison=bound,
    )

    assert (
        result.bound_comparison.relation
        is LandedCostCandidateRelation.FIRST_LESS
    )
    assert (
        result.bound_comparison.comparison.first_total
        == Decimal("100")
    )
    assert (
        result.bound_comparison.comparison.second_total
        == Decimal("120")
    )


def test_alignment_is_immutable():
    result = align_cross_border_bound_evidence(
        binding_set=_binding_set(),
        bound_comparison=_bound_comparison(),
    )

    with pytest.raises(FrozenInstanceError):
        result.position_one_binding = _binding(
            "candidate:other",
            1,
        )


def test_alignment_exposes_no_ranking_or_selection_authority():
    result = align_cross_border_bound_evidence(
        binding_set=_binding_set(),
        bound_comparison=_bound_comparison(),
    )

    forbidden = (
        "winner",
        "best",
        "score",
        "rank",
        "recommended_candidate",
        "selected_candidate",
        "preferred_candidate",
        "cheaper_candidate",
    )

    for name in forbidden:
        assert not hasattr(result, name)


def test_alignment_exposes_no_identity_resolution_authority():
    result = align_cross_border_bound_evidence(
        binding_set=_binding_set(),
        bound_comparison=_bound_comparison(),
    )

    forbidden = (
        "product_id",
        "product_identity_key",
        "listing_id",
        "offer_id",
        "product_url",
        "canonical_product_id",
        "matched_product",
    )

    for name in forbidden:
        assert not hasattr(result, name)
