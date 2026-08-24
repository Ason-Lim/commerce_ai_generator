from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.services.cross_border.currency import (
    CurrencyRateEvidence,
)
from app.services.cross_border.landed_cost_aggregation import (
    LandedCostAggregation,
    LandedCostAggregationQuality,
    LandedCostAggregationState,
)
from app.services.cross_border.landed_cost_estimate_validity_binding import (
    LandedCostEstimateValidityBinding,
)
from app.services.cross_border.landed_cost_temporal_evaluation import (
    LandedCostTemporalEvaluationState,
)


@dataclass(frozen=True)
class LandedCostEstimateDisclosureEvidence:
    """
    Immutable downstream-facing landed-cost estimate disclosure
    evidence.

    This contract preserves conclusions already established by
    canonical Cross-Border authorities.

    It does not:

    - calculate or re-aggregate landed cost;
    - retrieve or calculate FX rates;
    - convert monetary amounts;
    - calculate payment or card fees;
    - introduce VALID / INVALID / STALE vocabulary;
    - rank or recommend candidates;
    - render customer-facing disclosure text;
    - execute checkout, payment, or purchase behavior.

    The rate direction remains defined by CurrencyRateEvidence:

        1 base_currency = fx_rate quote_currency
    """

    total: Decimal | None
    currency: str | None

    aggregation_state: LandedCostAggregationState
    aggregation_quality: LandedCostAggregationQuality | None
    aggregation_reason: str

    temporal_state: LandedCostTemporalEvaluationState
    temporal_reason: str

    fx_base_currency: str
    fx_quote_currency: str
    fx_rate: Decimal | None
    fx_retrieved_at: str | None
    fx_effective_at: str | None


def compose_landed_cost_estimate_disclosure_evidence(
    *,
    aggregation: LandedCostAggregation,
    validity: LandedCostEstimateValidityBinding,
    currency_evidence: CurrencyRateEvidence,
) -> LandedCostEstimateDisclosureEvidence:
    """
    Compose already-established landed-cost, validity, and currency
    evidence into one bounded disclosure carrier.

    Inputs are preserved without deriving a new validity conclusion.
    """

    return LandedCostEstimateDisclosureEvidence(
        total=aggregation.total,
        currency=aggregation.currency,
        aggregation_state=validity.aggregation_state,
        aggregation_quality=validity.aggregation_quality,
        aggregation_reason=validity.aggregation_reason,
        temporal_state=validity.temporal_state,
        temporal_reason=validity.temporal_reason,
        fx_base_currency=currency_evidence.pair.base_currency,
        fx_quote_currency=currency_evidence.pair.quote_currency,
        fx_rate=currency_evidence.rate,
        fx_retrieved_at=currency_evidence.provenance.retrieved_at,
        fx_effective_at=currency_evidence.provenance.effective_at,
    )
