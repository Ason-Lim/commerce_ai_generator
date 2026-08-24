from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.currency import (
    CurrencyRateEvidence,
)
from app.services.cross_border.freshness import (
    EvidenceFreshnessState,
)
from app.services.cross_border.landed_cost_aggregation import (
    LandedCostAggregation,
    LandedCostAggregationState,
)


class LandedCostTemporalEvaluationState(str, Enum):
    """
    Canonical bounded temporal evaluation vocabulary.

    EVALUABLE means the aggregated landed-cost evidence can
    participate in the current evaluation with applicable fresh
    currency evidence.

    NOT_APPLICABLE means the supplied currency evidence does not
    apply to the aggregated landed-cost currency or evaluation
    context.

    NOT_EVALUABLE means applicable evidence is stale or the
    landed cost is not aggregated.

    UNKNOWN means available evidence is insufficient to decide
    temporal evaluability.
    """

    EVALUABLE = "evaluable"
    NOT_APPLICABLE = "not_applicable"
    NOT_EVALUABLE = "not_evaluable"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class LandedCostTemporalEvaluation:
    """
    Immutable bounded temporal evaluation result.

    This contract does not retrieve FX data, calculate FX rates,
    convert amounts, calculate payment fees, re-aggregate landed
    cost, rank routes, recommend purchases, or execute transactions.
    """

    state: LandedCostTemporalEvaluationState
    reason: str


def evaluate_landed_cost_temporal_evidence(
    aggregation: LandedCostAggregation,
    currency_evidence: CurrencyRateEvidence,
    context: CrossBorderEvaluationContext,
) -> LandedCostTemporalEvaluation:
    """
    Determine whether aggregated landed-cost evidence is temporally
    evaluable in the supplied Cross-Border evaluation context.

    Existing CurrencyRateEvidence freshness remains authoritative.
    No FX conversion is performed here.
    """

    if (
        aggregation.state
        is not LandedCostAggregationState.AGGREGATED
    ):
        return LandedCostTemporalEvaluation(
            state=LandedCostTemporalEvaluationState.NOT_EVALUABLE,
            reason="landed cost is not aggregated",
        )

    if aggregation.context is None:
        return LandedCostTemporalEvaluation(
            state=LandedCostTemporalEvaluationState.UNKNOWN,
            reason="landed-cost evaluation context is unavailable",
        )

    if aggregation.context != context:
        return LandedCostTemporalEvaluation(
            state=LandedCostTemporalEvaluationState.NOT_APPLICABLE,
            reason=(
                "landed-cost evaluation context differs from "
                "current evaluation context"
            ),
        )

    if currency_evidence.context != context:
        return LandedCostTemporalEvaluation(
            state=LandedCostTemporalEvaluationState.NOT_APPLICABLE,
            reason=(
                "currency evidence context differs from current "
                "evaluation context"
            ),
        )

    if aggregation.currency is None:
        return LandedCostTemporalEvaluation(
            state=LandedCostTemporalEvaluationState.UNKNOWN,
            reason="landed-cost currency is unavailable",
        )

    pair = currency_evidence.pair

    if (
        aggregation.currency != pair.base_currency
        and aggregation.currency != pair.quote_currency
    ):
        return LandedCostTemporalEvaluation(
            state=LandedCostTemporalEvaluationState.NOT_APPLICABLE,
            reason=(
                "currency evidence pair does not include "
                "landed-cost currency"
            ),
        )

    freshness = currency_evidence.freshness

    if freshness is None:
        return LandedCostTemporalEvaluation(
            state=LandedCostTemporalEvaluationState.UNKNOWN,
            reason="currency evidence freshness is unavailable",
        )

    if freshness.state is EvidenceFreshnessState.UNKNOWN:
        return LandedCostTemporalEvaluation(
            state=LandedCostTemporalEvaluationState.UNKNOWN,
            reason="currency evidence freshness is UNKNOWN",
        )

    if freshness.state is EvidenceFreshnessState.STALE:
        return LandedCostTemporalEvaluation(
            state=LandedCostTemporalEvaluationState.NOT_EVALUABLE,
            reason="currency evidence is stale",
        )

    return LandedCostTemporalEvaluation(
        state=LandedCostTemporalEvaluationState.EVALUABLE,
        reason=(
            "landed-cost evidence applies to the current context "
            "and currency evidence is fresh"
        ),
    )
