from __future__ import annotations

from enum import Enum


class ExternalEvidenceProviderEvaluationSourceRelationship(
    str,
    Enum,
):
    """
    Stable identities describing how an evaluation evidence source
    relates to the external evidence provider evaluation subject.

    SUBJECT_SUPPLIED means the subject supplied the evidence source.

    THIRD_PARTY means the source is separate from the subject. It does
    not assert independence, correctness, verification, or authority.

    INTERNAL_OBSERVATION means the evidence source records a bounded
    Commerce AI observation or validation activity.

    UNKNOWN means the source-to-subject relationship is unresolved.

    These values do not determine evidence state, freshness, trust,
    quality, score, rank, provider selection, or acquisition authority.
    """

    SUBJECT_SUPPLIED = "subject_supplied"
    THIRD_PARTY = "third_party"
    INTERNAL_OBSERVATION = "internal_observation"
    UNKNOWN = "unknown"
