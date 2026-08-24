from decimal import Decimal

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.currency import (
    CurrencyPair,
    CurrencyRateEvidence,
)
from app.services.cross_border.freshness import (
    EvidenceFreshness,
    EvidenceFreshnessState,
)
from app.services.cross_border.landed_cost_aggregation import (
    LandedCostAggregation,
    LandedCostAggregationQuality,
    LandedCostAggregationState,
)
from app.services.cross_border.landed_cost_temporal_evaluation import (
    LandedCostTemporalEvaluationState,
    evaluate_landed_cost_temporal_evidence,
)
from app.services.cross_border.models import (
    CrossBorderEvidence,
    EvidenceState,
)
from app.services.cross_border.provenance import (
    EvidenceProvenance,
)


def _context(
    *,
    destination_country: str = "US",
) -> CrossBorderEvaluationContext:
    return CrossBorderEvaluationContext(
        origin_country="KR",
        destination_country=destination_country,
    )


def _aggregation(
    *,
    context=None,
    currency="USD",
    state=LandedCostAggregationState.AGGREGATED,
):
    return LandedCostAggregation(
        state=state,
        total=(
            Decimal("125.00")
            if state is LandedCostAggregationState.AGGREGATED
            else None
        ),
        currency=currency,
        context=context if context is not None else _context(),
        included_component_count=3 if state is LandedCostAggregationState.AGGREGATED else 0,
        quality=(
            LandedCostAggregationQuality.KNOWN
            if state is LandedCostAggregationState.AGGREGATED
            else None
        ),
        reason="test aggregation",
    )


def _currency_evidence(
    *,
    context=None,
    base_currency="USD",
    quote_currency="KRW",
    freshness_state=EvidenceFreshnessState.FRESH,
    freshness=True,
):
    return CurrencyRateEvidence(
        pair=CurrencyPair(
            base_currency=base_currency,
            quote_currency=quote_currency,
        ),
        evidence=CrossBorderEvidence(
            state=EvidenceState.OBSERVED,
        ),
        provenance=EvidenceProvenance(
            source_id="fx-source-001",
            source_type="currency_rate",
        ),
        context=context if context is not None else _context(),
        rate=Decimal("1380.25"),
        freshness=(
            EvidenceFreshness(
                state=freshness_state,
            )
            if freshness
            else None
        ),
    )


def test_fresh_applicable_currency_evidence_is_evaluable():
    result = evaluate_landed_cost_temporal_evidence(
        _aggregation(),
        _currency_evidence(),
        _context(),
    )

    assert (
        result.state
        is LandedCostTemporalEvaluationState.EVALUABLE
    )


def test_stale_currency_evidence_is_not_evaluable():
    result = evaluate_landed_cost_temporal_evidence(
        _aggregation(),
        _currency_evidence(
            freshness_state=EvidenceFreshnessState.STALE,
        ),
        _context(),
    )

    assert (
        result.state
        is LandedCostTemporalEvaluationState.NOT_EVALUABLE
    )


def test_unknown_currency_freshness_is_unknown():
    result = evaluate_landed_cost_temporal_evidence(
        _aggregation(),
        _currency_evidence(
            freshness_state=EvidenceFreshnessState.UNKNOWN,
        ),
        _context(),
    )

    assert (
        result.state
        is LandedCostTemporalEvaluationState.UNKNOWN
    )


def test_missing_currency_freshness_is_unknown():
    result = evaluate_landed_cost_temporal_evidence(
        _aggregation(),
        _currency_evidence(
            freshness=False,
        ),
        _context(),
    )

    assert (
        result.state
        is LandedCostTemporalEvaluationState.UNKNOWN
    )


def test_non_aggregated_landed_cost_is_not_evaluable():
    result = evaluate_landed_cost_temporal_evidence(
        _aggregation(
            state=LandedCostAggregationState.NOT_AGGREGATED,
        ),
        _currency_evidence(),
        _context(),
    )

    assert (
        result.state
        is LandedCostTemporalEvaluationState.NOT_EVALUABLE
    )


def test_landed_cost_context_mismatch_is_not_applicable():
    result = evaluate_landed_cost_temporal_evidence(
        _aggregation(
            context=_context(
                destination_country="JP",
            ),
        ),
        _currency_evidence(),
        _context(),
    )

    assert (
        result.state
        is LandedCostTemporalEvaluationState.NOT_APPLICABLE
    )


def test_currency_evidence_context_mismatch_is_not_applicable():
    result = evaluate_landed_cost_temporal_evidence(
        _aggregation(),
        _currency_evidence(
            context=_context(
                destination_country="JP",
            ),
        ),
        _context(),
    )

    assert (
        result.state
        is LandedCostTemporalEvaluationState.NOT_APPLICABLE
    )


def test_currency_pair_without_landed_cost_currency_is_not_applicable():
    result = evaluate_landed_cost_temporal_evidence(
        _aggregation(
            currency="USD",
        ),
        _currency_evidence(
            base_currency="EUR",
            quote_currency="KRW",
        ),
        _context(),
    )

    assert (
        result.state
        is LandedCostTemporalEvaluationState.NOT_APPLICABLE
    )


def test_quote_currency_can_match_landed_cost_currency():
    result = evaluate_landed_cost_temporal_evidence(
        _aggregation(
            currency="KRW",
        ),
        _currency_evidence(
            base_currency="USD",
            quote_currency="KRW",
        ),
        _context(),
    )

    assert (
        result.state
        is LandedCostTemporalEvaluationState.EVALUABLE
    )


def test_contract_does_not_convert_or_recalculate():
    result = evaluate_landed_cost_temporal_evidence(
        _aggregation(),
        _currency_evidence(),
        _context(),
    )

    forbidden = {
        "converted_total",
        "converted_amount",
        "exchange_rate",
        "payment_fee",
        "payment_fx_fee",
        "recommended_route",
    }

    assert all(
        not hasattr(result, name)
        for name in forbidden
    )


def test_state_vocabulary_is_bounded():
    assert {
        state.value
        for state in LandedCostTemporalEvaluationState
    } == {
        "evaluable",
        "not_applicable",
        "not_evaluable",
        "unknown",
    }
