from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.services.cross_border.currency import (
    CurrencyRateEvidence,
)
from app.services.cross_border.models import (
    EvidenceState,
)


class CurrencyCompatibilityState(str, Enum):
    """
    Canonical bounded compatibility vocabulary.

    UNKNOWN means compatibility cannot be established from
    the available evaluation context and evidence.
    """

    COMPATIBLE = "compatible"
    INCOMPATIBLE = "incompatible"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class CurrencyCompatibility:
    """
    Immutable result of bounded currency-context compatibility.

    This contract checks whether CurrencyRateEvidence is aligned
    with the evaluation context currency.

    It does not convert monetary amounts, retrieve FX data,
    derive inverse rates, define rounding policy, calculate
    landed cost, or perform transaction execution.
    """

    state: CurrencyCompatibilityState
    context_currency: str | None
    quote_currency: str
    reason: str


def evaluate_currency_compatibility(
    currency_evidence: CurrencyRateEvidence,
) -> CurrencyCompatibility:
    """
    Evaluate compatibility between the evidence quote currency
    and the Cross-Border evaluation context currency.

    Rules:

    - UNKNOWN evidence -> UNKNOWN
    - missing context currency -> UNKNOWN
    - matching context/quote currency -> COMPATIBLE
    - differing context/quote currency -> INCOMPATIBLE
    """

    context_currency = (
        currency_evidence.context.currency
    )

    quote_currency = (
        currency_evidence.pair.quote_currency
    )

    if (
        currency_evidence.evidence.state
        is EvidenceState.UNKNOWN
    ):
        return CurrencyCompatibility(
            state=CurrencyCompatibilityState.UNKNOWN,
            context_currency=context_currency,
            quote_currency=quote_currency,
            reason="currency evidence is UNKNOWN",
        )

    if context_currency is None:
        return CurrencyCompatibility(
            state=CurrencyCompatibilityState.UNKNOWN,
            context_currency=None,
            quote_currency=quote_currency,
            reason="evaluation context currency is unavailable",
        )

    if context_currency == quote_currency:
        return CurrencyCompatibility(
            state=CurrencyCompatibilityState.COMPATIBLE,
            context_currency=context_currency,
            quote_currency=quote_currency,
            reason=(
                "evaluation context currency matches "
                "currency evidence quote currency"
            ),
        )

    return CurrencyCompatibility(
        state=CurrencyCompatibilityState.INCOMPATIBLE,
        context_currency=context_currency,
        quote_currency=quote_currency,
        reason=(
            "evaluation context currency differs from "
            "currency evidence quote currency"
        ),
    )
