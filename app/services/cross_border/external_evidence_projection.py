from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.services.cross_border.external_evidence_ingress import (
    ExternalEvidenceKind,
)


class CanonicalProjectionTarget(str, Enum):
    """
    Stable provider-neutral identities for canonical Cross-Border
    evidence targets.

    These values identify target contract families only.

    They do not construct canonical evidence, interpret provider
    fields, normalize provider values, select providers, retrieve
    external data, or authorize acquisition.
    """

    CURRENCY_RATE_EVIDENCE = "currency_rate_evidence"
    SHIPPING_ROUTE_EVIDENCE = "shipping_route_evidence"
    REGULATORY_EVIDENCE = "regulatory_evidence"
    LANDED_COST_COMPONENT_EVIDENCE = (
        "landed_cost_component_evidence"
    )


_PROJECTION_TARGET_BY_KIND = {
    ExternalEvidenceKind.CURRENCY_RATE:
        CanonicalProjectionTarget.CURRENCY_RATE_EVIDENCE,
    ExternalEvidenceKind.SHIPPING_ROUTE:
        CanonicalProjectionTarget.SHIPPING_ROUTE_EVIDENCE,
    ExternalEvidenceKind.REGULATORY:
        CanonicalProjectionTarget.REGULATORY_EVIDENCE,
    ExternalEvidenceKind.LANDED_COST_COMPONENT:
        CanonicalProjectionTarget.LANDED_COST_COMPONENT_EVIDENCE,
}


@dataclass(frozen=True)
class ExternalEvidenceProjectionEligibility:
    """
    Immutable declaration of the canonical target family permitted
    for one external evidence kind.

    This contract expresses projection eligibility only.

    It deliberately carries no provider payload, interpreted value,
    constructor arguments, credentials, HTTP state, retry policy,
    freshness decision, confidence decision, or executable projector.

    Actual construction and normalization remain owned by the
    existing canonical target contracts and their bounded
    normalization authorities.
    """

    kind: ExternalEvidenceKind
    target: CanonicalProjectionTarget

    def __post_init__(self) -> None:
        expected = _PROJECTION_TARGET_BY_KIND[self.kind]

        if self.target is not expected:
            raise ValueError(
                "canonical projection target does not match "
                f"external evidence kind: {self.kind.value}"
            )


def projection_target_for(
    kind: ExternalEvidenceKind,
) -> CanonicalProjectionTarget:
    """
    Return the single canonical target family associated with an
    external evidence kind.

    This lookup does not execute projection.
    """

    if not isinstance(kind, ExternalEvidenceKind):
        raise TypeError(
            "kind must be an ExternalEvidenceKind"
        )

    return _PROJECTION_TARGET_BY_KIND[kind]
