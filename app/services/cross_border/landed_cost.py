from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.provenance import (
    EvidenceProvenance,
)


class LandedCostComponentState(str, Enum):
    """
    Canonical evidence state for one landed-cost component.

    UNKNOWN and UNAVAILABLE must never be interpreted as zero.

    NOT_APPLICABLE means the component does not apply in the
    current evaluation context and therefore carries no amount.
    """

    KNOWN = "KNOWN"
    ESTIMATED = "ESTIMATED"
    DERIVED = "DERIVED"
    UNKNOWN = "UNKNOWN"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True)
class LandedCostComponentEvidence:
    """
    Immutable evidence for one material landed-cost component.

    This contract represents bounded monetary evidence only.

    It may preserve canonical provenance and Cross-Border
    evaluation context.

    It does not:
    - calculate landed cost;
    - calculate duty or tax;
    - perform FX conversion;
    - infer missing amounts;
    - rank purchase routes;
    - recommend a purchase path;
    - execute transactions.
    """

    component: str
    state: LandedCostComponentState

    amount: Decimal | None = None
    currency: str | None = None

    provenance: EvidenceProvenance | None = None
    context: CrossBorderEvaluationContext | None = None

    def __post_init__(self) -> None:
        component = self.component.strip()

        if not component:
            raise ValueError(
                "landed-cost component must be non-empty"
            )

        object.__setattr__(
            self,
            "component",
            component,
        )

        currency = (
            self.currency.strip().upper()
            if self.currency is not None
            else None
        )

        if currency == "":
            currency = None

        object.__setattr__(
            self,
            "currency",
            currency,
        )

        evidence_bearing_states = {
            LandedCostComponentState.KNOWN,
            LandedCostComponentState.ESTIMATED,
            LandedCostComponentState.DERIVED,
        }

        evidence_absent_states = {
            LandedCostComponentState.UNKNOWN,
            LandedCostComponentState.UNAVAILABLE,
            LandedCostComponentState.NOT_APPLICABLE,
        }

        if self.state in evidence_bearing_states:
            if self.amount is None:
                raise ValueError(
                    "evidence-bearing landed-cost component "
                    "requires an amount"
                )

            if self.amount < Decimal("0"):
                raise ValueError(
                    "landed-cost component amount "
                    "must not be negative"
                )

            if currency is None:
                raise ValueError(
                    "evidence-bearing landed-cost component "
                    "requires currency"
                )

        elif self.state in evidence_absent_states:
            if self.amount is not None:
                raise ValueError(
                    "evidence-absent landed-cost component "
                    "must not carry an amount"
                )

            if currency is not None:
                raise ValueError(
                    "evidence-absent landed-cost component "
                    "must not carry currency"
                )

    @property
    def has_amount(self) -> bool:
        return self.amount is not None

    @property
    def is_zero(self) -> bool:
        return (
            self.amount is not None
            and self.amount == Decimal("0")
        )

    @property
    def is_known(self) -> bool:
        return (
            self.state
            is LandedCostComponentState.KNOWN
        )

    @property
    def is_estimated(self) -> bool:
        return (
            self.state
            is LandedCostComponentState.ESTIMATED
        )

    @property
    def is_derived(self) -> bool:
        return (
            self.state
            is LandedCostComponentState.DERIVED
        )

    @property
    def is_unknown(self) -> bool:
        return (
            self.state
            is LandedCostComponentState.UNKNOWN
        )

    @property
    def is_unavailable(self) -> bool:
        return (
            self.state
            is LandedCostComponentState.UNAVAILABLE
        )

    @property
    def is_not_applicable(self) -> bool:
        return (
            self.state
            is LandedCostComponentState.NOT_APPLICABLE
        )
