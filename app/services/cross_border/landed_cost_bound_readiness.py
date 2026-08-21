from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.landed_cost_aggregation import (
    LandedCostAggregationQuality,
)
from app.services.cross_border.landed_cost_candidate_comparison import (
    LandedCostCandidateComparisonState,
    LandedCostCandidateRelation,
)
from app.services.cross_border.landed_cost_comparison_binding import (
    BoundLandedCostComparison,
)


class BoundLandedCostReadinessState(str, Enum):
    """
    Canonical readiness state for bound landed-cost comparison
    evidence.
    """

    READY = "ready"
    NOT_READY = "not_ready"


@dataclass(frozen=True)
class BoundLandedCostReadiness:
    """
    Immutable readiness result for downstream bounded decision use.

    READY means only that the bound comparison evidence is complete.

    It does not mean:
    - winner identified;
    - recommendation authorized;
    - candidate selected;
    - route selected;
    - ranking performed.
    """

    state: BoundLandedCostReadinessState

    first_candidate_ref: str
    second_candidate_ref: str

    relation: LandedCostCandidateRelation | None

    currency: str | None
    context: CrossBorderEvaluationContext | None

    first_quality: LandedCostAggregationQuality | None
    second_quality: LandedCostAggregationQuality | None

    reason: str


def evaluate_bound_landed_cost_readiness(
    bound: BoundLandedCostComparison,
) -> BoundLandedCostReadiness:
    """
    Determine whether bound landed-cost comparison evidence is
    structurally complete for downstream decision-layer consumption.

    This function performs no ranking or recommendation.
    """

    first_ref = (
        bound.first_candidate.candidate_ref
    )

    second_ref = (
        bound.second_candidate.candidate_ref
    )

    comparison = bound.comparison

    if first_ref == second_ref:
        return BoundLandedCostReadiness(
            state=BoundLandedCostReadinessState.NOT_READY,
            first_candidate_ref=first_ref,
            second_candidate_ref=second_ref,
            relation=comparison.relation,
            currency=comparison.currency,
            context=comparison.context,
            first_quality=comparison.first_quality,
            second_quality=comparison.second_quality,
            reason=(
                "candidate references must remain distinct"
            ),
        )

    if (
        comparison.state
        is not LandedCostCandidateComparisonState.COMPARED
    ):
        return BoundLandedCostReadiness(
            state=BoundLandedCostReadinessState.NOT_READY,
            first_candidate_ref=first_ref,
            second_candidate_ref=second_ref,
            relation=None,
            currency=comparison.currency,
            context=comparison.context,
            first_quality=comparison.first_quality,
            second_quality=comparison.second_quality,
            reason=(
                "landed-cost comparison must be COMPARED"
            ),
        )

    if comparison.relation is None:
        return BoundLandedCostReadiness(
            state=BoundLandedCostReadinessState.NOT_READY,
            first_candidate_ref=first_ref,
            second_candidate_ref=second_ref,
            relation=None,
            currency=comparison.currency,
            context=comparison.context,
            first_quality=comparison.first_quality,
            second_quality=comparison.second_quality,
            reason=(
                "landed-cost comparison relation is missing"
            ),
        )

    if (
        comparison.first_total is None
        or comparison.second_total is None
    ):
        return BoundLandedCostReadiness(
            state=BoundLandedCostReadinessState.NOT_READY,
            first_candidate_ref=first_ref,
            second_candidate_ref=second_ref,
            relation=comparison.relation,
            currency=comparison.currency,
            context=comparison.context,
            first_quality=comparison.first_quality,
            second_quality=comparison.second_quality,
            reason=(
                "landed-cost comparison totals are incomplete"
            ),
        )

    if comparison.currency is None:
        return BoundLandedCostReadiness(
            state=BoundLandedCostReadinessState.NOT_READY,
            first_candidate_ref=first_ref,
            second_candidate_ref=second_ref,
            relation=comparison.relation,
            currency=None,
            context=comparison.context,
            first_quality=comparison.first_quality,
            second_quality=comparison.second_quality,
            reason=(
                "landed-cost comparison currency is missing"
            ),
        )

    if comparison.context is None:
        return BoundLandedCostReadiness(
            state=BoundLandedCostReadinessState.NOT_READY,
            first_candidate_ref=first_ref,
            second_candidate_ref=second_ref,
            relation=comparison.relation,
            currency=comparison.currency,
            context=None,
            first_quality=comparison.first_quality,
            second_quality=comparison.second_quality,
            reason=(
                "landed-cost comparison context is missing"
            ),
        )

    if (
        comparison.first_quality is None
        or comparison.second_quality is None
    ):
        return BoundLandedCostReadiness(
            state=BoundLandedCostReadinessState.NOT_READY,
            first_candidate_ref=first_ref,
            second_candidate_ref=second_ref,
            relation=comparison.relation,
            currency=comparison.currency,
            context=comparison.context,
            first_quality=comparison.first_quality,
            second_quality=comparison.second_quality,
            reason=(
                "landed-cost comparison quality metadata "
                "is incomplete"
            ),
        )

    return BoundLandedCostReadiness(
        state=BoundLandedCostReadinessState.READY,
        first_candidate_ref=first_ref,
        second_candidate_ref=second_ref,
        relation=comparison.relation,
        currency=comparison.currency,
        context=comparison.context,
        first_quality=comparison.first_quality,
        second_quality=comparison.second_quality,
        reason=(
            "bound landed-cost comparison evidence is complete"
        ),
    )
