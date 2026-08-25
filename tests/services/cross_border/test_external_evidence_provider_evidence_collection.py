from dataclasses import FrozenInstanceError

import pytest

from app.services.cross_border import (
    external_evidence_provider_evidence_collection as collection_module,
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


def _subject(
    subject_ref: str = "provider-evaluation-subject-1",
) -> ExternalEvidenceProviderEvaluationSubject:
    return ExternalEvidenceProviderEvaluationSubject(
        subject_ref=subject_ref,
    )


def _item(
    *,
    subject: ExternalEvidenceProviderEvaluationSubject,
    dimension: ExternalEvidenceProviderEvaluationDimension,
    source_id: str,
    value: object,
    relationship: (
        ExternalEvidenceProviderEvaluationSourceRelationship
    ) = (
        ExternalEvidenceProviderEvaluationSourceRelationship
        .THIRD_PARTY
    ),
) -> ExternalEvidenceProviderEvaluationEvidence:
    return ExternalEvidenceProviderEvaluationEvidence(
        subject=subject,
        dimension=dimension,
        source_relationship=relationship,
        evidence=CrossBorderEvidence(
            state=EvidenceState.OBSERVED,
            value=value,
        ),
        provenance=EvidenceProvenance(
            source_id=source_id,
            source_type="evaluation-source",
        ),
    )


def test_collection_preserves_subject_and_item_order() -> None:
    subject = _subject()
    first = _item(
        subject=subject,
        dimension=(
            ExternalEvidenceProviderEvaluationDimension
            .EVIDENCE_KIND_COVERAGE
        ),
        source_id="source-1",
        value="currency-rate",
    )
    second = _item(
        subject=subject,
        dimension=(
            ExternalEvidenceProviderEvaluationDimension
            .GEOGRAPHIC_COVERAGE
        ),
        source_id="source-2",
        value="KR-US",
    )

    collection = (
        ExternalEvidenceProviderEvaluationEvidenceCollection(
            subject=subject,
            evidence_items=(
                first,
                second,
            ),
        )
    )

    assert collection.subject is subject
    assert collection.evidence_items == (
        first,
        second,
    )


def test_collection_defensively_converts_input_to_tuple() -> None:
    subject = _subject()
    first = _item(
        subject=subject,
        dimension=(
            ExternalEvidenceProviderEvaluationDimension
            .TEMPORAL_EVIDENCE
        ),
        source_id="source-1",
        value=True,
    )
    supplied_items = [first]

    collection = (
        ExternalEvidenceProviderEvaluationEvidenceCollection(
            subject=subject,
            evidence_items=supplied_items,
        )
    )
    supplied_items.clear()

    assert isinstance(
        collection.evidence_items,
        tuple,
    )
    assert collection.evidence_items == (first,)


def test_empty_collection_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "provider evaluation evidence collection "
            "must not be empty"
        ),
    ):
        ExternalEvidenceProviderEvaluationEvidenceCollection(
            subject=_subject(),
            evidence_items=(),
        )


def test_mixed_subjects_are_rejected() -> None:
    collection_subject = _subject(
        "provider-evaluation-subject-1"
    )
    other_subject = _subject(
        "provider-evaluation-subject-2"
    )
    item = _item(
        subject=other_subject,
        dimension=(
            ExternalEvidenceProviderEvaluationDimension
            .OPERATIONAL_CONSTRAINTS
        ),
        source_id="source-1",
        value="rate-limit",
    )

    with pytest.raises(
        ValueError,
        match=(
            "all provider evaluation evidence items "
            "must concern the collection subject"
        ),
    ):
        ExternalEvidenceProviderEvaluationEvidenceCollection(
            subject=collection_subject,
            evidence_items=(item,),
        )


def test_normalized_equivalent_subject_is_accepted() -> None:
    collection_subject = _subject(
        "provider-evaluation-subject-1"
    )
    item_subject = _subject(
        "  provider-evaluation-subject-1  "
    )
    item = _item(
        subject=item_subject,
        dimension=(
            ExternalEvidenceProviderEvaluationDimension
            .PROVENANCE_TRACEABILITY
        ),
        source_id="source-1",
        value=True,
    )

    collection = (
        ExternalEvidenceProviderEvaluationEvidenceCollection(
            subject=collection_subject,
            evidence_items=(item,),
        )
    )

    assert collection.evidence_items == (item,)


def test_multiple_evidence_items_for_same_dimension_are_allowed() -> None:
    subject = _subject()
    dimension = (
        ExternalEvidenceProviderEvaluationDimension
        .COMMERCIAL_CONSTRAINTS
    )
    first = _item(
        subject=subject,
        dimension=dimension,
        source_id="subject-document",
        value="usage-based",
        relationship=(
            ExternalEvidenceProviderEvaluationSourceRelationship
            .SUBJECT_SUPPLIED
        ),
    )
    second = _item(
        subject=subject,
        dimension=dimension,
        source_id="internal-observation",
        value="minimum-volume-observed",
        relationship=(
            ExternalEvidenceProviderEvaluationSourceRelationship
            .INTERNAL_OBSERVATION
        ),
    )

    collection = (
        ExternalEvidenceProviderEvaluationEvidenceCollection(
            subject=subject,
            evidence_items=(
                first,
                second,
            ),
        )
    )

    assert len(collection.evidence_items) == 2
    assert (
        collection.evidence_items[0].dimension
        is collection.evidence_items[1].dimension
    )
    assert (
        collection.evidence_items[0].provenance.source_id
        != collection.evidence_items[1].provenance.source_id
    )


def test_collection_does_not_merge_duplicate_items() -> None:
    subject = _subject()
    item = _item(
        subject=subject,
        dimension=(
            ExternalEvidenceProviderEvaluationDimension
            .ACCESS_SECURITY_REQUIREMENTS
        ),
        source_id="source-1",
        value="credential-required",
    )

    collection = (
        ExternalEvidenceProviderEvaluationEvidenceCollection(
            subject=subject,
            evidence_items=(
                item,
                item,
            ),
        )
    )

    assert collection.evidence_items == (
        item,
        item,
    )


def test_collection_is_immutable() -> None:
    subject = _subject()
    item = _item(
        subject=subject,
        dimension=(
            ExternalEvidenceProviderEvaluationDimension
            .ESTIMATE_STATUS_DISCLOSURE
        ),
        source_id="source-1",
        value=True,
    )
    collection = (
        ExternalEvidenceProviderEvaluationEvidenceCollection(
            subject=subject,
            evidence_items=(item,),
        )
    )

    with pytest.raises(FrozenInstanceError):
        collection.subject = _subject(
            "changed-subject"
        )


def test_collection_has_no_assessment_or_selection_surface() -> None:
    subject = _subject()
    item = _item(
        subject=subject,
        dimension=(
            ExternalEvidenceProviderEvaluationDimension
            .CANONICAL_PROJECTION_COMPATIBILITY
        ),
        source_id="source-1",
        value=True,
    )
    collection = (
        ExternalEvidenceProviderEvaluationEvidenceCollection(
            subject=subject,
            evidence_items=(item,),
        )
    )

    forbidden = (
        "complete",
        "coverage",
        "trust",
        "quality",
        "score",
        "weight",
        "rank",
        "comparison",
        "recommendation",
        "selection",
        "selected_provider",
        "registry",
        "acquisition_ready",
    )

    for name in forbidden:
        assert not hasattr(
            collection,
            name,
        )


def test_module_has_no_evaluation_or_execution_surface() -> None:
    forbidden = (
        "evaluate_provider",
        "compare_providers",
        "rank_providers",
        "select_provider",
        "register_provider",
        "deduplicate",
        "merge",
        "prioritize",
        "reconcile",
        "acquire",
        "execute",
        "request",
        "client",
        "credentials",
    )

    for name in forbidden:
        assert not hasattr(
            collection_module,
            name,
        )
