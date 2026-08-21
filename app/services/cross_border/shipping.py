from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum

from app.services.cross_border.freshness import (
    EvidenceFreshness,
)
from app.services.cross_border.provenance import (
    EvidenceProvenance,
)


class ShippingRouteType(str, Enum):
    """Provider-independent international shipping route types."""

    DIRECT_INTERNATIONAL = "direct_international"
    FORWARDER = "forwarder"
    MULTI_LEG = "multi_leg"


class ShippingAvailabilityState(str, Enum):
    """
    Canonical bounded shipping-route availability vocabulary.

    UNKNOWN is not equivalent to free shipping or unavailability.
    UNAVAILABLE is not equivalent to regulatory prohibition.
    """

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


def _normalize_country(
    name: str,
    value: str,
) -> str:
    normalized = value.strip().upper()

    if not normalized:
        raise ValueError(
            f"{name} must not be empty"
        )

    return normalized


def _normalize_optional_reference(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    normalized = value.strip()

    if not normalized:
        return None

    return normalized


def _normalize_route_cost(
    value: Decimal | str | int | float | None,
) -> Decimal | None:
    if value is None:
        return None

    if isinstance(value, float):
        value = str(value)

    try:
        cost = Decimal(value)
    except (
        InvalidOperation,
        TypeError,
        ValueError,
    ) as exc:
        raise ValueError(
            "estimated_route_cost must be a valid decimal value"
        ) from exc

    if not cost.is_finite():
        raise ValueError(
            "estimated_route_cost must be finite"
        )

    if cost < 0:
        raise ValueError(
            "estimated_route_cost must be non-negative"
        )

    return cost


@dataclass(frozen=True)
class ShippingRouteEvidence:
    """
    Canonical bounded evidence contract for cross-border routes.

    This contract preserves shipping-route evidence.

    It may represent provider-independent direct international,
    forwarder, or multi-leg route evidence together with carrier
    or forwarder references, estimated transit time, estimated
    route cost, constraints, provenance, and freshness.

    It does not select carriers, optimize routes, book shipments,
    dispatch carriers, execute warehouse operations, determine
    regulatory permission, calculate authoritative landed cost,
    or perform payment or settlement.
    """

    route_type: ShippingRouteType
    origin_country: str
    destination_country: str
    availability_state: ShippingAvailabilityState

    carrier_reference: str | None = None
    forwarder_reference: str | None = None

    estimated_transit_days: int | None = None

    estimated_route_cost: (
        Decimal | str | int | float | None
    ) = None

    route_cost_currency: str | None = None

    constraints: tuple[str, ...] = ()

    provenance: EvidenceProvenance | None = None
    freshness: EvidenceFreshness | None = None

    def __post_init__(self) -> None:
        origin_country = _normalize_country(
            "origin_country",
            self.origin_country,
        )

        destination_country = _normalize_country(
            "destination_country",
            self.destination_country,
        )

        carrier_reference = (
            _normalize_optional_reference(
                self.carrier_reference
            )
        )

        forwarder_reference = (
            _normalize_optional_reference(
                self.forwarder_reference
            )
        )

        route_cost_currency = (
            _normalize_optional_reference(
                self.route_cost_currency
            )
        )

        if route_cost_currency is not None:
            route_cost_currency = (
                route_cost_currency.upper()
            )

        route_cost = _normalize_route_cost(
            self.estimated_route_cost
        )

        if self.estimated_transit_days is not None:
            if self.estimated_transit_days < 0:
                raise ValueError(
                    "estimated_transit_days must be non-negative"
                )

        if (
            route_cost is not None
            and route_cost_currency is None
        ):
            raise ValueError(
                "route_cost_currency is required when "
                "estimated_route_cost is present"
            )

        if (
            route_cost is None
            and route_cost_currency is not None
        ):
            raise ValueError(
                "route_cost_currency requires "
                "estimated_route_cost"
            )

        object.__setattr__(
            self,
            "origin_country",
            origin_country,
        )

        object.__setattr__(
            self,
            "destination_country",
            destination_country,
        )

        object.__setattr__(
            self,
            "carrier_reference",
            carrier_reference,
        )

        object.__setattr__(
            self,
            "forwarder_reference",
            forwarder_reference,
        )

        object.__setattr__(
            self,
            "estimated_route_cost",
            route_cost,
        )

        object.__setattr__(
            self,
            "route_cost_currency",
            route_cost_currency,
        )
