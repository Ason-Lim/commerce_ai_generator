"""
Canonical Cross-Border Commerce intelligence contracts.

This package contains bounded intelligence contracts only.

Transaction execution, checkout, payment, customs filing,
shipment booking, and financial settlement are out of scope.
"""

from app.services.cross_border.evidence import (
    has_usable_evidence,
    is_unknown,
)
from app.services.cross_border.models import (
    CrossBorderEvidence,
    EvidenceState,
)

__all__ = [
    "CrossBorderEvidence",
    "EvidenceState",
    "has_usable_evidence",
    "is_unknown",
]
