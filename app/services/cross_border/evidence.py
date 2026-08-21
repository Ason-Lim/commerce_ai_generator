from __future__ import annotations

from app.services.cross_border.models import (
    CrossBorderEvidence,
    EvidenceState,
)


def is_unknown(
    evidence: CrossBorderEvidence,
) -> bool:
    """
    Return whether evidence is explicitly UNKNOWN.

    The value itself is deliberately ignored. In particular,
    zero, False, and an empty string do not imply UNKNOWN.
    """

    return evidence.state is EvidenceState.UNKNOWN


def has_usable_evidence(
    evidence: CrossBorderEvidence,
) -> bool:
    """
    Return whether the evidence state represents available evidence.

    VERIFIED, OBSERVED, and ESTIMATED remain distinguishable states
    but are all evidence-bearing. UNKNOWN is not evidence-bearing.

    This function does not assess freshness, regulatory permission,
    landed cost, route validity, or transaction executability.
    """

    return evidence.state is not EvidenceState.UNKNOWN
