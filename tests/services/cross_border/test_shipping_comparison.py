from __future__ import annotations

from datetime import timedelta

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.freshness import (
    EvidenceFreshness,
    EvidenceFreshnessState,
)
from app.services.cross_border.shipping import (
    ShippingAvailabilityState,
    ShippingRouteEvidence,
    ShippingRouteType,
)
from app.services.cross_border.shipping_comparison import (
    ShippingComparisonDimension,
    ShippingComparisonReadinessState,
    evaluate_shipping_comparison_readiness,
)


def _context() -> CrossBorderEvaluationContext:
    return CrossBorderEvaluationContext(
        origin_country="KR",
        destination_country="US",
    )


def _fresh() -> EvidenceFreshness:
    return EvidenceFreshness(
        state=EvidenceFreshnessState.FRESH,
        evidence_at="2026-08-22T00:00:00+09:00",
        age=timedelta(minutes=5),
    )


def _route(
    *,
    cost: str | None = "10.00",
    currency: str | None = "USD",
    transit_days: int | None = 5,
    destination_country: str = "US",
    availability: ShippingAvailabilityState = (
        ShippingAvailabilityState.AVAILABLE
    ),
) -> ShippingRouteEvidence:
    return ShippingRouteEvidence(
        route_type=(
            ShippingRouteType.DIRECT_INTERNATIONAL
        ),
        origin_country="KR",
        destination_country=destination_country,
        availability_state=availability,
        estimated_route_cost=cost,
        route_cost_currency=currency,
        estimated_transit_days=transit_days,
        freshness=_fresh(),
    )


def test_two_cost_complete_routes_are_ready() -> None:
    result = evaluate_shipping_comparison_readiness(
        [
            _route(cost="10.00"),
            _route(cost="12.00"),
        ],
        _context(),
        ShippingComparisonDimension.COST,
    )

    assert (
        result.state
        is ShippingComparisonReadinessState.READY
    )
    assert result.candidate_count == 2


def test_two_transit_complete_routes_are_ready() -> None:
    result = evaluate_shipping_comparison_readiness(
        [
            _route(transit_days=5),
            _route(transit_days=7),
        ],
        _context(),
        ShippingComparisonDimension.TRANSIT_TIME,
    )

    assert (
        result.state
        is ShippingComparisonReadinessState.READY
    )


def test_single_route_is_not_ready() -> None:
    result = evaluate_shipping_comparison_readiness(
        [_route()],
        _context(),
        ShippingComparisonDimension.COST,
    )

    assert (
        result.state
        is ShippingComparisonReadinessState.NOT_READY
    )


def test_context_mismatch_route_is_excluded() -> None:
    result = evaluate_shipping_comparison_readiness(
        [
            _route(),
            _route(destination_country="JP"),
        ],
        _context(),
        ShippingComparisonDimension.COST,
    )

    assert (
        result.state
        is ShippingComparisonReadinessState.NOT_READY
    )
    assert result.candidate_count == 1


def test_unavailable_route_is_excluded() -> None:
    result = evaluate_shipping_comparison_readiness(
        [
            _route(),
            _route(
                availability=(
                    ShippingAvailabilityState.UNAVAILABLE
                )
            ),
        ],
        _context(),
        ShippingComparisonDimension.COST,
    )

    assert (
        result.state
        is ShippingComparisonReadinessState.NOT_READY
    )


def test_missing_cost_evidence_is_unknown() -> None:
    result = evaluate_shipping_comparison_readiness(
        [
            _route(cost=None, currency=None),
            _route(cost="12.00"),
        ],
        _context(),
        ShippingComparisonDimension.COST,
    )

    assert (
        result.state
        is ShippingComparisonReadinessState.UNKNOWN
    )


def test_different_cost_currencies_are_not_ready() -> None:
    result = evaluate_shipping_comparison_readiness(
        [
            _route(
                cost="10.00",
                currency="USD",
            ),
            _route(
                cost="12000",
                currency="KRW",
            ),
        ],
        _context(),
        ShippingComparisonDimension.COST,
    )

    assert (
        result.state
        is ShippingComparisonReadinessState.NOT_READY
    )


def test_missing_transit_evidence_is_unknown() -> None:
    result = evaluate_shipping_comparison_readiness(
        [
            _route(transit_days=None),
            _route(transit_days=5),
        ],
        _context(),
        ShippingComparisonDimension.TRANSIT_TIME,
    )

    assert (
        result.state
        is ShippingComparisonReadinessState.UNKNOWN
    )


def test_missing_cost_does_not_block_transit_comparison() -> None:
    result = evaluate_shipping_comparison_readiness(
        [
            _route(
                cost=None,
                currency=None,
                transit_days=5,
            ),
            _route(
                cost=None,
                currency=None,
                transit_days=7,
            ),
        ],
        _context(),
        ShippingComparisonDimension.TRANSIT_TIME,
    )

    assert (
        result.state
        is ShippingComparisonReadinessState.READY
    )


def test_missing_transit_does_not_block_cost_comparison() -> None:
    result = evaluate_shipping_comparison_readiness(
        [
            _route(
                cost="10.00",
                transit_days=None,
            ),
            _route(
                cost="12.00",
                transit_days=None,
            ),
        ],
        _context(),
        ShippingComparisonDimension.COST,
    )

    assert (
        result.state
        is ShippingComparisonReadinessState.READY
    )


def test_zero_cost_is_real_cost_evidence() -> None:
    result = evaluate_shipping_comparison_readiness(
        [
            _route(cost="0"),
            _route(cost="10.00"),
        ],
        _context(),
        ShippingComparisonDimension.COST,
    )

    assert (
        result.state
        is ShippingComparisonReadinessState.READY
    )


def test_ready_does_not_mean_best_route() -> None:
    result = evaluate_shipping_comparison_readiness(
        [
            _route(cost="10.00"),
            _route(cost="12.00"),
        ],
        _context(),
        ShippingComparisonDimension.COST,
    )

    assert (
        result.state
        is ShippingComparisonReadinessState.READY
    )

    assert "best" not in result.reason.lower()
    assert "optimal" not in result.reason.lower()


def test_comparison_contract_has_no_selection_authority() -> None:
    forbidden = {
        "select_carrier",
        "recommend_route",
        "optimize_route",
        "book_shipment",
        "calculate_landed_cost",
    }

    public_names = {
        name.lower()
        for name in dir(
            ShippingComparisonReadinessState
        )
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(
        public_names
    )
