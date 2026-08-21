from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.landed_cost_aggregation import (
    LandedCostAggregation,
    LandedCostAggregationQuality,
)
from app.services.cross_border.landed_cost_comparison import (
    LandedCostComparisonReadinessState,
    evaluate_landed_cost_comparison_readiness,
)


class LandedCostCandidateComparisonState(str, Enum):
    """
    Canonical execution state for bounded pairwise landed-cost
    comparison.
    """

    COMPARED = "compared"
    NOT_COMPARED = "not_compared"


class LandedCostCandidateRelation(str, Enum):
    """
    Pure numeric relationship between two comparable landed costs.

    FIRST_LESS and SECOND_LESS describe monetary magnitude only.

    They do not express:
    - recommendation;
    - preference;
    - quality;
    - optimality;
    - ranking;
    - route selection.
    """

    FIRST_LESS = "first_less"
    SECOND_LESS = "second_less"
    EQUAL = "equal"


@dataclass(frozen=True)
class LandedCostCandidateComparison:
    """
    Immutable bounded pairwise landed-cost comparison result.

    Quality metadata from both aggregation results is preserved.

    This result does not rank candidate sets, recommend a purchase
    path, select a route, convert currency, calculate duty/tax,
    or execute a transaction.
    """

    state: LandedCostCandidateComparisonState
    relation: LandedCostCandidateRelation | None

    first_total: Decimal | None
    second_total: Decimal | None

    currency: str | None
    context: CrossBorderEvaluationContext | None

    first_quality: LandedCostAggregationQuality | None
    second_quality: LandedCostAggregationQuality | None

    reason: str


def compare_landed_cost_candidates(
    first: LandedCostAggregation,
    second: LandedCostAggregation,
) -> LandedCostCandidateComparison:
    """
    Compare exactly two landed-cost aggregation results.

    Phase 9F comparison readiness remains authoritative.

    A numerically lower total is not interpreted as a recommended,
    preferred, better, or selected candidate.
    """

    readiness = evaluate_landed_cost_comparison_readiness(
        first,
        second,
    )

    if (
        readiness.state
        is not LandedCostComparisonReadinessState.READY
    ):
        return LandedCostCandidateComparison(
            state=(
                LandedCostCandidateComparisonState.NOT_COMPARED
            ),
            relation=None,
            first_total=None,
            second_total=None,
            currency=readiness.currency,
            context=readiness.context,
            first_quality=readiness.first_quality,
            second_quality=readiness.second_quality,
            reason=(
                "landed-cost comparison readiness is "
                f"{readiness.state.value}"
            ),
        )

    if first.total is None or second.total is None:
        raise AssertionError(
            "READY landed-cost comparison missing total"
        )

    relation = _compare_totals(
        first.total,
        second.total,
    )

    return LandedCostCandidateComparison(
        state=LandedCostCandidateComparisonState.COMPARED,
        relation=relation,
        first_total=first.total,
        second_total=second.total,
        currency=readiness.currency,
        context=readiness.context,
        first_quality=readiness.first_quality,
        second_quality=readiness.second_quality,
        reason=(
            "landed-cost candidates compared by bounded "
            "monetary magnitude"
        ),
    )


def _compare_totals(
    first: Decimal,
    second: Decimal,
) -> LandedCostCandidateRelation:
    if first < second:
        return LandedCostCandidateRelation.FIRST_LESS

    if second < first:
        return LandedCostCandidateRelation.SECOND_LESS

    return LandedCostCandidateRelation.EQUAL
