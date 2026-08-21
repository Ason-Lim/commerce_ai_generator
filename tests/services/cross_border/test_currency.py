from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import timedelta
from decimal import Decimal

import pytest

from app.services.cross_border.currency import (
    CurrencyPair,
    CurrencyRateEvidence,
)
from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.freshness import (
    EvidenceFreshness,
    EvidenceFreshnessState,
)
from app.services.cross_border.models import (
    CrossBorderEvidence,
    EvidenceState,
)
from app.services.cross_border.provenance import (
    EvidenceProvenance,
)


def _context(
    currency: str | None = "USD",
) -> CrossBorderEvaluationContext:
    return CrossBorderEvaluationContext(
        origin_country="KR",
        destination_country="US",
        currency=currency,
        evaluated_at="2026-08-21T23:30:00+09:00",
    )


def _provenance() -> EvidenceProvenance:
    return EvidenceProvenance(
        source_id="fx-source-001",
        source_type="currency_rate",
        record_id="fx-record-001",
        retrieved_at="2026-08-21T23:29:00+09:00",
        effective_at="2026-08-21T23:28:00+09:00",
    )


def _evidence(
    state: EvidenceState,
) -> CrossBorderEvidence:
    return CrossBorderEvidence(
        state=state,
        source="fx-source-001",
        observed_at="2026-08-21T23:28:00+09:00",
    )


def test_currency_pair_normalizes_codes() -> None:
    pair = CurrencyPair(
        base_currency=" krw ",
        quote_currency=" usd ",
    )

    assert pair.base_currency == "KRW"
    assert pair.quote_currency == "USD"


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("base_currency", ""),
        ("base_currency", "US"),
        ("base_currency", "US12"),
        ("quote_currency", " "),
        ("quote_currency", "USDD"),
        ("quote_currency", "1SD"),
    ],
)
def test_currency_pair_rejects_invalid_codes(
    field_name: str,
    value: str,
) -> None:
    values = {
        "base_currency": "KRW",
        "quote_currency": "USD",
    }
    values[field_name] = value

    with pytest.raises(ValueError):
        CurrencyPair(**values)


def test_currency_pair_is_immutable() -> None:
    pair = CurrencyPair(
        base_currency="KRW",
        quote_currency="USD",
    )

    with pytest.raises(FrozenInstanceError):
        pair.base_currency = "JPY"


@pytest.mark.parametrize(
    ("raw_rate", "expected"),
    [
        ("0.00074", Decimal("0.00074")),
        (Decimal("0.00074"), Decimal("0.00074")),
        (1, Decimal("1")),
        (1.25, Decimal("1.25")),
    ],
)
def test_rate_is_normalized_to_decimal(
    raw_rate,
    expected: Decimal,
) -> None:
    result = CurrencyRateEvidence(
        pair=CurrencyPair("KRW", "USD"),
        evidence=_evidence(
            EvidenceState.OBSERVED
        ),
        provenance=_provenance(),
        context=_context(),
        rate=raw_rate,
    )

    assert result.rate == expected
    assert isinstance(
        result.rate,
        Decimal,
    )


@pytest.mark.parametrize(
    "rate",
    [
        0,
        "0",
        -1,
        "-0.01",
        "NaN",
        "Infinity",
        "-Infinity",
        "not-a-rate",
    ],
)
def test_invalid_rate_is_rejected(
    rate,
) -> None:
    with pytest.raises(ValueError):
        CurrencyRateEvidence(
            pair=CurrencyPair(
                "KRW",
                "USD",
            ),
            evidence=_evidence(
                EvidenceState.OBSERVED
            ),
            provenance=_provenance(),
            context=_context(),
            rate=rate,
        )


@pytest.mark.parametrize(
    "state",
    [
        EvidenceState.VERIFIED,
        EvidenceState.OBSERVED,
        EvidenceState.ESTIMATED,
    ],
)
def test_evidence_bearing_state_requires_rate(
    state: EvidenceState,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "evidence-bearing currency state "
            "requires a rate"
        ),
    ):
        CurrencyRateEvidence(
            pair=CurrencyPair(
                "KRW",
                "USD",
            ),
            evidence=_evidence(state),
            provenance=_provenance(),
            context=_context(),
            rate=None,
        )


def test_unknown_currency_evidence_preserves_no_rate() -> None:
    result = CurrencyRateEvidence(
        pair=CurrencyPair(
            "KRW",
            "USD",
        ),
        evidence=_evidence(
            EvidenceState.UNKNOWN
        ),
        provenance=_provenance(),
        context=_context(),
        rate=None,
    )

    assert result.rate is None
    assert result.has_rate is False


def test_unknown_currency_evidence_rejects_manufactured_rate() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "UNKNOWN currency evidence must not "
            "carry a rate"
        ),
    ):
        CurrencyRateEvidence(
            pair=CurrencyPair(
                "KRW",
                "USD",
            ),
            evidence=_evidence(
                EvidenceState.UNKNOWN
            ),
            provenance=_provenance(),
            context=_context(),
            rate="0.00074",
        )


def test_currency_evidence_preserves_provenance() -> None:
    provenance = _provenance()

    result = CurrencyRateEvidence(
        pair=CurrencyPair(
            "KRW",
            "USD",
        ),
        evidence=_evidence(
            EvidenceState.VERIFIED
        ),
        provenance=provenance,
        context=_context(),
        rate="0.00074",
    )

    assert result.provenance == provenance
    assert (
        result.provenance.record_id
        == "fx-record-001"
    )


def test_currency_evidence_preserves_context() -> None:
    context = _context(
        currency="usd"
    )

    result = CurrencyRateEvidence(
        pair=CurrencyPair(
            "KRW",
            "USD",
        ),
        evidence=_evidence(
            EvidenceState.VERIFIED
        ),
        provenance=_provenance(),
        context=context,
        rate="0.00074",
    )

    assert result.context == context
    assert result.context.currency == "USD"


def test_currency_evidence_can_preserve_existing_freshness() -> None:
    freshness = EvidenceFreshness(
        state=EvidenceFreshnessState.FRESH,
        evidence_at="2026-08-21T23:28:00+09:00",
        age=timedelta(minutes=2),
    )

    result = CurrencyRateEvidence(
        pair=CurrencyPair(
            "KRW",
            "USD",
        ),
        evidence=_evidence(
            EvidenceState.VERIFIED
        ),
        provenance=_provenance(),
        context=_context(),
        rate="0.00074",
        freshness=freshness,
    )

    assert result.freshness == freshness


def test_currency_rate_evidence_is_immutable() -> None:
    result = CurrencyRateEvidence(
        pair=CurrencyPair(
            "KRW",
            "USD",
        ),
        evidence=_evidence(
            EvidenceState.VERIFIED
        ),
        provenance=_provenance(),
        context=_context(),
        rate="0.00074",
    )

    with pytest.raises(FrozenInstanceError):
        result.rate = Decimal("0.00075")


def test_contract_does_not_expose_conversion_authority() -> None:
    forbidden = {
        "convert",
        "convert_amount",
        "calculate_exchange_rate",
        "get_exchange_rate",
        "fetch_rate",
    }

    public_names = {
        name.lower()
        for name in dir(
            CurrencyRateEvidence
        )
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(
        public_names
    )
