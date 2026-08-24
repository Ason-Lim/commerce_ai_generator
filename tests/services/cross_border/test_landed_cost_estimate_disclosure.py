from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

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
from app.services.cross_border.landed_cost_estimate_disclosure import (
    LandedCostEstimateDisclosureEvidence,
    compose_landed_cost_estimate_disclosure_evidence,
)
from app.services.cross_border.landed_cost_estimate_validity_binding import (
    bind_landed_cost_estimate_validity,
)
from app.services.cross_border.landed_cost_temporal_evaluation import (
    LandedCostTemporalEvaluation,
    LandedCostTemporalEvaluationState,
)
from app.services.cross_border.models import (
    CrossBorderEvidence,
    EvidenceState,
)
from app.services.cross_border.provenance import (
    EvidenceProvenance,
)


def _context():
    return CrossBorderEvaluationContext(
        origin_country="US",
        destination_country="KR",
    )


def _aggregation():
    return LandedCostAggregation(
        state=LandedCostAggregationState.AGGREGATED,
        total=Decimal("78.00"),
        currency="USD",
        context=_context(),
        quality=LandedCostAggregationQuality.ESTIMATED,
        included_component_count=1,
        reason="landed cost aggregated from available components",
    )


def _validity():
    temporal = LandedCostTemporalEvaluation(
        state=LandedCostTemporalEvaluationState.EVALUABLE,
        reason=(
            "landed-cost evidence applies to the current context "
            "and currency evidence is fresh"
        ),
    )
    return bind_landed_cost_estimate_validity(
        _aggregation(),
        temporal,
    )


def _currency_evidence():
    return CurrencyRateEvidence(
        pair=CurrencyPair(
            base_currency="USD",
            quote_currency="KRW",
        ),
        evidence=CrossBorderEvidence(
            state=EvidenceState.OBSERVED,
        ),
        provenance=EvidenceProvenance(
            source_id="fx-provider",
            source_type="currency_rate",
            record_id="fx-001",
            retrieved_at="2026-08-24T07:00:00Z",
            effective_at="2026-08-24T06:55:00Z",
        ),
        context=_context(),
        rate=Decimal("1390"),
        freshness=EvidenceFreshness(
            state=EvidenceFreshnessState.FRESH,
        ),
    )


def test_composes_canonical_disclosure_evidence():
    result = compose_landed_cost_estimate_disclosure_evidence(
        aggregation=_aggregation(),
        validity=_validity(),
        currency_evidence=_currency_evidence(),
    )

    assert isinstance(
        result,
        LandedCostEstimateDisclosureEvidence,
    )


def test_preserves_landed_cost_without_conversion():
    result = compose_landed_cost_estimate_disclosure_evidence(
        aggregation=_aggregation(),
        validity=_validity(),
        currency_evidence=_currency_evidence(),
    )

    assert result.total == Decimal("78.00")
    assert result.currency == "USD"


def test_preserves_existing_validity_authorities():
    validity = _validity()

    result = compose_landed_cost_estimate_disclosure_evidence(
        aggregation=_aggregation(),
        validity=validity,
        currency_evidence=_currency_evidence(),
    )

    assert result.aggregation_state is validity.aggregation_state
    assert result.aggregation_quality is validity.aggregation_quality
    assert result.aggregation_reason == validity.aggregation_reason
    assert result.temporal_state is validity.temporal_state
    assert result.temporal_reason == validity.temporal_reason


def test_preserves_fx_rate_direction_and_provenance_time():
    evidence = _currency_evidence()

    result = compose_landed_cost_estimate_disclosure_evidence(
        aggregation=_aggregation(),
        validity=_validity(),
        currency_evidence=evidence,
    )

    assert result.fx_base_currency == "USD"
    assert result.fx_quote_currency == "KRW"
    assert result.fx_rate == Decimal("1390")
    assert (
        result.fx_retrieved_at
        == evidence.provenance.retrieved_at
    )
    assert (
        result.fx_effective_at
        == evidence.provenance.effective_at
    )


def test_does_not_convert_landed_cost_using_fx_rate():
    result = compose_landed_cost_estimate_disclosure_evidence(
        aggregation=_aggregation(),
        validity=_validity(),
        currency_evidence=_currency_evidence(),
    )

    assert result.total == Decimal("78.00")
    assert not hasattr(result, "converted_total")
    assert not hasattr(result, "converted_amount")


def test_does_not_introduce_payment_fee_or_checkout_authority():
    result = compose_landed_cost_estimate_disclosure_evidence(
        aggregation=_aggregation(),
        validity=_validity(),
        currency_evidence=_currency_evidence(),
    )

    forbidden = {
        "card_fee",
        "payment_fee",
        "payment_fx_fee",
        "checkout_total",
        "final_payment_amount",
        "recommended_route",
        "winner",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(public_names)


def test_disclosure_evidence_is_immutable():
    result = compose_landed_cost_estimate_disclosure_evidence(
        aggregation=_aggregation(),
        validity=_validity(),
        currency_evidence=_currency_evidence(),
    )

    with pytest.raises(FrozenInstanceError):
        result.total = Decimal("100.00")
