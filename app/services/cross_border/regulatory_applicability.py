from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.services.cross_border.models import (
    EvidenceState,
)
from app.services.cross_border.regulatory import (
    RegulatoryEvidence,
)


class RegulatoryApplicabilityState(str, Enum):
    """
    Canonical bounded regulatory applicability vocabulary.

    UNKNOWN means applicability cannot be determined from the
    available evidence and evaluation context.

    NOT_APPLICABLE does not mean legally prohibited.
    It means the regulatory evidence does not apply to the
    current destination-country context.
    """

    APPLICABLE = "applicable"
    NOT_APPLICABLE = "not_applicable"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class RegulatoryApplicability:
    """
    Immutable bounded regulatory applicability result.

    This contract checks jurisdiction-to-destination context
    alignment only.

    It does not determine legal permission, import eligibility,
    prohibition, restriction severity, tariff classification,
    duty amount, customs filing requirements, or transaction
    executability.
    """

    state: RegulatoryApplicabilityState
    jurisdiction: str | None
    destination_country: str | None
    reason: str


def evaluate_regulatory_applicability(
    regulatory_evidence: RegulatoryEvidence,
) -> RegulatoryApplicability:
    """
    Evaluate whether regulatory evidence applies to the
    destination-country evaluation context.

    Rules:

    - UNKNOWN evidence -> UNKNOWN
    - missing jurisdiction -> UNKNOWN
    - missing destination country -> UNKNOWN
    - matching jurisdiction/destination -> APPLICABLE
    - differing jurisdiction/destination -> NOT_APPLICABLE

    This function does not make a legal permission decision.
    """

    jurisdiction = (
        regulatory_evidence.jurisdiction
    )

    destination_country = (
        regulatory_evidence.context.destination_country
    )

    if (
        regulatory_evidence.evidence.state
        is EvidenceState.UNKNOWN
    ):
        return RegulatoryApplicability(
            state=RegulatoryApplicabilityState.UNKNOWN,
            jurisdiction=jurisdiction,
            destination_country=destination_country,
            reason="regulatory evidence is UNKNOWN",
        )

    if jurisdiction is None:
        return RegulatoryApplicability(
            state=RegulatoryApplicabilityState.UNKNOWN,
            jurisdiction=None,
            destination_country=destination_country,
            reason="regulatory jurisdiction is unavailable",
        )

    if destination_country is None:
        return RegulatoryApplicability(
            state=RegulatoryApplicabilityState.UNKNOWN,
            jurisdiction=jurisdiction,
            destination_country=None,
            reason="destination country is unavailable",
        )

    normalized_jurisdiction = (
        jurisdiction.strip().upper()
    )

    normalized_destination = (
        destination_country.strip().upper()
    )

    if normalized_jurisdiction == normalized_destination:
        return RegulatoryApplicability(
            state=RegulatoryApplicabilityState.APPLICABLE,
            jurisdiction=normalized_jurisdiction,
            destination_country=normalized_destination,
            reason=(
                "regulatory jurisdiction matches "
                "destination country"
            ),
        )

    return RegulatoryApplicability(
        state=RegulatoryApplicabilityState.NOT_APPLICABLE,
        jurisdiction=normalized_jurisdiction,
        destination_country=normalized_destination,
        reason=(
            "regulatory jurisdiction differs from "
            "destination country"
        ),
    )
