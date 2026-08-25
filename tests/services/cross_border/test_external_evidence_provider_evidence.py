from dataclasses import FrozenInstanceError

import pytest

from app.services.cross_border import (
    external_evidence_provider_evidence as evidence_module,
)
from app.services.cross_border.external_evidence_provider_evaluation import (
    ExternalEvidenceProviderEvaluationDimension,
)
from app.services.cross_border.external_evidence_provider_evidence import (
    ExternalEvidenceProviderEvaluationEvidence,
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


def _provenance() -> EvidenceProvenance:
    return EvidenceProvenance(
        source_id="evidence-source-1",
        source_type="provider-documentation",
    )


def _binding(
    *,
    state: EvidenceState = EvidenceState.OBSERVED,
    value: object = "documented",
    source_relationship: (
        ExternalEvidenceProviderEvaluationSourceRelationship
    ) = (
        ExternalEvidenceProviderEvaluationSourceRelationship
        .SUBJECT_SUPPLIED
    ),
) -> ExternalEvidenceProviderEvaluationEvidence:
    return ExternalEvidenceProviderEvaluationEvidence(
        subject=_subject(),
        dimension=(
            ExternalEvidenceProviderEvaluationDimension
            .EVIDENCE_KIND_COVERAGE
        ),
        source_relationship=source_relationship,
        evidence=CrossBorderEvidence(
            state=state,
            value=value,
        ),
        provenance=_provenance(),
    )


def test_binding_preserves_existing_contract_instances() -> None:
    subject = _subject()
    dimension = (
        ExternalEvidenceProviderEvaluationDimension
        .PROVENANCE_TRACEABILITY
    )
    relationship = (
        ExternalEvidenceProviderEvaluationSourceRelationship
        .THIRD_PARTY
    )
    evidence = CrossBorderEvidence(
        state=EvidenceState.VERIFIED,
        value={"traceable": True},
    )
    provenance = _provenance()

    binding = ExternalEvidenceProviderEvaluationEvidence(
        subject=subject,
        dimension=dimension,
        source_relationship=relationship,
        evidence=evidence,
        provenance=provenance,
    )

    assert binding.subject is subject
    assert binding.dimension is dimension
    assert binding.source_relationship is relationship
    assert binding.evidence is evidence
    assert binding.provenance is provenance


def test_subject_and_provenance_source_remain_distinct() -> None:
    binding = _binding()

    assert (
        binding.subject.subject_ref
        == "provider-evaluation-subject-1"
    )
    assert binding.provenance.source_id == "evidence-source-1"
    assert (
        binding.subject.subject_ref
        != binding.provenance.source_id
    )


def test_unknown_evidence_with_none_is_preserved() -> None:
    binding = _binding(
        state=EvidenceState.UNKNOWN,
        value=None,
        source_relationship=(
            ExternalEvidenceProviderEvaluationSourceRelationship
            .UNKNOWN
        ),
    )

    assert binding.evidence.state is EvidenceState.UNKNOWN
    assert binding.evidence.value is None


@pytest.mark.parametrize(
    "value",
    [
        0,
        False,
        "",
        "manufactured",
    ],
)
def test_unknown_evidence_rejects_observation_value(
    value: object,
) -> None:
    with pytest.raises(
        ValueError,
        match="UNKNOWN evaluation evidence must not carry a value",
    ):
        _binding(
            state=EvidenceState.UNKNOWN,
            value=value,
        )


@pytest.mark.parametrize(
    "state",
    [
        EvidenceState.VERIFIED,
        EvidenceState.OBSERVED,
        EvidenceState.ESTIMATED,
    ],
)
def test_evidence_bearing_state_rejects_missing_value(
    state: EvidenceState,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "evidence-bearing evaluation evidence "
            "must carry a value"
        ),
    ):
        _binding(
            state=state,
            value=None,
        )


@pytest.mark.parametrize(
    "value",
    [
        0,
        False,
        "",
    ],
)
def test_falsy_values_remain_valid_observations(
    value: object,
) -> None:
    binding = _binding(
        state=EvidenceState.OBSERVED,
        value=value,
    )

    assert binding.evidence.value == value


@pytest.mark.parametrize(
    "relationship",
    list(
        ExternalEvidenceProviderEvaluationSourceRelationship
    ),
)
def test_source_relationship_does_not_determine_evidence_state(
    relationship: (
        ExternalEvidenceProviderEvaluationSourceRelationship
    ),
) -> None:
    binding = _binding(
        state=EvidenceState.OBSERVED,
        value=False,
        source_relationship=relationship,
    )

    assert binding.evidence.state is EvidenceState.OBSERVED
    assert binding.evidence.value is False


def test_binding_is_immutable() -> None:
    binding = _binding()

    with pytest.raises(FrozenInstanceError):
        binding.dimension = (
            ExternalEvidenceProviderEvaluationDimension
            .GEOGRAPHIC_COVERAGE
        )


def test_binding_has_no_assessment_or_provider_authority() -> None:
    binding = _binding()

    forbidden = (
        "provider_id",
        "provider_name",
        "trust",
        "quality",
        "score",
        "weight",
        "rank",
        "comparison",
        "recommendation",
        "selection",
        "registry",
        "raw_payload",
    )

    for name in forbidden:
        assert not hasattr(binding, name)


def test_module_has_no_execution_surface() -> None:
    forbidden = (
        "evaluate_provider",
        "compare_providers",
        "rank_providers",
        "select_provider",
        "register_provider",
        "acquire",
        "execute",
        "request",
        "client",
        "credentials",
    )

    for name in forbidden:
        assert not hasattr(evidence_module, name)
