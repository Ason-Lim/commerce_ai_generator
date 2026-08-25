from __future__ import annotations

from app.services.cross_border.evidence import (
    has_usable_evidence,
)
from app.services.cross_border.external_evidence_provider_evaluation import (
    ExternalEvidenceProviderEvaluationDimension,
)
from app.services.cross_border.external_evidence_provider_evidence import (
    ExternalEvidenceProviderEvaluationEvidence,
)
from app.services.cross_border.external_evidence_provider_evidence_collection import (
    ExternalEvidenceProviderEvaluationEvidenceCollection,
)


def evidence_items_for_dimension(
    collection: ExternalEvidenceProviderEvaluationEvidenceCollection,
    dimension: ExternalEvidenceProviderEvaluationDimension,
) -> tuple[
    ExternalEvidenceProviderEvaluationEvidence,
    ...,
]:
    """
    Return all recorded evidence bindings for one evaluation dimension.

    Input order and duplicates are preserved. UNKNOWN evidence remains
    present because a recorded item and usable evidence are distinct.

    An empty tuple means only that this collection contains no item for
    the requested dimension. It does not determine provider coverage,
    completeness, quality, readiness, or selection.
    """

    return tuple(
        item
        for item in collection.evidence_items
        if item.dimension is dimension
    )


def usable_evidence_items_for_dimension(
    collection: ExternalEvidenceProviderEvaluationEvidenceCollection,
    dimension: ExternalEvidenceProviderEvaluationDimension,
) -> tuple[
    ExternalEvidenceProviderEvaluationEvidence,
    ...,
]:
    """
    Return dimension bindings whose canonical evidence is usable.

    Usability delegates exclusively to has_usable_evidence. This
    function introduces no parallel evidence state and does not infer
    trust, correctness, sufficiency, completeness, score, or selection.
    Input order and duplicates are preserved.
    """

    return tuple(
        item
        for item in evidence_items_for_dimension(
            collection,
            dimension,
        )
        if has_usable_evidence(
            item.evidence
        )
    )
