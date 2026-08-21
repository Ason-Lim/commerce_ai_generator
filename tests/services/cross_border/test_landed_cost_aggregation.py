from __future__ import annotations

from decimal import Decimal

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.landed_cost import (
    LandedCostComponentEvidence,
    LandedCostComponentState,
)
from app.services.cross_border.landed_cost_aggregation import (
    LandedCostAggregationQuality,
    LandedCostAggregationState,
    aggregate_landed_cost_components,
)


def _context(
    *,
    destination_country: str = "US",
) -> CrossBorderEvaluationContext:
    return CrossBorderEvaluationContext(
        origin_country="KR",
        destination_country=destination_country,
    )


def _component(
    component: str,
    amount: str,
    *,
    state: LandedCostComponentState = (
        LandedCostComponentState.KNOWN
    ),
    currency: str = "USD",
    context: CrossBorderEvaluationContext | None = None,
) -> LandedCostComponentEvidence:
    return LandedCostComponentEvidence(
        component=component,
        state=state,
        amount=Decimal(amount),
        currency=currency,
        context=context or _context(),
    )


def test_known_components_are_aggregated():
    result = aggregate_landed_cost_components(
        [
            _component(
                "item_price",
                "100.00",
            ),
            _component(
                "shipping",
                "20.00",
            ),
            _component(
                "duty",
                "5.00",
            ),
        ]
    )

    assert (
        result.state
        is LandedCostAggregationState.AGGREGATED
    )
    assert result.total == Decimal("125.00")
    assert result.currency == "USD"
    assert result.context == _context()
    assert result.included_component_count == 3
    assert (
        result.quality
        is LandedCostAggregationQuality.KNOWN
    )


def test_known_zero_is_included_in_aggregation():
    result = aggregate_landed_cost_components(
        [
            _component(
                "item_price",
                "100",
            ),
            _component(
                "shipping",
                "20",
            ),
            _component(
                "duty",
                "0",
            ),
        ]
    )

    assert result.total == Decimal("120")
    assert result.included_component_count == 3


def test_not_applicable_component_is_excluded():
    result = aggregate_landed_cost_components(
        [
            _component(
                "item_price",
                "100",
            ),
            _component(
                "shipping",
                "20",
            ),
            LandedCostComponentEvidence(
                component="duty",
                state=(
                    LandedCostComponentState.NOT_APPLICABLE
                ),
            ),
        ]
    )

    assert (
        result.state
        is LandedCostAggregationState.AGGREGATED
    )
    assert result.total == Decimal("120")
    assert result.included_component_count == 2


def test_derived_component_sets_derived_quality():
    result = aggregate_landed_cost_components(
        [
            _component(
                "item_price",
                "100",
            ),
            _component(
                "tax",
                "10",
                state=(
                    LandedCostComponentState.DERIVED
                ),
            ),
        ]
    )

    assert result.total == Decimal("110")
    assert (
        result.quality
        is LandedCostAggregationQuality.DERIVED
    )


def test_estimated_component_sets_estimated_quality():
    result = aggregate_landed_cost_components(
        [
            _component(
                "item_price",
                "100",
            ),
            _component(
                "shipping",
                "20",
                state=(
                    LandedCostComponentState.ESTIMATED
                ),
            ),
        ]
    )

    assert result.total == Decimal("120")
    assert (
        result.quality
        is LandedCostAggregationQuality.ESTIMATED
    )


def test_estimated_dominates_derived_quality():
    result = aggregate_landed_cost_components(
        [
            _component(
                "item_price",
                "100",
            ),
            _component(
                "tax",
                "10",
                state=(
                    LandedCostComponentState.DERIVED
                ),
            ),
            _component(
                "shipping",
                "20",
                state=(
                    LandedCostComponentState.ESTIMATED
                ),
            ),
        ]
    )

    assert result.total == Decimal("130")
    assert (
        result.quality
        is LandedCostAggregationQuality.ESTIMATED
    )


def test_unknown_component_prevents_aggregation():
    result = aggregate_landed_cost_components(
        [
            _component(
                "item_price",
                "100",
            ),
            LandedCostComponentEvidence(
                component="duty",
                state=LandedCostComponentState.UNKNOWN,
            ),
        ]
    )

    assert (
        result.state
        is LandedCostAggregationState.NOT_AGGREGATED
    )
    assert result.total is None
    assert result.quality is None


def test_unavailable_component_prevents_aggregation():
    result = aggregate_landed_cost_components(
        [
            _component(
                "item_price",
                "100",
            ),
            LandedCostComponentEvidence(
                component="shipping",
                state=(
                    LandedCostComponentState.UNAVAILABLE
                ),
            ),
        ]
    )

    assert (
        result.state
        is LandedCostAggregationState.NOT_AGGREGATED
    )
    assert result.total is None


def test_currency_mismatch_prevents_aggregation():
    result = aggregate_landed_cost_components(
        [
            _component(
                "item_price",
                "100",
                currency="USD",
            ),
            _component(
                "shipping",
                "20000",
                currency="KRW",
            ),
        ]
    )

    assert (
        result.state
        is LandedCostAggregationState.NOT_AGGREGATED
    )
    assert result.total is None


def test_context_mismatch_prevents_aggregation():
    result = aggregate_landed_cost_components(
        [
            _component(
                "item_price",
                "100",
                context=_context(
                    destination_country="US",
                ),
            ),
            _component(
                "shipping",
                "20",
                context=_context(
                    destination_country="JP",
                ),
            ),
        ]
    )

    assert (
        result.state
        is LandedCostAggregationState.NOT_AGGREGATED
    )


def test_missing_context_prevents_aggregation():
    without_context = LandedCostComponentEvidence(
        component="item_price",
        state=LandedCostComponentState.KNOWN,
        amount=Decimal("100"),
        currency="USD",
    )

    result = aggregate_landed_cost_components(
        [
            without_context,
            _component(
                "shipping",
                "20",
            ),
        ]
    )

    assert (
        result.state
        is LandedCostAggregationState.NOT_AGGREGATED
    )
    assert result.total is None


def test_empty_set_is_not_aggregated():
    result = aggregate_landed_cost_components(
        []
    )

    assert (
        result.state
        is LandedCostAggregationState.NOT_AGGREGATED
    )


def test_all_not_applicable_is_not_aggregated():
    result = aggregate_landed_cost_components(
        [
            LandedCostComponentEvidence(
                component="duty",
                state=(
                    LandedCostComponentState.NOT_APPLICABLE
                ),
            ),
            LandedCostComponentEvidence(
                component="tax",
                state=(
                    LandedCostComponentState.NOT_APPLICABLE
                ),
            ),
        ]
    )

    assert (
        result.state
        is LandedCostAggregationState.NOT_AGGREGATED
    )


def test_decimal_precision_is_preserved():
    result = aggregate_landed_cost_components(
        [
            _component(
                "item_price",
                "10.10",
            ),
            _component(
                "shipping",
                "0.20",
            ),
            _component(
                "fee",
                "0.30",
            ),
        ]
    )

    assert result.total == Decimal("10.60")


def test_aggregation_result_is_not_recommendation():
    result = aggregate_landed_cost_components(
        [
            _component(
                "item_price",
                "100",
            ),
            _component(
                "shipping",
                "20",
            ),
        ]
    )

    assert (
        result.state
        is LandedCostAggregationState.AGGREGATED
    )

    reason = result.reason.lower()

    assert "recommend" not in reason
    assert "best" not in reason
    assert "cheapest" not in reason
    assert "optimal" not in reason


def test_result_has_no_route_selection_surface():
    result = aggregate_landed_cost_components(
        [
            _component(
                "item_price",
                "100",
            ),
            _component(
                "shipping",
                "20",
            ),
        ]
    )

    assert not hasattr(
        result,
        "selected_route",
    )

    assert not hasattr(
        result,
        "recommended_route",
    )


def test_quality_vocabulary_is_bounded():
    assert {
        state.value
        for state in LandedCostAggregationQuality
    } == {
        "known",
        "derived",
        "estimated",
    }
