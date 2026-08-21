from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.landed_cost_aggregation import (
    LandedCostAggregation,
    LandedCostAggregationQuality,
    LandedCostAggregationState,
)


class LandedCostComparisonReadinessState(str, Enum):
    """
    Canonical readiness state for pairwise landed-cost comparison.
    """

    READY = "ready"
    NOT_READY = "not_ready"


@dataclass(frozen=True)
class LandedCostComparisonReadiness:
    """
    Immutable pairwise landed-cost comparison readiness result.

    This contract does not compare totals and does not determine
    cheaper, better, preferred, optimal, or recommended candidates.
    """

    state: LandedCostComparisonReadinessState

    currency: str | None
    context: CrossBorderEvaluationContext | None

    first_quality: LandedCostAggregationQuality | None
    second_quality: LandedCostAggregationQuality | None

    reason: str


def evaluate_landed_cost_comparison_readiness(
    first: LandedCostAggregation,
    second: LandedCostAggregation,
) -> LandedCostComparisonReadiness:
    """
    Determine whether two bounded landed-cost aggregation results
    are structurally comparable.

    Requirements:
    - both must be AGGREGATED;
    - both must contain totals;
    - both must contain the same currency;
    - both must contain the same evaluation context.

    Evidence-quality differences are preserved rather than hidden.
    """

    if (
        first.state
        is not LandedCostAggregationState.AGGREGATED
        or second.state
        is not LandedCostAggregationState.AGGREGATED
    ):
        return LandedCostComparisonReadiness(
            state=LandedCostComparisonReadinessState.NOT_READY,
            currency=None,
            context=None,
            first_quality=first.quality,
            second_quality=second.quality,
            reason=(
                "both landed-cost results must be AGGREGATED"
            ),
        )

    if first.total is None or second.total is None:
        return LandedCostComparisonReadiness(
            state=LandedCostComparisonReadinessState.NOT_READY,
            currency=None,
            context=None,
            first_quality=first.quality,
            second_quality=second.quality,
            reason=(
                "both landed-cost results must contain totals"
            ),
        )

    if (
        first.currency is None
        or second.currency is None
        or first.currency != second.currency
    ):
        return LandedCostComparisonReadiness(
            state=LandedCostComparisonReadinessState.NOT_READY,
            currency=None,
            context=None,
            first_quality=first.quality,
            second_quality=second.quality,
            reason=(
                "landed-cost currencies are incompatible"
            ),
        )

    if (
        first.context is None
        or second.context is None
        or first.context != second.context
    ):
        return LandedCostComparisonReadiness(
            state=LandedCostComparisonReadinessState.NOT_READY,
            currency=first.currency,
            context=None,
            first_quality=first.quality,
            second_quality=second.quality,
            reason=(
                "landed-cost evaluation contexts are incompatible"
            ),
        )

    return LandedCostComparisonReadiness(
        state=LandedCostComparisonReadinessState.READY,
        currency=first.currency,
        context=first.context,
        first_quality=first.quality,
        second_quality=second.quality,
        reason=(
            "landed-cost results are ready for bounded "
            "pairwise comparison"
        ),
    )
