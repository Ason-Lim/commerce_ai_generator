from enum import Enum

from app.services.cross_border import (
    external_evidence_provider_source_relationship as relationship_module,
)
from app.services.cross_border.external_evidence_provider_source_relationship import (
    ExternalEvidenceProviderEvaluationSourceRelationship,
)


def test_source_relationship_vocabulary_is_exact():
    assert list(
        ExternalEvidenceProviderEvaluationSourceRelationship
    ) == [
        (
            ExternalEvidenceProviderEvaluationSourceRelationship
            .SUBJECT_SUPPLIED
        ),
        (
            ExternalEvidenceProviderEvaluationSourceRelationship
            .THIRD_PARTY
        ),
        (
            ExternalEvidenceProviderEvaluationSourceRelationship
            .INTERNAL_OBSERVATION
        ),
        (
            ExternalEvidenceProviderEvaluationSourceRelationship
            .UNKNOWN
        ),
    ]


def test_source_relationship_values_are_stable():
    assert {
        relationship.value
        for relationship
        in ExternalEvidenceProviderEvaluationSourceRelationship
    } == {
        "subject_supplied",
        "third_party",
        "internal_observation",
        "unknown",
    }


def test_source_relationships_are_string_enums():
    for relationship in (
        ExternalEvidenceProviderEvaluationSourceRelationship
    ):
        assert isinstance(relationship, str)
        assert isinstance(relationship, Enum)


def test_third_party_does_not_claim_independence():
    third_party = (
        ExternalEvidenceProviderEvaluationSourceRelationship
        .THIRD_PARTY
    )

    assert third_party.value == "third_party"
    assert "independent" not in third_party.value
    assert "verified" not in third_party.value


def test_relationship_contract_has_no_assessment_surface():
    forbidden = (
        "trust",
        "quality",
        "score",
        "weight",
        "rank",
        "select",
        "recommend",
        "verified",
        "reliable",
    )

    for name in forbidden:
        assert not hasattr(
            ExternalEvidenceProviderEvaluationSourceRelationship,
            name,
        )


def test_module_has_no_evaluation_execution_surface():
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
    )

    for name in forbidden:
        assert not hasattr(relationship_module, name)
