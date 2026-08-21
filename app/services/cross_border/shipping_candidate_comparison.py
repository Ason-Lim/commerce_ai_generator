from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Sequence

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.shipping import (
    ShippingRouteEvidence,
)
from app.services.cross_border.shipping_comparison import (
    ShippingComparisonDimension,
    ShippingComparisonReadinessState,
    evaluate_shipping_comparison_readiness,
)


class ShippingCandidateComparisonState(str, Enum):
    COMPARED = "compared"
    NOT_COMPARED = "not_compared"


class ShippingCandidateRelation(str, Enum):
    """
    Pairwise dimension-bounded relation.

    FIRST_LESS and SECOND_LESS describe only the numeric
    relationship on the requested comparison dimension.

    They do not express recommendation, quality, optimality,
    preference, ranking, or transaction selection.
    """

    FIRST_LESS = "first_less"
    SECOND_LESS = "second_less"
    EQUAL = "equal"


@dataclass(frozen=True)
class ShippingCandidateComparison:
    """
    Immutable pairwise shipping candidate comparison.

    The comparison is restricted to exactly two candidates
    and exactly one comparison dimension.

    This result does not rank a candidate set, recommend a
    route, select a carrier, calculate landed cost, determine
    regulatory permission, or execute shipment activity.
    """

    state: ShippingCandidateComparisonState
    dimension: ShippingComparisonDimension
    relation: ShippingCandidateRelation | None

    first_value: Decimal | int | None
    second_value: Decimal | int | None

    unit: str | None
    reason: str


def compare_shipping_candidates(
    routes: Sequence[ShippingRouteEvidence],
    context: CrossBorderEvaluationContext,
    dimension: ShippingComparisonDimension,
) -> ShippingCandidateComparison:
    """
    Compare exactly two shipping candidates on one dimension.

    Readiness remains authoritative and is evaluated through
    the established Phase 8C comparison-readiness contract.

    COST:
      compares Decimal route-cost evidence in one currency.

    TRANSIT_TIME:
      compares integer estimated transit days.

    A numerically lower value is not interpreted here as a
    better, preferred, recommended, or selected route.
    """

    route_list = tuple(routes)

    if len(route_list) != 2:
        return ShippingCandidateComparison(
            state=ShippingCandidateComparisonState.NOT_COMPARED,
            dimension=dimension,
            relation=None,
            first_value=None,
            second_value=None,
            unit=None,
            reason=(
                "pairwise shipping comparison requires "
                "exactly two candidates"
            ),
        )

    readiness = evaluate_shipping_comparison_readiness(
        route_list,
        context,
        dimension,
    )

    if (
        readiness.state
        is not ShippingComparisonReadinessState.READY
    ):
        return ShippingCandidateComparison(
            state=ShippingCandidateComparisonState.NOT_COMPARED,
            dimension=dimension,
            relation=None,
            first_value=None,
            second_value=None,
            unit=None,
            reason=(
                "shipping comparison readiness is "
                f"{readiness.state.value}"
            ),
        )

    first = route_list[0]
    second = route_list[1]

    if dimension is ShippingComparisonDimension.COST:
        first_value = first.estimated_route_cost
        second_value = second.estimated_route_cost

        if first_value is None or second_value is None:
            raise AssertionError(
                "READY cost comparison missing route cost"
            )

        if (
            first.route_cost_currency is None
            or second.route_cost_currency is None
        ):
            raise AssertionError(
                "READY cost comparison missing currency"
            )

        if (
            first.route_cost_currency
            != second.route_cost_currency
        ):
            raise AssertionError(
                "READY cost comparison currency mismatch"
            )

        relation = _compare_values(
            first_value,
            second_value,
        )

        return ShippingCandidateComparison(
            state=ShippingCandidateComparisonState.COMPARED,
            dimension=dimension,
            relation=relation,
            first_value=first_value,
            second_value=second_value,
            unit=first.route_cost_currency,
            reason=(
                "shipping candidates compared on route cost"
            ),
        )

    if (
        dimension
        is ShippingComparisonDimension.TRANSIT_TIME
    ):
        first_value = first.estimated_transit_days
        second_value = second.estimated_transit_days

        if first_value is None or second_value is None:
            raise AssertionError(
                "READY transit comparison missing transit days"
            )

        relation = _compare_values(
            first_value,
            second_value,
        )

        return ShippingCandidateComparison(
            state=ShippingCandidateComparisonState.COMPARED,
            dimension=dimension,
            relation=relation,
            first_value=first_value,
            second_value=second_value,
            unit="days",
            reason=(
                "shipping candidates compared on transit time"
            ),
        )

    raise ValueError(
        "unsupported shipping comparison dimension: "
        f"{dimension!r}"
    )


def _compare_values(
    first: Decimal | int,
    second: Decimal | int,
) -> ShippingCandidateRelation:
    if first < second:
        return ShippingCandidateRelation.FIRST_LESS

    if second < first:
        return ShippingCandidateRelation.SECOND_LESS

    return ShippingCandidateRelation.EQUAL
