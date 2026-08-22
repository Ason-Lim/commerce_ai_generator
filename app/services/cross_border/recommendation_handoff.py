from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.landed_cost_aggregation import (
    LandedCostAggregationQuality,
)
from app.services.cross_border.landed_cost_bound_readiness import (
    BoundLandedCostReadiness,
    BoundLandedCostReadinessState,
)
from app.services.cross_border.landed_cost_candidate_comparison import (
    LandedCostCandidateRelation,
)
from app.services.cross_border.landed_cost_comparison_binding import (
    BoundLandedCostComparison,
)


@dataclass(frozen=True)
class RecommendationHandoffEvidence:
    """
    Canonical Cross-Border outbound evidence contract.

    This contract packages verified Cross-Border comparison evidence
    for consumption by a downstream decision authority.

    Cross-Border does not own ranking, recommendation, candidate
    selection, user-preference weighting, or transaction execution.
    """

    first_candidate_ref: str
    second_candidate_ref: str

    relation: LandedCostCandidateRelation

    first_total: Decimal
    second_total: Decimal

    currency: str
    context: CrossBorderEvaluationContext

    first_quality: LandedCostAggregationQuality
    second_quality: LandedCostAggregationQuality


def build_recommendation_handoff_evidence(
    *,
    bound: BoundLandedCostComparison,
    readiness: BoundLandedCostReadiness,
) -> RecommendationHandoffEvidence:
    """
    Build outbound Cross-Border evidence for a downstream
    recommendation authority.

    The readiness result must correspond to the supplied bound
    comparison and must be READY.

    This function performs no ranking, recommendation, selection,
    optimization, or transaction execution.
    """

    if (
        readiness.state
        is not BoundLandedCostReadinessState.READY
    ):
        raise ValueError(
            "bound landed-cost evidence is not ready for handoff"
        )

    comparison = bound.comparison

    first_ref = (
        bound.first_candidate.candidate_ref
    )
    second_ref = (
        bound.second_candidate.candidate_ref
    )

    if (
        readiness.first_candidate_ref
        != first_ref
        or readiness.second_candidate_ref
        != second_ref
    ):
        raise ValueError(
            "readiness candidate references do not match "
            "bound comparison"
        )

    if readiness.relation is not comparison.relation:
        raise ValueError(
            "readiness relation does not match "
            "bound comparison"
        )

    if readiness.currency != comparison.currency:
        raise ValueError(
            "readiness currency does not match "
            "bound comparison"
        )

    if readiness.context != comparison.context:
        raise ValueError(
            "readiness context does not match "
            "bound comparison"
        )

    if (
        readiness.first_quality
        is not comparison.first_quality
        or readiness.second_quality
        is not comparison.second_quality
    ):
        raise ValueError(
            "readiness quality metadata does not match "
            "bound comparison"
        )

    if comparison.relation is None:
        raise ValueError(
            "ready comparison relation is missing"
        )

    if (
        comparison.first_total is None
        or comparison.second_total is None
    ):
        raise ValueError(
            "ready comparison totals are missing"
        )

    if comparison.currency is None:
        raise ValueError(
            "ready comparison currency is missing"
        )

    if comparison.context is None:
        raise ValueError(
            "ready comparison context is missing"
        )

    if (
        comparison.first_quality is None
        or comparison.second_quality is None
    ):
        raise ValueError(
            "ready comparison quality metadata is missing"
        )

    return RecommendationHandoffEvidence(
        first_candidate_ref=first_ref,
        second_candidate_ref=second_ref,
        relation=comparison.relation,
        first_total=comparison.first_total,
        second_total=comparison.second_total,
        currency=comparison.currency,
        context=comparison.context,
        first_quality=comparison.first_quality,
        second_quality=comparison.second_quality,
    )
