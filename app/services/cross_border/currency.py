from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.freshness import (
    EvidenceFreshness,
)
from app.services.cross_border.models import (
    CrossBorderEvidence,
    EvidenceState,
)
from app.services.cross_border.provenance import (
    EvidenceProvenance,
)


def _normalize_currency(
    name: str,
    value: str,
) -> str:
    normalized = value.strip().upper()

    if not normalized:
        raise ValueError(
            f"{name} must not be empty"
        )

    if len(normalized) != 3:
        raise ValueError(
            f"{name} must be a 3-character currency code"
        )

    if not normalized.isalpha():
        raise ValueError(
            f"{name} must contain letters only"
        )

    return normalized


def _normalize_rate(
    value: Decimal | str | int | float | None,
) -> Decimal | None:
    if value is None:
        return None

    if isinstance(value, float):
        value = str(value)

    try:
        rate = Decimal(value)
    except (
        InvalidOperation,
        TypeError,
        ValueError,
    ) as exc:
        raise ValueError(
            "rate must be a valid decimal value"
        ) from exc

    if not rate.is_finite():
        raise ValueError(
            "rate must be finite"
        )

    if rate <= 0:
        raise ValueError(
            "rate must be greater than zero"
        )

    return rate


@dataclass(frozen=True)
class CurrencyPair:
    """
    Immutable bounded currency-pair contract.

    This value object identifies the quoted conversion direction only.
    It does not retrieve rates or convert monetary amounts.
    """

    base_currency: str
    quote_currency: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "base_currency",
            _normalize_currency(
                "base_currency",
                self.base_currency,
            ),
        )

        object.__setattr__(
            self,
            "quote_currency",
            _normalize_currency(
                "quote_currency",
                self.quote_currency,
            ),
        )


@dataclass(frozen=True)
class CurrencyRateEvidence:
    """
    Immutable bounded currency-rate evidence.

    rate means:

        1 base_currency = rate quote_currency

    UNKNOWN evidence must not manufacture a rate.

    This contract preserves externally supplied rate evidence.
    It does not retrieve FX data, convert amounts, choose providers,
    define rounding policy, or calculate landed cost.
    """

    pair: CurrencyPair
    evidence: CrossBorderEvidence
    provenance: EvidenceProvenance
    context: CrossBorderEvaluationContext
    rate: Decimal | str | int | float | None = None
    freshness: EvidenceFreshness | None = None

    def __post_init__(self) -> None:
        rate = _normalize_rate(
            self.rate
        )

        if (
            self.evidence.state
            is EvidenceState.UNKNOWN
        ):
            if rate is not None:
                raise ValueError(
                    "UNKNOWN currency evidence must not "
                    "carry a rate"
                )
        elif rate is None:
            raise ValueError(
                "evidence-bearing currency state "
                "requires a rate"
            )

        object.__setattr__(
            self,
            "rate",
            rate,
        )

    @property
    def has_rate(self) -> bool:
        return self.rate is not None
