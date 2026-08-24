from __future__ import annotations

from decimal import Decimal, InvalidOperation

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.landed_cost import (
    LandedCostComponentEvidence,
    LandedCostComponentState,
    is_canonical_landed_cost_component,
)
from app.services.cross_border.provenance import (
    EvidenceProvenance,
)


def _normalize_amount(
    value: Decimal | str | int | float | None,
) -> Decimal | None:
    if value is None:
        return None

    if isinstance(value, float):
        value = str(value)

    try:
        amount = Decimal(value)
    except (
        InvalidOperation,
        TypeError,
        ValueError,
    ) as exc:
        raise ValueError(
            "landed-cost amount must be a valid decimal value"
        ) from exc

    if not amount.is_finite():
        raise ValueError(
            "landed-cost amount must be finite"
        )

    return amount


def normalize_landed_cost_component_evidence(
    *,
    component: str,
    state: LandedCostComponentState,
    amount: Decimal | str | int | float | None = None,
    currency: str | None = None,
    provenance: EvidenceProvenance | None = None,
    context: CrossBorderEvaluationContext | None = None,
    estimate_reason: str | None = None,
    canonical_required: bool = False,
) -> LandedCostComponentEvidence:
    """
    Project an already-interpreted provider-neutral landed-cost
    observation into the canonical component evidence contract.

    This boundary deliberately does not know provider field names,
    provider payload schemas, API clients, tariff algorithms,
    insurance rules, FX pricing rules, or shipping-rate formulas.

    Provider-specific adapters remain responsible for interpreting
    their own schemas and selecting the intended component name.

    The landed-cost component vocabulary remains open by default.
    canonical_required=True may be used by an adapter when it claims
    to project specifically into the canonical Commerce AI vocabulary.
    """

    normalized_component = component.strip()

    if not normalized_component:
        raise ValueError(
            "landed-cost component must be non-empty"
        )

    if (
        canonical_required
        and not is_canonical_landed_cost_component(
            normalized_component
        )
    ):
        raise ValueError(
            "landed-cost component is not canonical: "
            f"{normalized_component}"
        )

    normalized_currency = (
        currency.strip().upper()
        if currency is not None
        else None
    )

    if normalized_currency == "":
        normalized_currency = None

    return LandedCostComponentEvidence(
        component=normalized_component,
        state=state,
        amount=_normalize_amount(amount),
        currency=normalized_currency,
        provenance=provenance,
        context=context,
        estimate_reason=estimate_reason,
    )
