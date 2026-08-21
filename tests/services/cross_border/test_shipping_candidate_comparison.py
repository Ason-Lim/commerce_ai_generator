from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

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
from app.services.cross_border.shipping_candidate_comparison import (
    ShippingCandidateComparisonState,
    ShippingCandidateRelation,
    compare_shipping_candidates,
)
from app.services.cross_border.shipping_comparison import (
    ShippingComparisonDimension,
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
    freshness: EvidenceFreshness | None = None,
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
        freshness=(
            _fresh()
            if freshness is None
            else freshness
        ),
    )


def test_lower_first_cost_is_first_less() -> None:
    result = compare_shipping_candidates(
        [
            _route(cost="10.00"),
            _route(cost="12.00"),
        ],
        _context(),
        ShippingComparisonDimension.COST,
    )

    assert (
        result.state
        is ShippingCandidateComparisonState.COMPARED
    )
    assert (
        result.relation
        is ShippingCandidateRelation.FIRST_LESS
    )
    assert result.first_value == Decimal("10.00")
    assert result.second_value == Decimal("12.00")
    assert result.unit == "USD"


def test_lower_second_cost_is_second_less() -> None:
    result = compare_shipping_candidates(
        [
            _route(cost="15.00"),
            _route(cost="12.00"),
        ],
        _context(),
        ShippingComparisonDimension.COST,
    )

    assert (
        result.relation
        is ShippingCandidateRelation.SECOND_LESS
    )


def test_equal_cost_is_equal() -> None:
    result = compare_shipping_candidates(
        [
            _route(cost="10.00"),
            _route(cost="10.00"),
        ],
        _context(),
        ShippingComparisonDimension.COST,
    )

    assert (
        result.relation
        is ShippingCandidateRelation.EQUAL
    )


def test_lower_first_transit_is_first_less() -> None:
    result = compare_shipping_candidates(
        [
            _route(transit_days=5),
            _route(transit_days=7),
        ],
        _context(),
        ShippingComparisonDimension.TRANSIT_TIME,
    )

    assert (
        result.state
        is ShippingCandidateComparisonState.COMPARED
    )
    assert (
        result.relation
        is ShippingCandidateRelation.FIRST_LESS
    )
    assert result.first_value == 5
    assert result.second_value == 7
    assert result.unit == "days"


def test_lower_second_transit_is_second_less() -> None:
    result = compare_shipping_candidates(
        [
            _route(transit_days=8),
            _route(transit_days=6),
        ],
        _context(),
        ShippingComparisonDimension.TRANSIT_TIME,
    )

    assert (
        result.relation
        is ShippingCandidateRelation.SECOND_LESS
    )


def test_equal_transit_is_equal() -> None:
    result = compare_shipping_candidates(
        [
            _route(transit_days=5),
            _route(transit_days=5),
        ],
        _context(),
        ShippingComparisonDimension.TRANSIT_TIME,
    )

    assert (
        result.relation
        is ShippingCandidateRelation.EQUAL
    )


def test_zero_cost_remains_real_comparable_value() -> None:
    result = compare_shipping_candidates(
        [
            _route(cost="0"),
            _route(cost="10.00"),
        ],
        _context(),
        ShippingComparisonDimension.COST,
    )

    assert (
        result.relation
        is ShippingCandidateRelation.FIRST_LESS
    )
    assert result.first_value == Decimal("0")


def test_missing_cost_is_not_compared() -> None:
    result = compare_shipping_candidates(
        [
            _route(
                cost=None,
                currency=None,
            ),
            _route(cost="10.00"),
        ],
        _context(),
        ShippingComparisonDimension.COST,
    )

    assert (
        result.state
        is ShippingCandidateComparisonState.NOT_COMPARED
    )
    assert result.relation is None
    assert result.first_value is None
    assert result.second_value is None


def test_different_currency_is_not_compared() -> None:
    result = compare_shipping_candidates(
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
        is ShippingCandidateComparisonState.NOT_COMPARED
    )
    assert result.relation is None


def test_missing_transit_is_not_compared() -> None:
    result = compare_shipping_candidates(
        [
            _route(transit_days=None),
            _route(transit_days=5),
        ],
        _context(),
        ShippingComparisonDimension.TRANSIT_TIME,
    )

    assert (
        result.state
        is ShippingCandidateComparisonState.NOT_COMPARED
    )


def test_context_mismatch_is_not_compared() -> None:
    result = compare_shipping_candidates(
        [
            _route(),
            _route(
                destination_country="JP",
            ),
        ],
        _context(),
        ShippingComparisonDimension.COST,
    )

    assert (
        result.state
        is ShippingCandidateComparisonState.NOT_COMPARED
    )


def test_unavailable_route_is_not_compared() -> None:
    result = compare_shipping_candidates(
        [
            _route(),
            _route(
                availability=(
                    ShippingAvailabilityState.UNAVAILABLE
                ),
            ),
        ],
        _context(),
        ShippingComparisonDimension.COST,
    )

    assert (
        result.state
        is ShippingCandidateComparisonState.NOT_COMPARED
    )


def test_one_candidate_is_not_compared() -> None:
    result = compare_shipping_candidates(
        [_route()],
        _context(),
        ShippingComparisonDimension.COST,
    )

    assert (
        result.state
        is ShippingCandidateComparisonState.NOT_COMPARED
    )


def test_three_candidates_are_not_compared() -> None:
    result = compare_shipping_candidates(
        [
            _route(cost="10.00"),
            _route(cost="11.00"),
            _route(cost="12.00"),
        ],
        _context(),
        ShippingComparisonDimension.COST,
    )

    assert (
        result.state
        is ShippingCandidateComparisonState.NOT_COMPARED
    )

    assert "exactly two" in result.reason.lower()


def test_first_less_does_not_mean_recommended() -> None:
    result = compare_shipping_candidates(
        [
            _route(cost="10.00"),
            _route(cost="12.00"),
        ],
        _context(),
        ShippingComparisonDimension.COST,
    )

    assert (
        result.relation
        is ShippingCandidateRelation.FIRST_LESS
    )

    reason = result.reason.lower()

    assert "recommend" not in reason
    assert "best" not in reason
    assert "optimal" not in reason
    assert "select" not in reason


def test_comparison_vocabulary_has_no_ranking_state() -> None:
    values = {
        state.value
        for state in ShippingCandidateRelation
    }

    assert values == {
        "first_less",
        "second_less",
        "equal",
    }

    assert "best" not in values
    assert "winner" not in values
    assert "preferred" not in values
