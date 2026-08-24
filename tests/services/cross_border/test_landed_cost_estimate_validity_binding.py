from decimal import Decimal

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.landed_cost_aggregation import (
    LandedCostAggregation,
    LandedCostAggregationQuality,
    LandedCostAggregationState,
)
from app.services.cross_border.landed_cost_estimate_validity_binding import (
    LandedCostEstimateValidityBinding,
    bind_landed_cost_estimate_validity,
)
from app.services.cross_border.landed_cost_temporal_evaluation import (
    LandedCostTemporalEvaluation,
    LandedCostTemporalEvaluationState,
)


def _context() -> CrossBorderEvaluationContext:
    return CrossBorderEvaluationContext(
        origin_country="KR",
        destination_country="US",
    )


def test_binding_preserves_aggregated_estimated_evaluable_states():
    context = _context()

    aggregation = LandedCostAggregation(
        state=LandedCostAggregationState.AGGREGATED,
        total=Decimal("125.00"),
        currency="USD",
        context=context,
        included_component_count=4,
        quality=LandedCostAggregationQuality.ESTIMATED,
        reason="aggregation reason",
    )

    temporal = LandedCostTemporalEvaluation(
        state=LandedCostTemporalEvaluationState.EVALUABLE,
        reason="temporal reason",
    )

    result = bind_landed_cost_estimate_validity(
        aggregation,
        temporal,
    )

    assert isinstance(
        result,
        LandedCostEstimateValidityBinding,
    )
    assert (
        result.aggregation_state
        is LandedCostAggregationState.AGGREGATED
    )
    assert (
        result.aggregation_quality
        is LandedCostAggregationQuality.ESTIMATED
    )
    assert (
        result.temporal_state
        is LandedCostTemporalEvaluationState.EVALUABLE
    )
    assert result.aggregation_reason == "aggregation reason"
    assert result.temporal_reason == "temporal reason"


def test_binding_preserves_not_aggregated_and_not_evaluable():
    aggregation = LandedCostAggregation(
        state=LandedCostAggregationState.NOT_AGGREGATED,
        total=None,
        currency=None,
        context=None,
        included_component_count=0,
        quality=None,
        reason="not aggregated",
    )

    temporal = LandedCostTemporalEvaluation(
        state=LandedCostTemporalEvaluationState.NOT_EVALUABLE,
        reason="not evaluable",
    )

    result = bind_landed_cost_estimate_validity(
        aggregation,
        temporal,
    )

    assert (
        result.aggregation_state
        is LandedCostAggregationState.NOT_AGGREGATED
    )
    assert result.aggregation_quality is None
    assert (
        result.temporal_state
        is LandedCostTemporalEvaluationState.NOT_EVALUABLE
    )


def test_binding_preserves_unknown_temporal_state():
    aggregation = LandedCostAggregation(
        state=LandedCostAggregationState.AGGREGATED,
        total=Decimal("0"),
        currency="USD",
        context=_context(),
        included_component_count=1,
        quality=LandedCostAggregationQuality.KNOWN,
        reason="aggregated",
    )

    temporal = LandedCostTemporalEvaluation(
        state=LandedCostTemporalEvaluationState.UNKNOWN,
        reason="freshness unavailable",
    )

    result = bind_landed_cost_estimate_validity(
        aggregation,
        temporal,
    )

    assert (
        result.temporal_state
        is LandedCostTemporalEvaluationState.UNKNOWN
    )
    assert result.temporal_reason == "freshness unavailable"


def test_binding_preserves_not_applicable_temporal_state():
    aggregation = LandedCostAggregation(
        state=LandedCostAggregationState.AGGREGATED,
        total=Decimal("10"),
        currency="USD",
        context=_context(),
        included_component_count=1,
        quality=LandedCostAggregationQuality.DERIVED,
        reason="aggregated",
    )

    temporal = LandedCostTemporalEvaluation(
        state=LandedCostTemporalEvaluationState.NOT_APPLICABLE,
        reason="different context",
    )

    result = bind_landed_cost_estimate_validity(
        aggregation,
        temporal,
    )

    assert (
        result.aggregation_quality
        is LandedCostAggregationQuality.DERIVED
    )
    assert (
        result.temporal_state
        is LandedCostTemporalEvaluationState.NOT_APPLICABLE
    )


def test_binding_does_not_expose_parallel_validity_state():
    fields = LandedCostEstimateValidityBinding.__dataclass_fields__

    assert "state" not in fields
    assert "validity" not in fields
    assert "validity_state" not in fields
    assert "is_valid" not in fields
    assert "is_stale" not in fields
    assert "is_complete" not in fields
