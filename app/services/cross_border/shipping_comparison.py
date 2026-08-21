from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.shipping import (
    ShippingRouteEvidence,
)
from app.services.cross_border.shipping_evaluation import (
    ShippingRouteEvaluationState,
    evaluate_shipping_route,
)


class ShippingComparisonDimension(str, Enum):
    COST = "cost"
    TRANSIT_TIME = "transit_time"


class ShippingComparisonReadinessState(str, Enum):
    READY = "ready"
    NOT_READY = "not_ready"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ShippingComparisonReadiness:
    """
    Bounded comparison-readiness result.

    READY means the supplied routes can be compared on the
    requested dimension.

    This contract does not rank routes, select carriers,
    recommend a route, calculate landed cost, or execute
    shipment activity.
    """

    state: ShippingComparisonReadinessState
    dimension: ShippingComparisonDimension
    candidate_count: int
    reason: str


def evaluate_shipping_comparison_readiness(
    routes: Iterable[ShippingRouteEvidence],
    context: CrossBorderEvaluationContext,
    dimension: ShippingComparisonDimension,
) -> ShippingComparisonReadiness:
    """
    Determine whether at least two routes can be compared on a
    specific dimension.

    Cost comparison requires:
    - EVALUABLE routes
    - route cost present
    - route cost currency present
    - identical route cost currency

    Transit comparison requires:
    - EVALUABLE routes
    - estimated transit days present

    Missing evidence remains UNKNOWN.
    """

    route_list = tuple(routes)

    if len(route_list) < 2:
        return ShippingComparisonReadiness(
            state=(
                ShippingComparisonReadinessState.NOT_READY
            ),
            dimension=dimension,
            candidate_count=len(route_list),
            reason=(
                "at least two shipping routes are required"
            ),
        )

    evaluable_routes = []

    for route in route_list:
        evaluation = evaluate_shipping_route(
            route,
            context,
        )

        if (
            evaluation.state
            is ShippingRouteEvaluationState.EVALUABLE
        ):
            evaluable_routes.append(route)

    if len(evaluable_routes) < 2:
        return ShippingComparisonReadiness(
            state=(
                ShippingComparisonReadinessState.NOT_READY
            ),
            dimension=dimension,
            candidate_count=len(evaluable_routes),
            reason=(
                "fewer than two evaluable shipping routes"
            ),
        )

    if dimension is ShippingComparisonDimension.COST:
        complete_cost_routes = [
            route
            for route in evaluable_routes
            if (
                route.estimated_route_cost is not None
                and route.route_cost_currency is not None
            )
        ]

        if len(complete_cost_routes) < 2:
            return ShippingComparisonReadiness(
                state=ShippingComparisonReadinessState.UNKNOWN,
                dimension=dimension,
                candidate_count=len(
                    complete_cost_routes
                ),
                reason=(
                    "insufficient shipping cost evidence"
                ),
            )

        currencies = {
            route.route_cost_currency
            for route in complete_cost_routes
        }

        if len(currencies) != 1:
            return ShippingComparisonReadiness(
                state=ShippingComparisonReadinessState.NOT_READY,
                dimension=dimension,
                candidate_count=len(
                    complete_cost_routes
                ),
                reason=(
                    "shipping route currencies differ"
                ),
            )

        return ShippingComparisonReadiness(
            state=ShippingComparisonReadinessState.READY,
            dimension=dimension,
            candidate_count=len(
                complete_cost_routes
            ),
            reason=(
                "shipping routes are cost-comparable"
            ),
        )

    if (
        dimension
        is ShippingComparisonDimension.TRANSIT_TIME
    ):
        complete_transit_routes = [
            route
            for route in evaluable_routes
            if route.estimated_transit_days is not None
        ]

        if len(complete_transit_routes) < 2:
            return ShippingComparisonReadiness(
                state=ShippingComparisonReadinessState.UNKNOWN,
                dimension=dimension,
                candidate_count=len(
                    complete_transit_routes
                ),
                reason=(
                    "insufficient transit-time evidence"
                ),
            )

        return ShippingComparisonReadiness(
            state=ShippingComparisonReadinessState.READY,
            dimension=dimension,
            candidate_count=len(
                complete_transit_routes
            ),
            reason=(
                "shipping routes are transit-time comparable"
            ),
        )

    raise ValueError(
        f"unsupported shipping comparison dimension: "
        f"{dimension!r}"
    )
