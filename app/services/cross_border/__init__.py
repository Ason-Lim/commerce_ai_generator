"""
Canonical Cross-Border Commerce intelligence contracts.

This package contains bounded intelligence contracts only.

Transaction execution, checkout, payment, customs filing,
shipment booking, and financial settlement are out of scope.
"""

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.evidence import (
    has_usable_evidence,
    is_unknown,
)
from app.services.cross_border.freshness import (
    EvidenceFreshness,
    EvidenceFreshnessState,
    evaluate_evidence_freshness,
)
from app.services.cross_border.models import (
    CrossBorderEvidence,
    EvidenceState,
)
from app.services.cross_border.provenance import (
    EvidenceProvenance,
)

__all__ = [
    "CrossBorderEvaluationContext",
    "CrossBorderEvidence",
    "EvidenceFreshness",
    "EvidenceFreshnessState",
    "EvidenceState",
    "EvidenceProvenance",
    "evaluate_evidence_freshness",
    "has_usable_evidence",
    "is_unknown",
]
