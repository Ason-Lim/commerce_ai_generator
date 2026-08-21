from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.freshness import (
    EvidenceFreshnessState,
)
from app.services.cross_border.shipping import (
    ShippingAvailabilityState,
    ShippingRouteEvidence,
)


class ShippingRouteEvaluationState(str, Enum):
    """
    Canonical bounded shipping-route evaluation vocabulary.

    EVALUABLE means the route evidence can participate in the
    current Cross-Border evaluation.

    NOT_APPLICABLE means route origin/destination does not match
    the current evaluation context.

    NOT_EVALUABLE means evidence applies to the context but cannot
    currently be used for candidate evaluation.

    UNKNOWN means available evidence is insufficient to decide
    evaluability.
    """

    EVALUABLE = "evaluable"
    NOT_APPLICABLE = "not_applicable"
    NOT_EVALUABLE = "not_evaluable"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ShippingRouteEvaluation:
    """
    Immutable bounded shipping-route evaluation result.

    This contract does not select carriers, rank candidate routes,
    optimize logistics, calculate landed cost, book shipments,
    determine regulatory permission, or execute transactions.
    """

    state: ShippingRouteEvaluationState

    route_origin_country: str
    route_destination_country: str

    context_origin_country: str
    context_destination_country: str

    reason: str


def evaluate_shipping_route(
    route: ShippingRouteEvidence,
    context: CrossBorderEvaluationContext,
) -> ShippingRouteEvaluation:
    """
    Determine whether shipping-route evidence is evaluable in the
    current Cross-Border context.

    Evaluation order is intentional:

    1. route/context alignment
    2. availability evidence
    3. freshness evidence
    4. evaluability

    Regulatory permission is outside this contract.
    """

    route_origin = route.origin_country
    route_destination = route.destination_country

    context_origin = context.origin_country
    context_destination = context.destination_country

    if (
        route_origin != context_origin
        or route_destination != context_destination
    ):
        return ShippingRouteEvaluation(
            state=(
                ShippingRouteEvaluationState.NOT_APPLICABLE
            ),
            route_origin_country=route_origin,
            route_destination_country=route_destination,
            context_origin_country=context_origin,
            context_destination_country=context_destination,
            reason=(
                "shipping route origin/destination differs "
                "from evaluation context"
            ),
        )

    if (
        route.availability_state
        is ShippingAvailabilityState.UNKNOWN
    ):
        return ShippingRouteEvaluation(
            state=ShippingRouteEvaluationState.UNKNOWN,
            route_origin_country=route_origin,
            route_destination_country=route_destination,
            context_origin_country=context_origin,
            context_destination_country=context_destination,
            reason="shipping route availability is UNKNOWN",
        )

    if (
        route.availability_state
        is ShippingAvailabilityState.UNAVAILABLE
    ):
        return ShippingRouteEvaluation(
            state=(
                ShippingRouteEvaluationState.NOT_EVALUABLE
            ),
            route_origin_country=route_origin,
            route_destination_country=route_destination,
            context_origin_country=context_origin,
            context_destination_country=context_destination,
            reason="shipping route is unavailable",
        )

    if route.freshness is None:
        return ShippingRouteEvaluation(
            state=ShippingRouteEvaluationState.UNKNOWN,
            route_origin_country=route_origin,
            route_destination_country=route_destination,
            context_origin_country=context_origin,
            context_destination_country=context_destination,
            reason="shipping route freshness is unavailable",
        )

    if (
        route.freshness.state
        is EvidenceFreshnessState.UNKNOWN
    ):
        return ShippingRouteEvaluation(
            state=ShippingRouteEvaluationState.UNKNOWN,
            route_origin_country=route_origin,
            route_destination_country=route_destination,
            context_origin_country=context_origin,
            context_destination_country=context_destination,
            reason="shipping route freshness is UNKNOWN",
        )

    if (
        route.freshness.state
        is EvidenceFreshnessState.STALE
    ):
        return ShippingRouteEvaluation(
            state=(
                ShippingRouteEvaluationState.NOT_EVALUABLE
            ),
            route_origin_country=route_origin,
            route_destination_country=route_destination,
            context_origin_country=context_origin,
            context_destination_country=context_destination,
            reason="shipping route evidence is stale",
        )

    return ShippingRouteEvaluation(
        state=ShippingRouteEvaluationState.EVALUABLE,
        route_origin_country=route_origin,
        route_destination_country=route_destination,
        context_origin_country=context_origin,
        context_destination_country=context_destination,
        reason=(
            "shipping route applies to the evaluation context "
            "and has available fresh evidence"
        ),
    )
