from __future__ import annotations

from decimal import Decimal

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.landed_cost_aggregation import (
    LandedCostAggregationQuality,
)
from app.services.cross_border.landed_cost_bound_readiness import (
    BoundLandedCostReadinessState,
    evaluate_bound_landed_cost_readiness,
)
from app.services.cross_border.landed_cost_candidate_comparison import (
    LandedCostCandidateComparison,
    LandedCostCandidateComparisonState,
    LandedCostCandidateRelation,
)
from app.services.cross_border.landed_cost_comparison_binding import (
    BoundLandedCostComparison,
    LandedCostCandidateRef,
)


def _context() -> CrossBorderEvaluationContext:
    return CrossBorderEvaluationContext(
        origin_country="KR",
        destination_country="US",
    )


def _comparison(
    *,
    state: LandedCostCandidateComparisonState = (
        LandedCostCandidateComparisonState.COMPARED
    ),
    relation: LandedCostCandidateRelation | None = (
        LandedCostCandidateRelation.FIRST_LESS
    ),
    first_total: Decimal | None = Decimal("100"),
    second_total: Decimal | None = Decimal("120"),
    currency: str | None = "USD",
    context: CrossBorderEvaluationContext | None = None,
    first_quality: LandedCostAggregationQuality | None = (
        LandedCostAggregationQuality.KNOWN
    ),
    second_quality: LandedCostAggregationQuality | None = (
        LandedCostAggregationQuality.ESTIMATED
    ),
) -> LandedCostCandidateComparison:
    return LandedCostCandidateComparison(
        state=state,
        relation=relation,
        first_total=first_total,
        second_total=second_total,
        currency=currency,
        context=(
            _context()
            if context is None
            and state
            is LandedCostCandidateComparisonState.COMPARED
            else context
        ),
        first_quality=first_quality,
        second_quality=second_quality,
        reason="bounded comparison",
    )


def _bound(
    comparison: LandedCostCandidateComparison | None = None,
) -> BoundLandedCostComparison:
    return BoundLandedCostComparison(
        first_candidate=LandedCostCandidateRef(
            candidate_ref="candidate:first",
        ),
        second_candidate=LandedCostCandidateRef(
            candidate_ref="candidate:second",
        ),
        comparison=comparison or _comparison(),
    )


def test_complete_bound_comparison_is_ready():
    result = evaluate_bound_landed_cost_readiness(
        _bound()
    )

    assert (
        result.state
        is BoundLandedCostReadinessState.READY
    )

    assert (
        result.first_candidate_ref
        == "candidate:first"
    )

    assert (
        result.second_candidate_ref
        == "candidate:second"
    )

    assert (
        result.relation
        is LandedCostCandidateRelation.FIRST_LESS
    )

    assert result.currency == "USD"
    assert result.context == _context()


def test_quality_metadata_is_preserved():
    result = evaluate_bound_landed_cost_readiness(
        _bound()
    )

    assert (
        result.first_quality
        is LandedCostAggregationQuality.KNOWN
    )

    assert (
        result.second_quality
        is LandedCostAggregationQuality.ESTIMATED
    )


def test_second_less_can_be_ready():
    result = evaluate_bound_landed_cost_readiness(
        _bound(
            _comparison(
                relation=(
                    LandedCostCandidateRelation.SECOND_LESS
                )
            )
        )
    )

    assert (
        result.state
        is BoundLandedCostReadinessState.READY
    )

    assert (
        result.relation
        is LandedCostCandidateRelation.SECOND_LESS
    )


def test_equal_can_be_ready():
    result = evaluate_bound_landed_cost_readiness(
        _bound(
            _comparison(
                relation=LandedCostCandidateRelation.EQUAL,
                first_total=Decimal("100"),
                second_total=Decimal("100"),
            )
        )
    )

    assert (
        result.state
        is BoundLandedCostReadinessState.READY
    )


def test_not_compared_is_not_ready():
    comparison = _comparison(
        state=(
            LandedCostCandidateComparisonState.NOT_COMPARED
        ),
        relation=None,
        first_total=None,
        second_total=None,
        currency=None,
        context=None,
        first_quality=None,
        second_quality=None,
    )

    result = evaluate_bound_landed_cost_readiness(
        _bound(comparison)
    )

    assert (
        result.state
        is BoundLandedCostReadinessState.NOT_READY
    )

    assert result.relation is None


def test_missing_relation_is_not_ready():
    result = evaluate_bound_landed_cost_readiness(
        _bound(
            _comparison(
                relation=None,
            )
        )
    )

    assert (
        result.state
        is BoundLandedCostReadinessState.NOT_READY
    )


def test_missing_first_total_is_not_ready():
    result = evaluate_bound_landed_cost_readiness(
        _bound(
            _comparison(
                first_total=None,
            )
        )
    )

    assert (
        result.state
        is BoundLandedCostReadinessState.NOT_READY
    )


def test_missing_second_total_is_not_ready():
    result = evaluate_bound_landed_cost_readiness(
        _bound(
            _comparison(
                second_total=None,
            )
        )
    )

    assert (
        result.state
        is BoundLandedCostReadinessState.NOT_READY
    )


def test_zero_totals_are_real_evidence():
    result = evaluate_bound_landed_cost_readiness(
        _bound(
            _comparison(
                relation=LandedCostCandidateRelation.EQUAL,
                first_total=Decimal("0"),
                second_total=Decimal("0"),
            )
        )
    )

    assert (
        result.state
        is BoundLandedCostReadinessState.READY
    )


def test_missing_currency_is_not_ready():
    result = evaluate_bound_landed_cost_readiness(
        _bound(
            _comparison(
                currency=None,
            )
        )
    )

    assert (
        result.state
        is BoundLandedCostReadinessState.NOT_READY
    )


def test_missing_context_is_not_ready():
    comparison = LandedCostCandidateComparison(
        state=LandedCostCandidateComparisonState.COMPARED,
        relation=LandedCostCandidateRelation.FIRST_LESS,
        first_total=Decimal("100"),
        second_total=Decimal("120"),
        currency="USD",
        context=None,
        first_quality=LandedCostAggregationQuality.KNOWN,
        second_quality=(
            LandedCostAggregationQuality.ESTIMATED
        ),
        reason="synthetic incomplete comparison",
    )

    result = evaluate_bound_landed_cost_readiness(
        _bound(comparison)
    )

    assert (
        result.state
        is BoundLandedCostReadinessState.NOT_READY
    )


def test_missing_first_quality_is_not_ready():
    result = evaluate_bound_landed_cost_readiness(
        _bound(
            _comparison(
                first_quality=None,
            )
        )
    )

    assert (
        result.state
        is BoundLandedCostReadinessState.NOT_READY
    )


def test_missing_second_quality_is_not_ready():
    result = evaluate_bound_landed_cost_readiness(
        _bound(
            _comparison(
                second_quality=None,
            )
        )
    )

    assert (
        result.state
        is BoundLandedCostReadinessState.NOT_READY
    )


def test_ready_does_not_mean_winner():
    result = evaluate_bound_landed_cost_readiness(
        _bound()
    )

    assert (
        result.state
        is BoundLandedCostReadinessState.READY
    )

    assert not hasattr(
        result,
        "winner",
    )

    assert not hasattr(
        result,
        "recommended_candidate",
    )

    assert not hasattr(
        result,
        "selected_candidate",
    )


def test_ready_does_not_create_ranking_surface():
    result = evaluate_bound_landed_cost_readiness(
        _bound()
    )

    assert not hasattr(
        result,
        "rank",
    )

    assert not hasattr(
        result,
        "score",
    )


def test_readiness_vocabulary_is_bounded():
    assert {
        state.value
        for state in BoundLandedCostReadinessState
    } == {
        "ready",
        "not_ready",
    }


def test_evaluation_does_not_mutate_bound_evidence():
    bound = _bound()

    evaluate_bound_landed_cost_readiness(
        bound
    )

    assert (
        bound.first_candidate.candidate_ref
        == "candidate:first"
    )

    assert (
        bound.second_candidate.candidate_ref
        == "candidate:second"
    )

    assert (
        bound.comparison.relation
        is LandedCostCandidateRelation.FIRST_LESS
    )
