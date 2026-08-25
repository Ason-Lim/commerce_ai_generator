from dataclasses import FrozenInstanceError

import pytest

from app.services.cross_border.external_evidence_provider_subject import (
    ExternalEvidenceProviderEvaluationSubject,
)


def test_subject_preserves_opaque_reference():
    subject = ExternalEvidenceProviderEvaluationSubject(
        subject_ref="provider-evaluation-subject-1",
    )

    assert (
        subject.subject_ref
        == "provider-evaluation-subject-1"
    )


def test_subject_normalizes_surrounding_whitespace():
    subject = ExternalEvidenceProviderEvaluationSubject(
        subject_ref="  provider-evaluation-subject-1  ",
    )

    assert (
        subject.subject_ref
        == "provider-evaluation-subject-1"
    )


@pytest.mark.parametrize(
    "subject_ref",
    [
        "",
        " ",
        "\t",
        "\n",
    ],
)
def test_subject_rejects_empty_reference(subject_ref):
    with pytest.raises(
        ValueError,
        match="evaluation subject_ref must not be empty",
    ):
        ExternalEvidenceProviderEvaluationSubject(
            subject_ref=subject_ref,
        )


def test_subject_is_immutable():
    subject = ExternalEvidenceProviderEvaluationSubject(
        subject_ref="provider-evaluation-subject-1",
    )

    with pytest.raises(FrozenInstanceError):
        subject.subject_ref = "changed"


def test_subject_does_not_claim_provider_identity_authority():
    subject = ExternalEvidenceProviderEvaluationSubject(
        subject_ref="provider-evaluation-subject-1",
    )

    forbidden = (
        "provider_id",
        "provider_name",
        "legal_entity",
        "account_id",
        "endpoint",
        "registry_id",
    )

    for name in forbidden:
        assert not hasattr(subject, name)


def test_subject_does_not_carry_evidence_or_provenance():
    subject = ExternalEvidenceProviderEvaluationSubject(
        subject_ref="provider-evaluation-subject-1",
    )

    forbidden = (
        "evidence",
        "provenance",
        "source_id",
        "source_type",
        "source_reference",
        "finding",
        "claim",
    )

    for name in forbidden:
        assert not hasattr(subject, name)


def test_subject_does_not_expose_selection_or_execution():
    subject = ExternalEvidenceProviderEvaluationSubject(
        subject_ref="provider-evaluation-subject-1",
    )

    forbidden = (
        "select",
        "rank",
        "recommend",
        "register",
        "acquire",
        "execute",
        "request",
        "client",
        "credentials",
    )

    for name in forbidden:
        assert not hasattr(subject, name)
