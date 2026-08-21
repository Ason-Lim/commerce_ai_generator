from dataclasses import FrozenInstanceError
from datetime import timedelta
from decimal import Decimal

import pytest

from app.services.cross_border.freshness import (
    EvidenceFreshness,
    EvidenceFreshnessState,
)
from app.services.cross_border.provenance import (
    EvidenceProvenance,
)
from app.services.cross_border.shipping import (
    ShippingAvailabilityState,
    ShippingRouteEvidence,
    ShippingRouteType,
)


def _provenance() -> EvidenceProvenance:
    return EvidenceProvenance(
        source_id="shipping-source-001",
        source_type="shipping_route",
        record_id="shipping-record-001",
    )


def test_direct_international_shipping_evidence() -> None:
    evidence = ShippingRouteEvidence(
        route_type=ShippingRouteType.DIRECT_INTERNATIONAL,
        origin_country="kr",
        destination_country="us",
        availability_state=ShippingAvailabilityState.AVAILABLE,
        carrier_reference="carrier-reference",
        estimated_transit_days=5,
        estimated_route_cost="25.00",
        route_cost_currency="usd",
        provenance=_provenance(),
    )

    assert (
        evidence.route_type
        is ShippingRouteType.DIRECT_INTERNATIONAL
    )
    assert (
        evidence.availability_state
        is ShippingAvailabilityState.AVAILABLE
    )
    assert evidence.origin_country == "KR"
    assert evidence.destination_country == "US"
    assert (
        evidence.estimated_route_cost
        == Decimal("25.00")
    )
    assert evidence.route_cost_currency == "USD"


def test_forwarder_shipping_evidence() -> None:
    evidence = ShippingRouteEvidence(
        route_type=ShippingRouteType.FORWARDER,
        origin_country="KR",
        destination_country="US",
        availability_state=ShippingAvailabilityState.AVAILABLE,
        forwarder_reference="forwarder-reference",
    )

    assert (
        evidence.forwarder_reference
        == "forwarder-reference"
    )
    assert evidence.carrier_reference is None


def test_multi_leg_shipping_evidence() -> None:
    evidence = ShippingRouteEvidence(
        route_type=ShippingRouteType.MULTI_LEG,
        origin_country="KR",
        destination_country="DE",
        availability_state=ShippingAvailabilityState.UNKNOWN,
        constraints=(
            "route evidence incomplete",
        ),
    )

    assert (
        evidence.route_type
        is ShippingRouteType.MULTI_LEG
    )

    assert evidence.constraints == (
        "route evidence incomplete",
    )


def test_unknown_shipping_does_not_mean_free_shipping() -> None:
    evidence = ShippingRouteEvidence(
        route_type=ShippingRouteType.DIRECT_INTERNATIONAL,
        origin_country="KR",
        destination_country="US",
        availability_state=ShippingAvailabilityState.UNKNOWN,
    )

    assert evidence.estimated_route_cost is None
    assert evidence.route_cost_currency is None


def test_unavailable_is_distinct_from_unknown() -> None:
    unavailable = ShippingRouteEvidence(
        route_type=ShippingRouteType.DIRECT_INTERNATIONAL,
        origin_country="KR",
        destination_country="US",
        availability_state=ShippingAvailabilityState.UNAVAILABLE,
    )

    unknown = ShippingRouteEvidence(
        route_type=ShippingRouteType.DIRECT_INTERNATIONAL,
        origin_country="KR",
        destination_country="US",
        availability_state=ShippingAvailabilityState.UNKNOWN,
    )

    assert (
        unavailable.availability_state
        != unknown.availability_state
    )


def test_shipping_contract_has_no_prohibited_state() -> None:
    values = {
        state.value
        for state in ShippingAvailabilityState
    }

    assert "prohibited" not in values


@pytest.mark.parametrize(
    (
        "origin_country",
        "destination_country",
    ),
    [
        ("", "US"),
        ("   ", "US"),
        ("KR", ""),
        ("KR", "   "),
    ],
)
def test_country_context_must_not_be_empty(
    origin_country: str,
    destination_country: str,
) -> None:
    with pytest.raises(ValueError):
        ShippingRouteEvidence(
            route_type=(
                ShippingRouteType.DIRECT_INTERNATIONAL
            ),
            origin_country=origin_country,
            destination_country=destination_country,
            availability_state=(
                ShippingAvailabilityState.UNKNOWN
            ),
        )


def test_negative_transit_days_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="estimated_transit_days",
    ):
        ShippingRouteEvidence(
            route_type=(
                ShippingRouteType.DIRECT_INTERNATIONAL
            ),
            origin_country="KR",
            destination_country="US",
            availability_state=(
                ShippingAvailabilityState.AVAILABLE
            ),
            estimated_transit_days=-1,
        )


@pytest.mark.parametrize(
    "route_cost",
    [
        "-1",
        -1,
        -1.0,
        "NaN",
        "Infinity",
        "-Infinity",
        "not-a-cost",
    ],
)
def test_invalid_route_cost_rejected(
    route_cost,
) -> None:
    with pytest.raises(ValueError):
        ShippingRouteEvidence(
            route_type=(
                ShippingRouteType.DIRECT_INTERNATIONAL
            ),
            origin_country="KR",
            destination_country="US",
            availability_state=(
                ShippingAvailabilityState.AVAILABLE
            ),
            estimated_route_cost=route_cost,
            route_cost_currency="USD",
        )


def test_route_cost_requires_currency() -> None:
    with pytest.raises(
        ValueError,
        match="route_cost_currency is required",
    ):
        ShippingRouteEvidence(
            route_type=(
                ShippingRouteType.DIRECT_INTERNATIONAL
            ),
            origin_country="KR",
            destination_country="US",
            availability_state=(
                ShippingAvailabilityState.AVAILABLE
            ),
            estimated_route_cost="25.00",
        )


def test_currency_without_route_cost_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="route_cost_currency requires",
    ):
        ShippingRouteEvidence(
            route_type=(
                ShippingRouteType.DIRECT_INTERNATIONAL
            ),
            origin_country="KR",
            destination_country="US",
            availability_state=(
                ShippingAvailabilityState.UNKNOWN
            ),
            route_cost_currency="USD",
        )


def test_zero_shipping_cost_is_real_zero_not_unknown() -> None:
    evidence = ShippingRouteEvidence(
        route_type=ShippingRouteType.DIRECT_INTERNATIONAL,
        origin_country="KR",
        destination_country="US",
        availability_state=ShippingAvailabilityState.AVAILABLE,
        estimated_route_cost="0",
        route_cost_currency="USD",
    )

    assert evidence.estimated_route_cost == Decimal("0")
    assert (
        evidence.availability_state
        is ShippingAvailabilityState.AVAILABLE
    )


def test_provenance_uses_canonical_contract() -> None:
    provenance = _provenance()

    evidence = ShippingRouteEvidence(
        route_type=ShippingRouteType.DIRECT_INTERNATIONAL,
        origin_country="KR",
        destination_country="US",
        availability_state=ShippingAvailabilityState.AVAILABLE,
        provenance=provenance,
    )

    assert evidence.provenance is provenance
    assert (
        evidence.provenance.source_id
        == "shipping-source-001"
    )


def test_freshness_uses_canonical_contract() -> None:
    freshness = EvidenceFreshness(
        state=EvidenceFreshnessState.FRESH,
        evidence_at="2026-08-22T00:00:00+09:00",
        age=timedelta(minutes=5),
    )

    evidence = ShippingRouteEvidence(
        route_type=ShippingRouteType.DIRECT_INTERNATIONAL,
        origin_country="KR",
        destination_country="US",
        availability_state=ShippingAvailabilityState.AVAILABLE,
        freshness=freshness,
    )

    assert evidence.freshness is freshness


def test_shipping_route_evidence_is_immutable() -> None:
    evidence = ShippingRouteEvidence(
        route_type=ShippingRouteType.DIRECT_INTERNATIONAL,
        origin_country="KR",
        destination_country="US",
        availability_state=ShippingAvailabilityState.UNKNOWN,
    )

    with pytest.raises(FrozenInstanceError):
        evidence.destination_country = "JP"
