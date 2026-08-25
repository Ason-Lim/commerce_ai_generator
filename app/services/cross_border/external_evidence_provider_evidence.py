from __future__ import annotations

from dataclasses import dataclass

from app.services.cross_border.external_evidence_provider_evaluation import (
    ExternalEvidenceProviderEvaluationDimension,
)
from app.services.cross_border.external_evidence_provider_source_relationship import (
    ExternalEvidenceProviderEvaluationSourceRelationship,
)
from app.services.cross_border.external_evidence_provider_subject import (
    ExternalEvidenceProviderEvaluationSubject,
)
from app.services.cross_border.models import (
    CrossBorderEvidence,
    EvidenceState,
)
from app.services.cross_border.provenance import (
    EvidenceProvenance,
)


@dataclass(frozen=True)
class ExternalEvidenceProviderEvaluationEvidence:
    """
    Immutable binding of one provider-evaluation subject and dimension
    to canonical cross-border evidence and its provenance.

    subject identifies only the evaluation subject. provenance
    independently identifies the evidence source.

    source_relationship describes the source-to-subject relationship.
    It does not determine evidence state, trust, correctness, quality,
    score, rank, recommendation, selection, or acquisition authority.

    UNKNOWN evidence carries no observation value. Evidence-bearing
    states carry an observation value; zero, False, and an empty string
    remain valid values.

    This contract does not create provider identity, registry, adapter,
    network, credential, raw-payload, or execution authority.
    """

    subject: ExternalEvidenceProviderEvaluationSubject
    dimension: ExternalEvidenceProviderEvaluationDimension
    source_relationship: (
        ExternalEvidenceProviderEvaluationSourceRelationship
    )
    evidence: CrossBorderEvidence
    provenance: EvidenceProvenance

    def __post_init__(self) -> None:
        if (
            self.evidence.state is EvidenceState.UNKNOWN
            and self.evidence.value is not None
        ):
            raise ValueError(
                "UNKNOWN evaluation evidence must not carry a value"
            )

        if (
            self.evidence.state is not EvidenceState.UNKNOWN
            and self.evidence.value is None
        ):
            raise ValueError(
                "evidence-bearing evaluation evidence must carry a value"
            )
