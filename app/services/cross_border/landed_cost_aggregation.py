from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Iterable

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


class LandedCostAggregationQuality(str, Enum):
    """
    Canonical evidence-quality summary for bounded landed cost.

    KNOWN:
        all arithmetic-bearing components are KNOWN.

    DERIVED:
        at least one component is DERIVED and none are ESTIMATED.

    ESTIMATED:
        at least one arithmetic-bearing component is ESTIMATED.
    """

    KNOWN = "known"
    DERIVED = "derived"
    ESTIMATED = "estimated"


class LandedCostAggregationState(str, Enum):
    AGGREGATED = "aggregated"
    NOT_AGGREGATED = "not_aggregated"


@dataclass(frozen=True)
class LandedCostAggregation:
    """
    Immutable bounded landed-cost aggregation result.

    This result is arithmetic evidence only.

    It does not:
    - convert currency;
    - calculate duty or tax;
    - infer missing fees;
    - rank routes;
    - recommend a purchase path;
    - execute checkout, payment, customs filing, or shipment.
    """

    state: LandedCostAggregationState

    total: Decimal | None
    currency: str | None
    context: CrossBorderEvaluationContext | None

    included_component_count: int
    quality: LandedCostAggregationQuality | None

    reason: str


def aggregate_landed_cost_components(
    components: Iterable[LandedCostComponentEvidence],
) -> LandedCostAggregation:
    """
    Perform bounded arithmetic aggregation over a READY component set.

    Phase 9D readiness remains authoritative.

    Only KNOWN / ESTIMATED / DERIVED components participate in
    arithmetic. NOT_APPLICABLE components are excluded.

    No currency conversion or missing-value inference is performed.
    """

    component_list = tuple(components)

    readiness = evaluate_landed_cost_aggregation_readiness(
        component_list
    )

    if (
        readiness.state
        is not LandedCostAggregationReadinessState.READY
    ):
        return LandedCostAggregation(
            state=LandedCostAggregationState.NOT_AGGREGATED,
            total=None,
            currency=readiness.currency,
            context=readiness.context,
            included_component_count=0,
            quality=None,
            reason=(
                "landed-cost aggregation readiness is "
                f"{readiness.state.value}"
            ),
        )

    arithmetic_states = {
        LandedCostComponentState.KNOWN,
        LandedCostComponentState.ESTIMATED,
        LandedCostComponentState.DERIVED,
    }

    arithmetic_components = [
        component
        for component in component_list
        if component.state in arithmetic_states
    ]

    total = Decimal("0")

    for component in arithmetic_components:
        if component.amount is None:
            raise AssertionError(
                "READY landed-cost component missing amount"
            )

        total += component.amount

    quality = _derive_aggregation_quality(
        arithmetic_components
    )

    return LandedCostAggregation(
        state=LandedCostAggregationState.AGGREGATED,
        total=total,
        currency=readiness.currency,
        context=readiness.context,
        included_component_count=len(
            arithmetic_components
        ),
        quality=quality,
        reason=(
            "landed-cost components aggregated within "
            "validated currency and evaluation context"
        ),
    )


def _derive_aggregation_quality(
    components: Iterable[LandedCostComponentEvidence],
) -> LandedCostAggregationQuality:
    states = {
        component.state
        for component in components
    }

    if LandedCostComponentState.ESTIMATED in states:
        return LandedCostAggregationQuality.ESTIMATED

    if LandedCostComponentState.DERIVED in states:
        return LandedCostAggregationQuality.DERIVED

    return LandedCostAggregationQuality.KNOWN
