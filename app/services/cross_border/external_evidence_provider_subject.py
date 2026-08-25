from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExternalEvidenceProviderEvaluationSubject:
    """
    Opaque correlation reference for the subject of an external
    evidence provider evaluation.

    subject_ref links evaluation material concerning the same subject.

    It does not identify or resolve a canonical provider, legal entity,
    account, endpoint, credential, client, registry entry, or selected
    provider.

    It does not carry evaluation evidence or provenance. Evidence
    source identity remains owned by EvidenceProvenance.
    """

    subject_ref: str

    def __post_init__(self) -> None:
        subject_ref = self.subject_ref.strip()

        if not subject_ref:
            raise ValueError(
                "evaluation subject_ref must not be empty"
            )

        object.__setattr__(
            self,
            "subject_ref",
            subject_ref,
        )
