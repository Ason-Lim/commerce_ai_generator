from __future__ import annotations

from dataclasses import dataclass

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.evidence import (
    has_usable_evidence,
)
from app.services.cross_border.freshness import (
    EvidenceFreshness,
)
from app.services.cross_border.identity import (
    ProductIdentityRelationship,
)
from app.services.cross_border.models import (
    CrossBorderEvidence,
    EvidenceState,
)
from app.services.cross_border.provenance import (
    EvidenceProvenance,
)


@dataclass(frozen=True)
class ProductIdentityEvidenceBinding:
    """
    Immutable binding between a bounded product relationship and
    the evidence context that supports or records that relationship.

    This contract does not resolve, match, normalize, canonicalize,
    or otherwise own general Product Identity.

    Freshness may be associated when already evaluated by the
    canonical freshness contract. This class does not calculate
    freshness or define freshness thresholds.

    Transaction execution remains outside this contract.
    """

    relationship: ProductIdentityRelationship
    evidence: CrossBorderEvidence
    provenance: EvidenceProvenance
    context: CrossBorderEvaluationContext
    freshness: EvidenceFreshness | None = None

    def __post_init__(self) -> None:
        if (
            self.relationship.is_resolved
            and self.evidence.state is EvidenceState.UNKNOWN
        ):
            raise ValueError(
                "resolved product relationship requires "
                "evidence-bearing state"
            )

    @property
    def relationship_is_resolved(self) -> bool:
        return self.relationship.is_resolved

    @property
    def evidence_is_usable(self) -> bool:
        return has_usable_evidence(
            self.evidence
        )
