from __future__ import annotations

from decimal import Decimal

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.landed_cost import (
    LandedCostComponentEvidence,
    LandedCostComponentState,
)
from app.services.cross_border.landed_cost_readiness import (
    LandedCostAggregationReadinessState,
    evaluate_landed_cost_aggregation_readiness,
)


def _context(
    *,
    origin_country: str = "KR",
    destination_country: str = "US",
) -> CrossBorderEvaluationContext:
    return CrossBorderEvaluationContext(
        origin_country=origin_country,
        destination_country=destination_country,
    )


def _component(
    component: str,
    *,
    state: LandedCostComponentState = (
        LandedCostComponentState.KNOWN
    ),
    amount: str | None = "10.00",
    currency: str | None = "USD",
    context: CrossBorderEvaluationContext | None = None,
) -> LandedCostComponentEvidence:
    if state in {
        LandedCostComponentState.UNKNOWN,
        LandedCostComponentState.UNAVAILABLE,
        LandedCostComponentState.NOT_APPLICABLE,
    }:
        amount = None
        currency = None

    return LandedCostComponentEvidence(
        component=component,
        state=state,
        amount=(
            Decimal(amount)
            if amount is not None
            else None
        ),
        currency=currency,
        context=(
            _context()
            if context is None
            and state
            not in {
                LandedCostComponentState.UNKNOWN,
                LandedCostComponentState.UNAVAILABLE,
                LandedCostComponentState.NOT_APPLICABLE,
            }
            else context
        ),
    )


def test_known_components_same_currency_and_context_are_ready():
    result = evaluate_landed_cost_aggregation_readiness(
        [
            _component(
                "item_price",
                amount="100.00",
            ),
            _component(
                "shipping",
                amount="20.00",
            ),
            _component(
                "duty",
                amount="0",
            ),
        ]
    )

    assert (
        result.state
        is LandedCostAggregationReadinessState.READY
    )
    assert result.currency == "USD"
    assert result.context == _context()
    assert result.arithmetic_component_count == 3


def test_known_zero_is_valid_for_readiness():
    result = evaluate_landed_cost_aggregation_readiness(
        [
            _component(
                "item_price",
                amount="100.00",
            ),
            _component(
                "duty",
                amount="0",
            ),
        ]
    )

    assert (
        result.state
        is LandedCostAggregationReadinessState.READY
    )


def test_estimated_component_can_be_ready():
    result = evaluate_landed_cost_aggregation_readiness(
        [
            _component(
                "item_price",
            ),
            _component(
                "shipping",
                state=(
                    LandedCostComponentState.ESTIMATED
                ),
            ),
        ]
    )

    assert (
        result.state
        is LandedCostAggregationReadinessState.READY
    )


def test_derived_component_can_be_ready():
    result = evaluate_landed_cost_aggregation_readiness(
        [
            _component(
                "item_price",
            ),
            _component(
                "tax",
                state=(
                    LandedCostComponentState.DERIVED
                ),
            ),
        ]
    )

    assert (
        result.state
        is LandedCostAggregationReadinessState.READY
    )


def test_unknown_component_makes_readiness_unknown():
    result = evaluate_landed_cost_aggregation_readiness(
        [
            _component(
                "item_price",
            ),
            _component(
                "duty",
                state=(
                    LandedCostComponentState.UNKNOWN
                ),
            ),
        ]
    )

    assert (
        result.state
        is LandedCostAggregationReadinessState.UNKNOWN
    )


def test_unavailable_component_makes_not_ready():
    result = evaluate_landed_cost_aggregation_readiness(
        [
            _component(
                "item_price",
            ),
            _component(
                "shipping",
                state=(
                    LandedCostComponentState.UNAVAILABLE
                ),
            ),
        ]
    )

    assert (
        result.state
        is LandedCostAggregationReadinessState.NOT_READY
    )


def test_not_applicable_component_is_excluded():
    result = evaluate_landed_cost_aggregation_readiness(
        [
            _component(
                "item_price",
            ),
            _component(
                "shipping",
            ),
            _component(
                "duty",
                state=(
                    LandedCostComponentState.NOT_APPLICABLE
                ),
            ),
        ]
    )

    assert (
        result.state
        is LandedCostAggregationReadinessState.READY
    )
    assert result.applicable_component_count == 2
    assert result.arithmetic_component_count == 2


def test_all_not_applicable_is_not_ready():
    result = evaluate_landed_cost_aggregation_readiness(
        [
            _component(
                "duty",
                state=(
                    LandedCostComponentState.NOT_APPLICABLE
                ),
            ),
            _component(
                "tax",
                state=(
                    LandedCostComponentState.NOT_APPLICABLE
                ),
            ),
        ]
    )

    assert (
        result.state
        is LandedCostAggregationReadinessState.NOT_READY
    )


def test_empty_component_set_is_not_ready():
    result = evaluate_landed_cost_aggregation_readiness(
        []
    )

    assert (
        result.state
        is LandedCostAggregationReadinessState.NOT_READY
    )


def test_currency_mismatch_is_not_ready():
    result = evaluate_landed_cost_aggregation_readiness(
        [
            _component(
                "item_price",
                amount="100",
                currency="USD",
            ),
            _component(
                "shipping",
                amount="20000",
                currency="KRW",
            ),
        ]
    )

    assert (
        result.state
        is LandedCostAggregationReadinessState.NOT_READY
    )
    assert result.currency is None


def test_context_mismatch_is_not_ready():
    result = evaluate_landed_cost_aggregation_readiness(
        [
            _component(
                "item_price",
                context=_context(),
            ),
            _component(
                "shipping",
                context=_context(
                    destination_country="JP",
                ),
            ),
        ]
    )

    assert (
        result.state
        is LandedCostAggregationReadinessState.NOT_READY
    )


def test_all_missing_context_is_unknown():
    first = LandedCostComponentEvidence(
        component="item_price",
        state=LandedCostComponentState.KNOWN,
        amount=Decimal("100"),
        currency="USD",
    )

    second = LandedCostComponentEvidence(
        component="shipping",
        state=LandedCostComponentState.KNOWN,
        amount=Decimal("20"),
        currency="USD",
    )

    result = evaluate_landed_cost_aggregation_readiness(
        [first, second]
    )

    assert (
        result.state
        is LandedCostAggregationReadinessState.UNKNOWN
    )
    assert result.context is None


def test_partial_missing_context_is_unknown():
    first = _component(
        "item_price",
    )

    second = LandedCostComponentEvidence(
        component="shipping",
        state=LandedCostComponentState.KNOWN,
        amount=Decimal("20"),
        currency="USD",
    )

    result = evaluate_landed_cost_aggregation_readiness(
        [first, second]
    )

    assert (
        result.state
        is LandedCostAggregationReadinessState.UNKNOWN
    )
    assert result.context == _context()


def test_unknown_is_not_treated_as_zero():
    result = evaluate_landed_cost_aggregation_readiness(
        [
            _component(
                "item_price",
                amount="100",
            ),
            _component(
                "duty",
                state=(
                    LandedCostComponentState.UNKNOWN
                ),
            ),
        ]
    )

    assert (
        result.state
        is LandedCostAggregationReadinessState.UNKNOWN
    )


def test_ready_does_not_mean_calculated():
    result = evaluate_landed_cost_aggregation_readiness(
        [
            _component(
                "item_price",
                amount="100",
            ),
            _component(
                "shipping",
                amount="20",
            ),
        ]
    )

    assert (
        result.state
        is LandedCostAggregationReadinessState.READY
    )

    assert not hasattr(
        result,
        "total",
    )

    assert not hasattr(
        result,
        "landed_cost",
    )


def test_contract_has_no_calculation_or_recommendation_authority():
    forbidden = {
        "calculate_landed_cost",
        "sum_components",
        "convert_currency",
        "calculate_duty",
        "calculate_tax",
        "recommend_route",
        "select_route",
    }

    public_names = {
        name.lower()
        for name in dir(
            LandedCostAggregationReadinessState
        )
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(
        public_names
    )
