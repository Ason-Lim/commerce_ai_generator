from enum import Enum

from app.services.cross_border import (
    external_evidence_provider_evaluation as evaluation_module,
)
from app.services.cross_border.external_evidence_provider_evaluation import (
    ExternalEvidenceProviderEvaluationDimension,
)


def test_evaluation_dimension_vocabulary_is_exact():
    assert list(ExternalEvidenceProviderEvaluationDimension) == [
        (
            ExternalEvidenceProviderEvaluationDimension
            .EVIDENCE_KIND_COVERAGE
        ),
        (
            ExternalEvidenceProviderEvaluationDimension
            .GEOGRAPHIC_COVERAGE
        ),
        (
            ExternalEvidenceProviderEvaluationDimension
            .PROVENANCE_TRACEABILITY
        ),
        (
            ExternalEvidenceProviderEvaluationDimension
            .TEMPORAL_EVIDENCE
        ),
        (
            ExternalEvidenceProviderEvaluationDimension
            .ESTIMATE_STATUS_DISCLOSURE
        ),
        (
            ExternalEvidenceProviderEvaluationDimension
            .CANONICAL_PROJECTION_COMPATIBILITY
        ),
        (
            ExternalEvidenceProviderEvaluationDimension
            .OPERATIONAL_CONSTRAINTS
        ),
        (
            ExternalEvidenceProviderEvaluationDimension
            .ACCESS_SECURITY_REQUIREMENTS
        ),
        (
            ExternalEvidenceProviderEvaluationDimension
            .COMMERCIAL_CONSTRAINTS
        ),
    ]


def test_evaluation_dimension_values_are_stable():
    assert {
        dimension.value
        for dimension in ExternalEvidenceProviderEvaluationDimension
    } == {
        "evidence_kind_coverage",
        "geographic_coverage",
        "provenance_traceability",
        "temporal_evidence",
        "estimate_status_disclosure",
        "canonical_projection_compatibility",
        "operational_constraints",
        "access_security_requirements",
        "commercial_constraints",
    }


def test_evaluation_dimensions_are_string_enums():
    for dimension in ExternalEvidenceProviderEvaluationDimension:
        assert isinstance(dimension, str)
        assert isinstance(dimension, Enum)


def test_contract_has_no_provider_assessment_surface():
    forbidden = (
        "provider_id",
        "provider_name",
        "facts",
        "claims",
        "findings",
        "score",
        "weight",
        "rank",
        "select",
        "recommend",
    )

    for name in forbidden:
        assert not hasattr(
            ExternalEvidenceProviderEvaluationDimension,
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
        assert not hasattr(evaluation_module, name)
