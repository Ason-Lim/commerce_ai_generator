from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import timedelta

import pytest

from app.services.cross_border import (
    CrossBorderEvaluationContext,
    CrossBorderEvidence,
    EvidenceFreshness,
    EvidenceFreshnessState,
    EvidenceProvenance,
    EvidenceState,
    ProductIdentityEvidenceBinding,
    ProductIdentityRelationship,
    ProductRelationship,
)


def _context(
    destination_country: str = "US",
) -> CrossBorderEvaluationContext:
    return CrossBorderEvaluationContext(
        origin_country="KR",
        destination_country=destination_country,
        market="market-001",
        currency="USD",
        evaluated_at="2026-08-21T23:20:00+09:00",
    )


def _provenance() -> EvidenceProvenance:
    return EvidenceProvenance(
        source_id="identity-authority-001",
        source_type="product_identity",
        record_id="identity-record-001",
        retrieved_at="2026-08-21T23:19:00+09:00",
        effective_at="2026-08-21T23:18:00+09:00",
    )


def _relationship(
    relationship: ProductRelationship = (
        ProductRelationship.SAME_PRODUCT
    ),
) -> ProductIdentityRelationship:
    return ProductIdentityRelationship(
        relationship=relationship,
        source_product_ref="kr:product:123",
        target_product_ref="us:product:456",
        authority="product_identity",
        evidence_ref="identity-record-001",
    )


def _evidence(
    state: EvidenceState = EvidenceState.VERIFIED,
) -> CrossBorderEvidence:
    return CrossBorderEvidence(
        state=state,
        value="identity-record-001",
        source="product_identity",
        observed_at="2026-08-21T23:18:00+09:00",
    )


def test_binding_preserves_relationship() -> None:
    relationship = _relationship()

    binding = ProductIdentityEvidenceBinding(
        relationship=relationship,
        evidence=_evidence(),
        provenance=_provenance(),
        context=_context(),
    )

    assert binding.relationship == relationship
    assert (
        binding.relationship.relationship
        is ProductRelationship.SAME_PRODUCT
    )


def test_binding_preserves_evidence() -> None:
    evidence = _evidence(
        EvidenceState.OBSERVED
    )

    binding = ProductIdentityEvidenceBinding(
        relationship=_relationship(),
        evidence=evidence,
        provenance=_provenance(),
        context=_context(),
    )

    assert binding.evidence == evidence
    assert (
        binding.evidence.state
        is EvidenceState.OBSERVED
    )


def test_binding_preserves_provenance() -> None:
    provenance = _provenance()

    binding = ProductIdentityEvidenceBinding(
        relationship=_relationship(),
        evidence=_evidence(),
        provenance=provenance,
        context=_context(),
    )

    assert binding.provenance == provenance
    assert (
        binding.provenance.source_id
        == "identity-authority-001"
    )
    assert (
        binding.provenance.record_id
        == "identity-record-001"
    )


def test_binding_preserves_evaluation_context() -> None:
    context = _context(
        destination_country="JP"
    )

    binding = ProductIdentityEvidenceBinding(
        relationship=_relationship(),
        evidence=_evidence(),
        provenance=_provenance(),
        context=context,
    )

    assert binding.context == context
    assert (
        binding.context.destination_country
        == "JP"
    )


def test_binding_can_preserve_existing_freshness_result() -> None:
    freshness = EvidenceFreshness(
        state=EvidenceFreshnessState.FRESH,
        evidence_at="2026-08-21T23:18:00+09:00",
        age=timedelta(minutes=2),
    )

    binding = ProductIdentityEvidenceBinding(
        relationship=_relationship(),
        evidence=_evidence(),
        provenance=_provenance(),
        context=_context(),
        freshness=freshness,
    )

    assert binding.freshness == freshness
    assert (
        binding.freshness.state
        is EvidenceFreshnessState.FRESH
    )


def test_freshness_is_optional() -> None:
    binding = ProductIdentityEvidenceBinding(
        relationship=_relationship(),
        evidence=_evidence(),
        provenance=_provenance(),
        context=_context(),
    )

    assert binding.freshness is None


@pytest.mark.parametrize(
    "state",
    [
        EvidenceState.VERIFIED,
        EvidenceState.OBSERVED,
        EvidenceState.ESTIMATED,
    ],
)
def test_resolved_relationship_accepts_evidence_bearing_state(
    state: EvidenceState,
) -> None:
    binding = ProductIdentityEvidenceBinding(
        relationship=_relationship(),
        evidence=_evidence(state),
        provenance=_provenance(),
        context=_context(),
    )

    assert binding.relationship_is_resolved is True
    assert binding.evidence_is_usable is True


def test_resolved_relationship_rejects_unknown_evidence() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "resolved product relationship requires "
            "evidence-bearing state"
        ),
    ):
        ProductIdentityEvidenceBinding(
            relationship=_relationship(),
            evidence=_evidence(
                EvidenceState.UNKNOWN
            ),
            provenance=_provenance(),
            context=_context(),
        )


def test_unknown_relationship_can_preserve_unknown_evidence() -> None:
    binding = ProductIdentityEvidenceBinding(
        relationship=_relationship(
            ProductRelationship.UNKNOWN_RELATIONSHIP
        ),
        evidence=_evidence(
            EvidenceState.UNKNOWN
        ),
        provenance=_provenance(),
        context=_context(),
    )

    assert binding.relationship_is_resolved is False
    assert binding.evidence_is_usable is False


def test_unknown_relationship_can_have_observed_evidence() -> None:
    binding = ProductIdentityEvidenceBinding(
        relationship=_relationship(
            ProductRelationship.UNKNOWN_RELATIONSHIP
        ),
        evidence=_evidence(
            EvidenceState.OBSERVED
        ),
        provenance=_provenance(),
        context=_context(),
    )

    assert binding.relationship_is_resolved is False
    assert binding.evidence_is_usable is True


def test_destination_specific_bindings_remain_distinct() -> None:
    us_binding = ProductIdentityEvidenceBinding(
        relationship=_relationship(),
        evidence=_evidence(),
        provenance=_provenance(),
        context=_context("US"),
    )

    jp_binding = ProductIdentityEvidenceBinding(
        relationship=_relationship(),
        evidence=_evidence(),
        provenance=_provenance(),
        context=_context("JP"),
    )

    assert us_binding != jp_binding
    assert (
        us_binding.context.destination_country
        != jp_binding.context.destination_country
    )


def test_binding_is_immutable() -> None:
    binding = ProductIdentityEvidenceBinding(
        relationship=_relationship(),
        evidence=_evidence(),
        provenance=_provenance(),
        context=_context(),
    )

    with pytest.raises(FrozenInstanceError):
        binding.relationship = _relationship(
            ProductRelationship.RELATED
        )


def test_binding_does_not_expose_identity_resolution_authority() -> None:
    forbidden = {
        "resolve",
        "match",
        "normalize",
        "canonicalize",
    }

    public_names = {
        name.lower()
        for name in dir(
            ProductIdentityEvidenceBinding
        )
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(
        public_names
    )
