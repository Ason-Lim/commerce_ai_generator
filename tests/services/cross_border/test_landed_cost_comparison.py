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
from app.services.cross_border.landed_cost_comparison import (
    LandedCostComparisonReadinessState,
    evaluate_landed_cost_comparison_readiness,
)


def _context(
    *,
    destination_country: str = "US",
) -> CrossBorderEvaluationContext:
    return CrossBorderEvaluationContext(
        origin_country="KR",
        destination_country=destination_country,
    )


def _aggregated(
    *,
    total: str = "120.00",
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
        reason="not ready",
    )


def test_same_currency_and_context_are_ready():
    result = evaluate_landed_cost_comparison_readiness(
        _aggregated(
            total="120",
        ),
        _aggregated(
            total="125",
        ),
    )

    assert (
        result.state
        is LandedCostComparisonReadinessState.READY
    )
    assert result.currency == "USD"
    assert result.context == _context()


def test_different_totals_do_not_prevent_readiness():
    result = evaluate_landed_cost_comparison_readiness(
        _aggregated(
            total="100",
        ),
        _aggregated(
            total="999",
        ),
    )

    assert (
        result.state
        is LandedCostComparisonReadinessState.READY
    )


def test_equal_totals_are_ready():
    result = evaluate_landed_cost_comparison_readiness(
        _aggregated(
            total="120",
        ),
        _aggregated(
            total="120",
        ),
    )

    assert (
        result.state
        is LandedCostComparisonReadinessState.READY
    )


def test_quality_difference_is_preserved():
    result = evaluate_landed_cost_comparison_readiness(
        _aggregated(
            quality=(
                LandedCostAggregationQuality.KNOWN
            ),
        ),
        _aggregated(
            quality=(
                LandedCostAggregationQuality.ESTIMATED
            ),
        ),
    )

    assert (
        result.state
        is LandedCostComparisonReadinessState.READY
    )

    assert (
        result.first_quality
        is LandedCostAggregationQuality.KNOWN
    )

    assert (
        result.second_quality
        is LandedCostAggregationQuality.ESTIMATED
    )


def test_derived_and_estimated_can_be_ready():
    result = evaluate_landed_cost_comparison_readiness(
        _aggregated(
            quality=(
                LandedCostAggregationQuality.DERIVED
            ),
        ),
        _aggregated(
            quality=(
                LandedCostAggregationQuality.ESTIMATED
            ),
        ),
    )

    assert (
        result.state
        is LandedCostComparisonReadinessState.READY
    )


def test_first_not_aggregated_is_not_ready():
    result = evaluate_landed_cost_comparison_readiness(
        _not_aggregated(),
        _aggregated(),
    )

    assert (
        result.state
        is LandedCostComparisonReadinessState.NOT_READY
    )


def test_second_not_aggregated_is_not_ready():
    result = evaluate_landed_cost_comparison_readiness(
        _aggregated(),
        _not_aggregated(),
    )

    assert (
        result.state
        is LandedCostComparisonReadinessState.NOT_READY
    )


def test_both_not_aggregated_are_not_ready():
    result = evaluate_landed_cost_comparison_readiness(
        _not_aggregated(),
        _not_aggregated(),
    )

    assert (
        result.state
        is LandedCostComparisonReadinessState.NOT_READY
    )


def test_currency_mismatch_is_not_ready():
    result = evaluate_landed_cost_comparison_readiness(
        _aggregated(
            currency="USD",
        ),
        _aggregated(
            currency="KRW",
        ),
    )

    assert (
        result.state
        is LandedCostComparisonReadinessState.NOT_READY
    )
    assert result.currency is None


def test_context_mismatch_is_not_ready():
    result = evaluate_landed_cost_comparison_readiness(
        _aggregated(
            context=_context(
                destination_country="US",
            ),
        ),
        _aggregated(
            context=_context(
                destination_country="JP",
            ),
        ),
    )

    assert (
        result.state
        is LandedCostComparisonReadinessState.NOT_READY
    )
    assert result.context is None


def test_missing_first_total_is_not_ready():
    first = LandedCostAggregation(
        state=LandedCostAggregationState.AGGREGATED,
        total=None,
        currency="USD",
        context=_context(),
        included_component_count=3,
        quality=LandedCostAggregationQuality.KNOWN,
        reason="invalid synthetic test input",
    )

    result = evaluate_landed_cost_comparison_readiness(
        first,
        _aggregated(),
    )

    assert (
        result.state
        is LandedCostComparisonReadinessState.NOT_READY
    )


def test_missing_second_total_is_not_ready():
    second = LandedCostAggregation(
        state=LandedCostAggregationState.AGGREGATED,
        total=None,
        currency="USD",
        context=_context(),
        included_component_count=3,
        quality=LandedCostAggregationQuality.KNOWN,
        reason="invalid synthetic test input",
    )

    result = evaluate_landed_cost_comparison_readiness(
        _aggregated(),
        second,
    )

    assert (
        result.state
        is LandedCostComparisonReadinessState.NOT_READY
    )


def test_zero_total_is_real_comparable_value():
    result = evaluate_landed_cost_comparison_readiness(
        _aggregated(
            total="0",
        ),
        _aggregated(
            total="10",
        ),
    )

    assert (
        result.state
        is LandedCostComparisonReadinessState.READY
    )


def test_ready_result_has_no_comparison_relation():
    result = evaluate_landed_cost_comparison_readiness(
        _aggregated(
            total="100",
        ),
        _aggregated(
            total="120",
        ),
    )

    assert (
        result.state
        is LandedCostComparisonReadinessState.READY
    )

    assert not hasattr(
        result,
        "relation",
    )

    assert not hasattr(
        result,
        "cheaper",
    )


def test_ready_result_is_not_recommendation():
    result = evaluate_landed_cost_comparison_readiness(
        _aggregated(
            total="100",
        ),
        _aggregated(
            total="120",
        ),
    )

    reason = result.reason.lower()

    assert "recommend" not in reason
    assert "best" not in reason
    assert "cheaper" not in reason
    assert "optimal" not in reason


def test_readiness_vocabulary_is_bounded():
    assert {
        state.value
        for state in LandedCostComparisonReadinessState
    } == {
        "ready",
        "not_ready",
    }
