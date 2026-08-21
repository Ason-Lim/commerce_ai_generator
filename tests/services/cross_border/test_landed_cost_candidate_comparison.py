from __future__ import annotations

from decimal import Decimal

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.landed_cost_aggregation import (
    LandedCostAggregation,
    LandedCostAggregationQuality,
    LandedCostAggregationState,
)
from app.services.cross_border.landed_cost_candidate_comparison import (
    LandedCostCandidateComparisonState,
    LandedCostCandidateRelation,
    compare_landed_cost_candidates,
)


def _context(
    *,
    destination_country: str = "US",
) -> CrossBorderEvaluationContext:
    return CrossBorderEvaluationContext(
        origin_country="KR",
        destination_country=destination_country,
    )


def _aggregation(
    total: str,
    *,
    currency: str = "USD",
    context: CrossBorderEvaluationContext | None = None,
    quality: LandedCostAggregationQuality = (
        LandedCostAggregationQuality.KNOWN
    ),
) -> LandedCostAggregation:
    return LandedCostAggregation(
        state=LandedCostAggregationState.AGGREGATED,
        total=Decimal(total),
        currency=currency,
        context=context or _context(),
        included_component_count=3,
        quality=quality,
        reason="bounded aggregation",
    )


def _not_aggregated() -> LandedCostAggregation:
    return LandedCostAggregation(
        state=LandedCostAggregationState.NOT_AGGREGATED,
        total=None,
        currency=None,
        context=None,
        included_component_count=0,
        quality=None,
        reason="not aggregated",
    )


def test_first_lower_total_is_first_less():
    result = compare_landed_cost_candidates(
        _aggregation("100"),
        _aggregation("120"),
    )

    assert (
        result.state
        is LandedCostCandidateComparisonState.COMPARED
    )

    assert (
        result.relation
        is LandedCostCandidateRelation.FIRST_LESS
    )

    assert result.first_total == Decimal("100")
    assert result.second_total == Decimal("120")
    assert result.currency == "USD"
    assert result.context == _context()


def test_second_lower_total_is_second_less():
    result = compare_landed_cost_candidates(
        _aggregation("150"),
        _aggregation("120"),
    )

    assert (
        result.relation
        is LandedCostCandidateRelation.SECOND_LESS
    )


def test_equal_total_is_equal():
    result = compare_landed_cost_candidates(
        _aggregation("120"),
        _aggregation("120"),
    )

    assert (
        result.relation
        is LandedCostCandidateRelation.EQUAL
    )


def test_zero_first_total_is_real_comparable_value():
    result = compare_landed_cost_candidates(
        _aggregation("0"),
        _aggregation("10"),
    )

    assert (
        result.relation
        is LandedCostCandidateRelation.FIRST_LESS
    )

    assert result.first_total == Decimal("0")


def test_zero_second_total_is_real_comparable_value():
    result = compare_landed_cost_candidates(
        _aggregation("10"),
        _aggregation("0"),
    )

    assert (
        result.relation
        is LandedCostCandidateRelation.SECOND_LESS
    )


def test_equal_zero_totals_are_equal():
    result = compare_landed_cost_candidates(
        _aggregation("0"),
        _aggregation("0"),
    )

    assert (
        result.relation
        is LandedCostCandidateRelation.EQUAL
    )


def test_known_vs_estimated_quality_is_preserved():
    result = compare_landed_cost_candidates(
        _aggregation(
            "100",
            quality=(
                LandedCostAggregationQuality.KNOWN
            ),
        ),
        _aggregation(
            "120",
            quality=(
                LandedCostAggregationQuality.ESTIMATED
            ),
        ),
    )

    assert (
        result.relation
        is LandedCostCandidateRelation.FIRST_LESS
    )

    assert (
        result.first_quality
        is LandedCostAggregationQuality.KNOWN
    )

    assert (
        result.second_quality
        is LandedCostAggregationQuality.ESTIMATED
    )


def test_estimated_lower_than_known_remains_numeric_relation():
    result = compare_landed_cost_candidates(
        _aggregation(
            "90",
            quality=(
                LandedCostAggregationQuality.ESTIMATED
            ),
        ),
        _aggregation(
            "100",
            quality=(
                LandedCostAggregationQuality.KNOWN
            ),
        ),
    )

    assert (
        result.relation
        is LandedCostCandidateRelation.FIRST_LESS
    )

    assert (
        result.first_quality
        is LandedCostAggregationQuality.ESTIMATED
    )

    assert (
        result.second_quality
        is LandedCostAggregationQuality.KNOWN
    )


def test_derived_quality_is_preserved():
    result = compare_landed_cost_candidates(
        _aggregation(
            "100",
            quality=(
                LandedCostAggregationQuality.DERIVED
            ),
        ),
        _aggregation(
            "120",
            quality=(
                LandedCostAggregationQuality.KNOWN
            ),
        ),
    )

    assert (
        result.first_quality
        is LandedCostAggregationQuality.DERIVED
    )


def test_first_not_aggregated_is_not_compared():
    result = compare_landed_cost_candidates(
        _not_aggregated(),
        _aggregation("120"),
    )

    assert (
        result.state
        is LandedCostCandidateComparisonState.NOT_COMPARED
    )

    assert result.relation is None
    assert result.first_total is None
    assert result.second_total is None


def test_second_not_aggregated_is_not_compared():
    result = compare_landed_cost_candidates(
        _aggregation("120"),
        _not_aggregated(),
    )

    assert (
        result.state
        is LandedCostCandidateComparisonState.NOT_COMPARED
    )


def test_currency_mismatch_is_not_compared():
    result = compare_landed_cost_candidates(
        _aggregation(
            "100",
            currency="USD",
        ),
        _aggregation(
            "100000",
            currency="KRW",
        ),
    )

    assert (
        result.state
        is LandedCostCandidateComparisonState.NOT_COMPARED
    )

    assert result.relation is None


def test_context_mismatch_is_not_compared():
    result = compare_landed_cost_candidates(
        _aggregation(
            "100",
            context=_context(
                destination_country="US",
            ),
        ),
        _aggregation(
            "120",
            context=_context(
                destination_country="JP",
            ),
        ),
    )

    assert (
        result.state
        is LandedCostCandidateComparisonState.NOT_COMPARED
    )


def test_first_less_does_not_mean_recommended():
    result = compare_landed_cost_candidates(
        _aggregation("100"),
        _aggregation("120"),
    )

    assert (
        result.relation
        is LandedCostCandidateRelation.FIRST_LESS
    )

    reason = result.reason.lower()

    assert "recommend" not in reason
    assert "best" not in reason
    assert "preferred" not in reason
    assert "optimal" not in reason
    assert "selected" not in reason


def test_result_has_no_ranking_surface():
    result = compare_landed_cost_candidates(
        _aggregation("100"),
        _aggregation("120"),
    )

    assert not hasattr(
        result,
        "winner",
    )

    assert not hasattr(
        result,
        "rank",
    )

    assert not hasattr(
        result,
        "recommended_candidate",
    )


def test_relation_vocabulary_is_bounded():
    assert {
        relation.value
        for relation in LandedCostCandidateRelation
    } == {
        "first_less",
        "second_less",
        "equal",
    }


def test_comparison_state_vocabulary_is_bounded():
    assert {
        state.value
        for state in LandedCostCandidateComparisonState
    } == {
        "compared",
        "not_compared",
    }


def test_comparison_does_not_mutate_inputs():
    first = _aggregation("100")
    second = _aggregation("120")

    compare_landed_cost_candidates(
        first,
        second,
    )

    assert first.total == Decimal("100")
    assert second.total == Decimal("120")
