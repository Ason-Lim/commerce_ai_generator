from __future__ import annotations

from dataclasses import dataclass

from app.services.cross_border.external_evidence_provider_evidence import (
    ExternalEvidenceProviderEvaluationEvidence,
)
from app.services.cross_border.external_evidence_provider_subject import (
    ExternalEvidenceProviderEvaluationSubject,
)


@dataclass(frozen=True)
class ExternalEvidenceProviderEvaluationEvidenceCollection:
    """
    Immutable ordered collection of provider-evaluation evidence
    bindings concerning one evaluation subject.

    Input order is preserved. Multiple evidence items for the same
    dimension are allowed because distinct sources may support or
    record evidence concerning that dimension.

    This collection does not deduplicate, merge, prioritize, reconcile,
    compare, score, rank, recommend, or select providers or evidence.

    It does not determine completeness, coverage, trust, correctness,
    quality, or acquisition readiness. Existing evidence, provenance,
    dimension, source-relationship, and subject contracts retain their
    authority.
    """

    subject: ExternalEvidenceProviderEvaluationSubject
    evidence_items: tuple[
        ExternalEvidenceProviderEvaluationEvidence,
        ...,
    ]

    def __post_init__(self) -> None:
        evidence_items = tuple(
            self.evidence_items
        )

        if not evidence_items:
            raise ValueError(
                "provider evaluation evidence collection "
                "must not be empty"
            )

        if any(
            item.subject != self.subject
            for item in evidence_items
        ):
            raise ValueError(
                "all provider evaluation evidence items "
                "must concern the collection subject"
            )

        object.__setattr__(
            self,
            "evidence_items",
            evidence_items,
        )
