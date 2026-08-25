from app.services.cross_border import (
    external_evidence_provider_dimension_evidence as dimension_module,
)
from app.services.cross_border.external_evidence_provider_dimension_evidence import (
    evidence_items_for_dimension,
    usable_evidence_items_for_dimension,
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


def _subject() -> ExternalEvidenceProviderEvaluationSubject:
    return ExternalEvidenceProviderEvaluationSubject(
        subject_ref="provider-evaluation-subject-1",
    )


def _item(
    *,
    subject: ExternalEvidenceProviderEvaluationSubject,
    dimension: ExternalEvidenceProviderEvaluationDimension,
    state: EvidenceState,
    value: object,
    source_id: str,
) -> ExternalEvidenceProviderEvaluationEvidence:
    return ExternalEvidenceProviderEvaluationEvidence(
        subject=subject,
        dimension=dimension,
        source_relationship=(
            ExternalEvidenceProviderEvaluationSourceRelationship
            .THIRD_PARTY
        ),
        evidence=CrossBorderEvidence(
            state=state,
            value=value,
        ),
        provenance=EvidenceProvenance(
            source_id=source_id,
            source_type="evaluation-source",
        ),
    )


def _collection(
    *items: ExternalEvidenceProviderEvaluationEvidence,
) -> ExternalEvidenceProviderEvaluationEvidenceCollection:
    return ExternalEvidenceProviderEvaluationEvidenceCollection(
        subject=items[0].subject,
        evidence_items=items,
    )


def test_dimension_projection_preserves_matching_order() -> None:
    subject = _subject()
    target = (
        ExternalEvidenceProviderEvaluationDimension
        .GEOGRAPHIC_COVERAGE
    )
    first = _item(
        subject=subject,
        dimension=target,
        state=EvidenceState.OBSERVED,
        value="KR-US",
        source_id="source-1",
    )
    other = _item(
        subject=subject,
        dimension=(
            ExternalEvidenceProviderEvaluationDimension
            .TEMPORAL_EVIDENCE
        ),
        state=EvidenceState.OBSERVED,
        value=True,
        source_id="source-2",
    )
    second = _item(
        subject=subject,
        dimension=target,
        state=EvidenceState.VERIFIED,
        value="KR-US-CA",
        source_id="source-3",
    )

    result = evidence_items_for_dimension(
        _collection(
            first,
            other,
            second,
        ),
        target,
    )

    assert result == (
        first,
        second,
    )


def test_missing_dimension_returns_empty_tuple() -> None:
    subject = _subject()
    item = _item(
        subject=subject,
        dimension=(
            ExternalEvidenceProviderEvaluationDimension
            .EVIDENCE_KIND_COVERAGE
        ),
        state=EvidenceState.OBSERVED,
        value="currency-rate",
        source_id="source-1",
    )

    result = evidence_items_for_dimension(
        _collection(item),
        (
            ExternalEvidenceProviderEvaluationDimension
            .COMMERCIAL_CONSTRAINTS
        ),
    )

    assert result == ()
    assert isinstance(result, tuple)


def test_recorded_unknown_item_remains_present() -> None:
    subject = _subject()
    dimension = (
        ExternalEvidenceProviderEvaluationDimension
        .OPERATIONAL_CONSTRAINTS
    )
    unknown = _item(
        subject=subject,
        dimension=dimension,
        state=EvidenceState.UNKNOWN,
        value=None,
        source_id="source-1",
    )

    result = evidence_items_for_dimension(
        _collection(unknown),
        dimension,
    )

    assert result == (unknown,)
    assert result[0].evidence.state is EvidenceState.UNKNOWN


def test_usable_projection_excludes_unknown_only() -> None:
    subject = _subject()
    dimension = (
        ExternalEvidenceProviderEvaluationDimension
        .PROVENANCE_TRACEABILITY
    )
    verified = _item(
        subject=subject,
        dimension=dimension,
        state=EvidenceState.VERIFIED,
        value=True,
        source_id="source-1",
    )
    observed = _item(
        subject=subject,
        dimension=dimension,
        state=EvidenceState.OBSERVED,
        value=False,
        source_id="source-2",
    )
    estimated = _item(
        subject=subject,
        dimension=dimension,
        state=EvidenceState.ESTIMATED,
        value="partial",
        source_id="source-3",
    )
    unknown = _item(
        subject=subject,
        dimension=dimension,
        state=EvidenceState.UNKNOWN,
        value=None,
        source_id="source-4",
    )

    result = usable_evidence_items_for_dimension(
        _collection(
            verified,
            unknown,
            observed,
            estimated,
        ),
        dimension,
    )

    assert result == (
        verified,
        observed,
        estimated,
    )


def test_falsy_observed_values_remain_usable() -> None:
    subject = _subject()
    dimension = (
        ExternalEvidenceProviderEvaluationDimension
        .ESTIMATE_STATUS_DISCLOSURE
    )
    zero = _item(
        subject=subject,
        dimension=dimension,
        state=EvidenceState.OBSERVED,
        value=0,
        source_id="source-1",
    )
    false = _item(
        subject=subject,
        dimension=dimension,
        state=EvidenceState.OBSERVED,
        value=False,
        source_id="source-2",
    )
    empty_string = _item(
        subject=subject,
        dimension=dimension,
        state=EvidenceState.OBSERVED,
        value="",
        source_id="source-3",
    )

    result = usable_evidence_items_for_dimension(
        _collection(
            zero,
            false,
            empty_string,
        ),
        dimension,
    )

    assert result == (
        zero,
        false,
        empty_string,
    )


def test_duplicate_items_are_preserved() -> None:
    subject = _subject()
    dimension = (
        ExternalEvidenceProviderEvaluationDimension
        .ACCESS_SECURITY_REQUIREMENTS
    )
    item = _item(
        subject=subject,
        dimension=dimension,
        state=EvidenceState.OBSERVED,
        value="credential-required",
        source_id="source-1",
    )

    collection = _collection(
        item,
        item,
    )

    assert evidence_items_for_dimension(
        collection,
        dimension,
    ) == (
        item,
        item,
    )

    assert usable_evidence_items_for_dimension(
        collection,
        dimension,
    ) == (
        item,
        item,
    )


def test_projection_does_not_mutate_collection() -> None:
    subject = _subject()
    dimension = (
        ExternalEvidenceProviderEvaluationDimension
        .CANONICAL_PROJECTION_COMPATIBILITY
    )
    item = _item(
        subject=subject,
        dimension=dimension,
        state=EvidenceState.OBSERVED,
        value=True,
        source_id="source-1",
    )
    collection = _collection(item)
    before = collection.evidence_items

    evidence_items_for_dimension(
        collection,
        dimension,
    )
    usable_evidence_items_for_dimension(
        collection,
        dimension,
    )

    assert collection.evidence_items is before
    assert collection.evidence_items == (item,)


def test_module_introduces_no_presence_state() -> None:
    forbidden = (
        "EvidencePresenceState",
        "DimensionPresenceState",
        "PRESENT",
        "ABSENT",
        "COMPLETE",
        "INCOMPLETE",
    )

    for name in forbidden:
        assert not hasattr(
            dimension_module,
            name,
        )


def test_module_has_no_assessment_or_selection_surface() -> None:
    forbidden = (
        "evaluate_provider",
        "evaluate_completeness",
        "calculate_coverage",
        "compare_providers",
        "score_provider",
        "rank_providers",
        "recommend_provider",
        "select_provider",
        "register_provider",
        "acquire",
        "execute",
        "request",
        "client",
        "credentials",
    )

    for name in forbidden:
        assert not hasattr(
            dimension_module,
            name,
        )
