from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.provenance import (
    EvidenceProvenance,
)


class ExternalEvidenceKind(str, Enum):
    """
    Provider-neutral canonical projection targets for external
    Cross-Border evidence ingress.

    These values identify the kind of canonical evidence an
    already-interpreted external observation is intended to
    project into. They do not identify providers or authorize
    acquisition.
    """

    CURRENCY_RATE = "currency_rate"
    SHIPPING_ROUTE = "shipping_route"
    REGULATORY = "regulatory"
    LANDED_COST_COMPONENT = "landed_cost_component"


@dataclass(frozen=True)
class ExternalEvidenceIngress:
    """
    Minimal immutable ingress envelope for already-interpreted
    external Cross-Border evidence.

    provenance remains the canonical authority for source identity
    and source timing.

    context remains the canonical authority for the bounded
    Cross-Border evaluation context.

    This contract deliberately does not carry raw provider payloads,
    provider field mappings, credentials, HTTP state, freshness
    decisions, evidence values, or provider-specific identifiers.

    It does not retrieve external data, select providers, interpret
    provider schemas, calculate values, project evidence into a
    downstream canonical contract, or authorize transaction
    execution.
    """

    kind: ExternalEvidenceKind
    provenance: EvidenceProvenance
    context: CrossBorderEvaluationContext
