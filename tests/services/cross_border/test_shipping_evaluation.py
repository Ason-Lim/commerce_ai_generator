from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import timedelta

import pytest

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
from app.services.cross_border.shipping_evaluation import (
    ShippingRouteEvaluation,
    ShippingRouteEvaluationState,
    evaluate_shipping_route,
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


def _freshness(
    state: EvidenceFreshnessState,
) -> EvidenceFreshness:
    return EvidenceFreshness(
        state=state,
        evidence_at="2026-08-22T00:00:00+09:00",
        age=(
            None
            if state is EvidenceFreshnessState.UNKNOWN
            else timedelta(minutes=5)
        ),
    )


def _route(
    *,
    origin_country: str = "KR",
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
        origin_country=origin_country,
        destination_country=destination_country,
        availability_state=availability,
        freshness=freshness,
    )


def test_evaluation_state_vocabulary() -> None:
    assert {
        item.value
        for item in ShippingRouteEvaluationState
    } == {
        "evaluable",
        "not_applicable",
        "not_evaluable",
        "unknown",
    }


def test_matching_available_fresh_route_is_evaluable() -> None:
    result = evaluate_shipping_route(
        _route(
            availability=(
                ShippingAvailabilityState.AVAILABLE
            ),
            freshness=_freshness(
                EvidenceFreshnessState.FRESH
            ),
        ),
        _context(),
    )

    assert (
        result.state
        is ShippingRouteEvaluationState.EVALUABLE
    )


def test_origin_mismatch_is_not_applicable() -> None:
    result = evaluate_shipping_route(
        _route(
            origin_country="JP",
            freshness=_freshness(
                EvidenceFreshnessState.FRESH
            ),
        ),
        _context(
            origin_country="KR",
        ),
    )

    assert (
        result.state
        is ShippingRouteEvaluationState.NOT_APPLICABLE
    )


def test_destination_mismatch_is_not_applicable() -> None:
    result = evaluate_shipping_route(
        _route(
            destination_country="JP",
            freshness=_freshness(
                EvidenceFreshnessState.FRESH
            ),
        ),
        _context(
            destination_country="US",
        ),
    )

    assert (
        result.state
        is ShippingRouteEvaluationState.NOT_APPLICABLE
    )


def test_unknown_availability_is_unknown() -> None:
    result = evaluate_shipping_route(
        _route(
            availability=(
                ShippingAvailabilityState.UNKNOWN
            ),
            freshness=_freshness(
                EvidenceFreshnessState.FRESH
            ),
        ),
        _context(),
    )

    assert (
        result.state
        is ShippingRouteEvaluationState.UNKNOWN
    )


def test_unavailable_route_is_not_evaluable() -> None:
    result = evaluate_shipping_route(
        _route(
            availability=(
                ShippingAvailabilityState.UNAVAILABLE
            ),
            freshness=_freshness(
                EvidenceFreshnessState.FRESH
            ),
        ),
        _context(),
    )

    assert (
        result.state
        is ShippingRouteEvaluationState.NOT_EVALUABLE
    )


def test_missing_freshness_is_unknown() -> None:
    result = evaluate_shipping_route(
        _route(
            availability=(
                ShippingAvailabilityState.AVAILABLE
            ),
            freshness=None,
        ),
        _context(),
    )

    assert (
        result.state
        is ShippingRouteEvaluationState.UNKNOWN
    )


def test_unknown_freshness_is_unknown() -> None:
    result = evaluate_shipping_route(
        _route(
            freshness=_freshness(
                EvidenceFreshnessState.UNKNOWN
            ),
        ),
        _context(),
    )

    assert (
        result.state
        is ShippingRouteEvaluationState.UNKNOWN
    )


def test_stale_route_is_not_evaluable() -> None:
    result = evaluate_shipping_route(
        _route(
            freshness=_freshness(
                EvidenceFreshnessState.STALE
            ),
        ),
        _context(),
    )

    assert (
        result.state
        is ShippingRouteEvaluationState.NOT_EVALUABLE
    )


def test_not_applicable_is_distinct_from_unavailable() -> None:
    not_applicable = evaluate_shipping_route(
        _route(
            destination_country="JP",
            freshness=_freshness(
                EvidenceFreshnessState.FRESH
            ),
        ),
        _context(),
    )

    unavailable = evaluate_shipping_route(
        _route(
            availability=(
                ShippingAvailabilityState.UNAVAILABLE
            ),
            freshness=_freshness(
                EvidenceFreshnessState.FRESH
            ),
        ),
        _context(),
    )

    assert (
        not_applicable.state
        is ShippingRouteEvaluationState.NOT_APPLICABLE
    )

    assert (
        unavailable.state
        is ShippingRouteEvaluationState.NOT_EVALUABLE
    )


def test_not_evaluable_is_not_regulatory_prohibition() -> None:
    result = evaluate_shipping_route(
        _route(
            availability=(
                ShippingAvailabilityState.UNAVAILABLE
            ),
            freshness=_freshness(
                EvidenceFreshnessState.FRESH
            ),
        ),
        _context(),
    )

    assert (
        result.state
        is ShippingRouteEvaluationState.NOT_EVALUABLE
    )

    assert "prohibit" not in result.reason.lower()
    assert "illegal" not in result.reason.lower()


def test_evaluable_does_not_mean_best_route() -> None:
    result = evaluate_shipping_route(
        _route(
            freshness=_freshness(
                EvidenceFreshnessState.FRESH
            ),
        ),
        _context(),
    )

    assert (
        result.state
        is ShippingRouteEvaluationState.EVALUABLE
    )

    assert "best" not in result.reason.lower()
    assert "optimal" not in result.reason.lower()


def test_context_countries_are_preserved() -> None:
    result = evaluate_shipping_route(
        _route(
            freshness=_freshness(
                EvidenceFreshnessState.FRESH
            ),
        ),
        _context(),
    )

    assert result.route_origin_country == "KR"
    assert result.route_destination_country == "US"
    assert result.context_origin_country == "KR"
    assert result.context_destination_country == "US"


def test_evaluation_result_is_immutable() -> None:
    result = ShippingRouteEvaluation(
        state=ShippingRouteEvaluationState.EVALUABLE,
        route_origin_country="KR",
        route_destination_country="US",
        context_origin_country="KR",
        context_destination_country="US",
        reason="test",
    )

    with pytest.raises(FrozenInstanceError):
        result.state = (
            ShippingRouteEvaluationState.NOT_EVALUABLE
        )


def test_contract_exposes_no_route_execution_authority() -> None:
    forbidden = {
        "select_carrier",
        "optimize_route",
        "book_shipment",
        "dispatch_carrier",
        "calculate_landed_cost",
        "calculate_duty",
    }

    public_names = {
        name.lower()
        for name in dir(
            ShippingRouteEvaluation
        )
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(
        public_names
    )
