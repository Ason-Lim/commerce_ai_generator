from __future__ import annotations

from dataclasses import dataclass

from app.services.cross_border.landed_cost_aggregation import (
    LandedCostAggregation,
    LandedCostAggregationQuality,
    LandedCostAggregationState,
)
from app.services.cross_border.landed_cost_temporal_evaluation import (
    LandedCostTemporalEvaluation,
    LandedCostTemporalEvaluationState,
)


@dataclass(frozen=True)
class LandedCostEstimateValidityBinding:
    """
    Immutable composition of existing landed-cost authorities.

    This contract introduces no new validity vocabulary.

    Aggregation remains authoritative for:
    - whether a landed cost was aggregated;
    - total / currency / context;
    - KNOWN / DERIVED / ESTIMATED quality.

    Temporal evaluation remains authoritative for:
    - EVALUABLE;
    - NOT_APPLICABLE;
    - NOT_EVALUABLE;
    - UNKNOWN.

    This binding does not reinterpret those states as VALID,
    INVALID, STALE, INCOMPLETE, or any other parallel status.
    """

    aggregation_state: LandedCostAggregationState
    aggregation_quality: LandedCostAggregationQuality | None
    temporal_state: LandedCostTemporalEvaluationState
    aggregation_reason: str
    temporal_reason: str


def bind_landed_cost_estimate_validity(
    aggregation: LandedCostAggregation,
    temporal_evaluation: LandedCostTemporalEvaluation,
) -> LandedCostEstimateValidityBinding:
    """
    Preserve existing landed-cost aggregation and temporal conclusions
    in one bounded downstream-facing result.

    No new inference or state translation is performed.
    """

    return LandedCostEstimateValidityBinding(
        aggregation_state=aggregation.state,
        aggregation_quality=aggregation.quality,
        temporal_state=temporal_evaluation.state,
        aggregation_reason=aggregation.reason,
        temporal_reason=temporal_evaluation.reason,
    )
