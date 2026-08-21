from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.currency import (
    CurrencyPair,
    CurrencyRateEvidence,
)
from app.services.cross_border.currency_compatibility import (
    CurrencyCompatibility,
    CurrencyCompatibilityState,
    evaluate_currency_compatibility,
)
from app.services.cross_border.models import (
    CrossBorderEvidence,
    EvidenceState,
)
from app.services.cross_border.provenance import (
    EvidenceProvenance,
)


def _currency_evidence(
    *,
    context_currency: str | None = "USD",
    quote_currency: str = "USD",
    evidence_state: EvidenceState = (
        EvidenceState.VERIFIED
    ),
) -> CurrencyRateEvidence:
    return CurrencyRateEvidence(
        pair=CurrencyPair(
            base_currency="KRW",
            quote_currency=quote_currency,
        ),
        evidence=CrossBorderEvidence(
            state=evidence_state,
        ),
        provenance=EvidenceProvenance(
            source_id="fx-source-001",
            source_type="currency_rate",
        ),
        context=CrossBorderEvaluationContext(
            origin_country="KR",
            destination_country="US",
            currency=context_currency,
        ),
        rate=(
            None
            if evidence_state is EvidenceState.UNKNOWN
            else "0.00074"
        ),
    )


def test_compatibility_state_vocabulary() -> None:
    assert {
        state.value
        for state in CurrencyCompatibilityState
    } == {
        "compatible",
        "incompatible",
        "unknown",
    }


@pytest.mark.parametrize(
    "state",
    [
        EvidenceState.VERIFIED,
        EvidenceState.OBSERVED,
        EvidenceState.ESTIMATED,
    ],
)
def test_matching_quote_currency_is_compatible(
    state: EvidenceState,
) -> None:
    result = evaluate_currency_compatibility(
        _currency_evidence(
            context_currency="USD",
            quote_currency="USD",
            evidence_state=state,
        )
    )

    assert (
        result.state
        is CurrencyCompatibilityState.COMPATIBLE
    )
    assert result.context_currency == "USD"
    assert result.quote_currency == "USD"


def test_mismatched_quote_currency_is_incompatible() -> None:
    result = evaluate_currency_compatibility(
        _currency_evidence(
            context_currency="USD",
            quote_currency="JPY",
        )
    )

    assert (
        result.state
        is CurrencyCompatibilityState.INCOMPATIBLE
    )
    assert result.context_currency == "USD"
    assert result.quote_currency == "JPY"


def test_missing_context_currency_is_unknown() -> None:
    result = evaluate_currency_compatibility(
        _currency_evidence(
            context_currency=None,
            quote_currency="USD",
        )
    )

    assert (
        result.state
        is CurrencyCompatibilityState.UNKNOWN
    )
    assert result.context_currency is None


def test_unknown_currency_evidence_is_unknown() -> None:
    result = evaluate_currency_compatibility(
        _currency_evidence(
            context_currency="USD",
            quote_currency="USD",
            evidence_state=EvidenceState.UNKNOWN,
        )
    )

    assert (
        result.state
        is CurrencyCompatibilityState.UNKNOWN
    )


def test_unknown_evidence_does_not_become_compatible() -> None:
    result = evaluate_currency_compatibility(
        _currency_evidence(
            context_currency="USD",
            quote_currency="USD",
            evidence_state=EvidenceState.UNKNOWN,
        )
    )

    assert (
        result.state
        is not CurrencyCompatibilityState.COMPATIBLE
    )


def test_currency_codes_are_compared_after_normalization() -> None:
    result = evaluate_currency_compatibility(
        _currency_evidence(
            context_currency=" usd ",
            quote_currency=" usd ",
        )
    )

    assert (
        result.state
        is CurrencyCompatibilityState.COMPATIBLE
    )

    assert result.context_currency == "USD"
    assert result.quote_currency == "USD"


def test_compatibility_result_is_immutable() -> None:
    result = CurrencyCompatibility(
        state=CurrencyCompatibilityState.COMPATIBLE,
        context_currency="USD",
        quote_currency="USD",
        reason="test",
    )

    with pytest.raises(FrozenInstanceError):
        result.state = (
            CurrencyCompatibilityState.INCOMPATIBLE
        )


def test_contract_does_not_expose_conversion_authority() -> None:
    forbidden = {
        "convert",
        "convert_amount",
        "calculate_exchange_rate",
        "derive_inverse_rate",
        "get_exchange_rate",
    }

    public_names = {
        name.lower()
        for name in dir(
            CurrencyCompatibility
        )
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(
        public_names
    )
