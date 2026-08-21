from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.models import (
    CrossBorderEvidence,
    EvidenceState,
)
from app.services.cross_border.provenance import (
    EvidenceProvenance,
)
from app.services.cross_border.regulatory import (
    RegulatoryEvidence,
)


def build_context() -> CrossBorderEvaluationContext:
    return CrossBorderEvaluationContext(
        origin_country="KR",
        destination_country="US",
        market="US",
        currency="USD",
        evaluated_at="2026-08-21T12:00:00+00:00",
    )


def build_provenance() -> EvidenceProvenance:
    return EvidenceProvenance(
        source_id="regulatory-source",
        source_type="regulatory",
        record_id="reg-001",
        source_reference="external-regulatory-record",
        retrieved_at="2026-08-21T11:00:00+00:00",
    )


def test_verified_regulatory_evidence_preserves_observation():
    regulatory = RegulatoryEvidence(
        evidence=CrossBorderEvidence(
            state=EvidenceState.VERIFIED,
        ),
        provenance=build_provenance(),
        context=build_context(),
        observation="external regulatory observation",
    )

    assert (
        regulatory.observation
        == "external regulatory observation"
    )
    assert regulatory.has_observation is True


def test_observed_regulatory_evidence_preserves_observation():
    regulatory = RegulatoryEvidence(
        evidence=CrossBorderEvidence(
            state=EvidenceState.OBSERVED,
        ),
        provenance=build_provenance(),
        context=build_context(),
        observation="observed regulatory condition",
    )

    assert (
        regulatory.evidence.state
        is EvidenceState.OBSERVED
    )
    assert regulatory.has_observation is True


def test_estimated_regulatory_evidence_preserves_observation():
    regulatory = RegulatoryEvidence(
        evidence=CrossBorderEvidence(
            state=EvidenceState.ESTIMATED,
        ),
        provenance=build_provenance(),
        context=build_context(),
        observation="estimated regulatory condition",
    )

    assert (
        regulatory.evidence.state
        is EvidenceState.ESTIMATED
    )


def test_unknown_regulatory_evidence_has_no_observation():
    regulatory = RegulatoryEvidence(
        evidence=CrossBorderEvidence(
            state=EvidenceState.UNKNOWN,
        ),
        provenance=build_provenance(),
        context=build_context(),
    )

    assert regulatory.observation is None
    assert regulatory.has_observation is False


def test_unknown_regulatory_evidence_rejects_observation():
    with pytest.raises(
        ValueError,
        match=(
            "UNKNOWN regulatory evidence must not "
            "carry an observation"
        ),
    ):
        RegulatoryEvidence(
            evidence=CrossBorderEvidence(
                state=EvidenceState.UNKNOWN,
            ),
            provenance=build_provenance(),
            context=build_context(),
            observation="manufactured observation",
        )


def test_evidence_bearing_state_requires_observation():
    with pytest.raises(
        ValueError,
        match=(
            "evidence-bearing regulatory state "
            "requires an observation"
        ),
    ):
        RegulatoryEvidence(
            evidence=CrossBorderEvidence(
                state=EvidenceState.VERIFIED,
            ),
            provenance=build_provenance(),
            context=build_context(),
        )


def test_optional_fields_are_normalized():
    regulatory = RegulatoryEvidence(
        evidence=CrossBorderEvidence(
            state=EvidenceState.VERIFIED,
        ),
        provenance=build_provenance(),
        context=build_context(),
        observation="  regulatory observation  ",
        jurisdiction="  US  ",
        regulatory_reference="  ref-001  ",
    )

    assert (
        regulatory.observation
        == "regulatory observation"
    )
    assert regulatory.jurisdiction == "US"
    assert (
        regulatory.regulatory_reference
        == "ref-001"
    )


def test_blank_optional_fields_become_none():
    regulatory = RegulatoryEvidence(
        evidence=CrossBorderEvidence(
            state=EvidenceState.UNKNOWN,
        ),
        provenance=build_provenance(),
        context=build_context(),
        jurisdiction="   ",
        regulatory_reference="   ",
    )

    assert regulatory.jurisdiction is None
    assert regulatory.regulatory_reference is None


def test_regulatory_evidence_is_immutable():
    regulatory = RegulatoryEvidence(
        evidence=CrossBorderEvidence(
            state=EvidenceState.VERIFIED,
        ),
        provenance=build_provenance(),
        context=build_context(),
        observation="regulatory observation",
    )

    with pytest.raises(FrozenInstanceError):
        regulatory.observation = "changed"


def test_context_is_preserved():
    context = build_context()

    regulatory = RegulatoryEvidence(
        evidence=CrossBorderEvidence(
            state=EvidenceState.VERIFIED,
        ),
        provenance=build_provenance(),
        context=context,
        observation="regulatory observation",
    )

    assert regulatory.context is context
    assert regulatory.context.origin_country == "KR"
    assert regulatory.context.destination_country == "US"


def test_provenance_is_preserved():
    provenance = build_provenance()

    regulatory = RegulatoryEvidence(
        evidence=CrossBorderEvidence(
            state=EvidenceState.VERIFIED,
        ),
        provenance=provenance,
        context=build_context(),
        observation="regulatory observation",
    )

    assert regulatory.provenance is provenance
    assert (
        regulatory.provenance.source_id
        == "regulatory-source"
    )
