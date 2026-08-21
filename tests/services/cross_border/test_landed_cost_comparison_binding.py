from __future__ import annotations

from decimal import Decimal

import pytest

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.landed_cost_aggregation import (
    LandedCostAggregationQuality,
)
from app.services.cross_border.landed_cost_candidate_comparison import (
    LandedCostCandidateComparison,
    LandedCostCandidateComparisonState,
    LandedCostCandidateRelation,
)
from app.services.cross_border.landed_cost_comparison_binding import (
    BoundLandedCostComparison,
    LandedCostCandidateRef,
    bind_landed_cost_comparison_candidates,
)


def _context() -> CrossBorderEvaluationContext:
    return CrossBorderEvaluationContext(
        origin_country="KR",
        destination_country="US",
    )


def _comparison(
    relation: LandedCostCandidateRelation | None = (
        LandedCostCandidateRelation.FIRST_LESS
    ),
    *,
    state: LandedCostCandidateComparisonState = (
        LandedCostCandidateComparisonState.COMPARED
    ),
) -> LandedCostCandidateComparison:
    if (
        state
        is LandedCostCandidateComparisonState.NOT_COMPARED
    ):
        relation = None

    return LandedCostCandidateComparison(
        state=state,
        relation=relation,
        first_total=(
            Decimal("100")
            if state
            is LandedCostCandidateComparisonState.COMPARED
            else None
        ),
        second_total=(
            Decimal("120")
            if state
            is LandedCostCandidateComparisonState.COMPARED
            else None
        ),
        currency=(
            "USD"
            if state
            is LandedCostCandidateComparisonState.COMPARED
            else None
        ),
        context=(
            _context()
            if state
            is LandedCostCandidateComparisonState.COMPARED
            else None
        ),
        first_quality=(
            LandedCostAggregationQuality.KNOWN
            if state
            is LandedCostCandidateComparisonState.COMPARED
            else None
        ),
        second_quality=(
            LandedCostAggregationQuality.ESTIMATED
            if state
            is LandedCostCandidateComparisonState.COMPARED
            else None
        ),
        reason="bounded comparison",
    )


def test_candidate_ref_is_normalized():
    candidate = LandedCostCandidateRef(
        candidate_ref="  amazon-us:offer:123  ",
    )

    assert (
        candidate.candidate_ref
        == "amazon-us:offer:123"
    )


def test_blank_candidate_ref_is_rejected():
    with pytest.raises(
        ValueError,
        match="candidate_ref must be non-empty",
    ):
        LandedCostCandidateRef(
            candidate_ref="   ",
        )


def test_comparison_can_bind_candidate_refs():
    comparison = _comparison()

    bound = bind_landed_cost_comparison_candidates(
        first_candidate_ref="amazon-us:offer:123",
        second_candidate_ref="korea-direct:offer:456",
        comparison=comparison,
    )

    assert isinstance(
        bound,
        BoundLandedCostComparison,
    )

    assert (
        bound.first_candidate.candidate_ref
        == "amazon-us:offer:123"
    )

    assert (
        bound.second_candidate.candidate_ref
        == "korea-direct:offer:456"
    )

    assert bound.comparison is comparison


def test_first_less_preserves_first_candidate_position():
    bound = bind_landed_cost_comparison_candidates(
        first_candidate_ref="candidate:first",
        second_candidate_ref="candidate:second",
        comparison=_comparison(
            LandedCostCandidateRelation.FIRST_LESS
        ),
    )

    assert (
        bound.relation
        is LandedCostCandidateRelation.FIRST_LESS
    )

    assert (
        bound.first_candidate.candidate_ref
        == "candidate:first"
    )


def test_second_less_preserves_second_candidate_position():
    bound = bind_landed_cost_comparison_candidates(
        first_candidate_ref="candidate:first",
        second_candidate_ref="candidate:second",
        comparison=_comparison(
            LandedCostCandidateRelation.SECOND_LESS
        ),
    )

    assert (
        bound.relation
        is LandedCostCandidateRelation.SECOND_LESS
    )

    assert (
        bound.second_candidate.candidate_ref
        == "candidate:second"
    )


def test_equal_relation_is_preserved():
    bound = bind_landed_cost_comparison_candidates(
        first_candidate_ref="candidate:first",
        second_candidate_ref="candidate:second",
        comparison=_comparison(
            LandedCostCandidateRelation.EQUAL
        ),
    )

    assert (
        bound.relation
        is LandedCostCandidateRelation.EQUAL
    )


def test_not_compared_preserves_none_relation():
    bound = bind_landed_cost_comparison_candidates(
        first_candidate_ref="candidate:first",
        second_candidate_ref="candidate:second",
        comparison=_comparison(
            state=(
                LandedCostCandidateComparisonState.NOT_COMPARED
            )
        ),
    )

    assert bound.is_compared is False
    assert bound.relation is None


def test_compared_state_is_preserved():
    bound = bind_landed_cost_comparison_candidates(
        first_candidate_ref="candidate:first",
        second_candidate_ref="candidate:second",
        comparison=_comparison(),
    )

    assert bound.is_compared is True


def test_duplicate_candidate_refs_are_rejected():
    with pytest.raises(
        ValueError,
        match="must be distinct",
    ):
        bind_landed_cost_comparison_candidates(
            first_candidate_ref="candidate:1",
            second_candidate_ref="candidate:1",
            comparison=_comparison(),
        )


def test_duplicate_candidate_refs_after_normalization_are_rejected():
    with pytest.raises(
        ValueError,
        match="must be distinct",
    ):
        bind_landed_cost_comparison_candidates(
            first_candidate_ref=" candidate:1 ",
            second_candidate_ref="candidate:1",
            comparison=_comparison(),
        )


def test_quality_metadata_remains_in_comparison():
    comparison = _comparison()

    bound = bind_landed_cost_comparison_candidates(
        first_candidate_ref="candidate:first",
        second_candidate_ref="candidate:second",
        comparison=comparison,
    )

    assert (
        bound.comparison.first_quality
        is LandedCostAggregationQuality.KNOWN
    )

    assert (
        bound.comparison.second_quality
        is LandedCostAggregationQuality.ESTIMATED
    )


def test_binding_does_not_mutate_comparison():
    comparison = _comparison()

    bind_landed_cost_comparison_candidates(
        first_candidate_ref="candidate:first",
        second_candidate_ref="candidate:second",
        comparison=comparison,
    )

    assert (
        comparison.relation
        is LandedCostCandidateRelation.FIRST_LESS
    )

    assert comparison.first_total == Decimal("100")
    assert comparison.second_total == Decimal("120")


def test_binding_has_no_winner_surface():
    bound = bind_landed_cost_comparison_candidates(
        first_candidate_ref="candidate:first",
        second_candidate_ref="candidate:second",
        comparison=_comparison(),
    )

    assert not hasattr(
        bound,
        "winner",
    )

    assert not hasattr(
        bound,
        "recommended_candidate",
    )

    assert not hasattr(
        bound,
        "selected_candidate",
    )


def test_first_less_is_not_renamed_to_cheaper():
    bound = bind_landed_cost_comparison_candidates(
        first_candidate_ref="candidate:first",
        second_candidate_ref="candidate:second",
        comparison=_comparison(
            LandedCostCandidateRelation.FIRST_LESS
        ),
    )

    assert not hasattr(
        bound,
        "cheaper_candidate",
    )

    assert not hasattr(
        bound,
        "better_candidate",
    )


def test_candidate_ref_contract_does_not_claim_identity_authority():
    forbidden = {
        "resolve",
        "match",
        "canonicalize",
        "normalize_product",
        "identify_product",
        "rank",
        "recommend",
        "select",
    }

    public_names = {
        name.lower()
        for name in dir(
            LandedCostCandidateRef
        )
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(
        public_names
    )


def test_bound_comparison_contract_does_not_claim_recommendation():
    forbidden = {
        "winner",
        "best",
        "recommended_candidate",
        "selected_candidate",
        "preferred_candidate",
        "rank",
    }

    public_names = {
        name.lower()
        for name in dir(
            BoundLandedCostComparison
        )
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(
        public_names
    )
