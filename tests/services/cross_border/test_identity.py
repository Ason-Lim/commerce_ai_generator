from dataclasses import FrozenInstanceError

import pytest

from app.services.cross_border.identity import (
    ProductIdentityRelationship,
    ProductRelationship,
)


def test_relationship_vocabulary_is_canonical():
    assert {
        member.name
        for member in ProductRelationship
    } == {
        "SAME_PRODUCT",
        "EQUIVALENT",
        "SUBSTITUTE",
        "RELATED",
        "UNKNOWN_RELATIONSHIP",
    }


@pytest.mark.parametrize(
    "relationship",
    [
        ProductRelationship.SAME_PRODUCT,
        ProductRelationship.EQUIVALENT,
        ProductRelationship.SUBSTITUTE,
        ProductRelationship.RELATED,
    ],
)
def test_known_relationship_is_resolved(relationship):
    evidence = ProductIdentityRelationship(
        relationship=relationship,
    )

    assert evidence.is_resolved is True


def test_unknown_relationship_is_not_resolved():
    evidence = ProductIdentityRelationship(
        relationship=ProductRelationship.UNKNOWN_RELATIONSHIP,
    )

    assert evidence.is_resolved is False


def test_relationship_can_preserve_external_references():
    evidence = ProductIdentityRelationship(
        relationship=ProductRelationship.SAME_PRODUCT,
        source_product_ref="kr:product:123",
        target_product_ref="us:product:456",
        authority="product_identity",
        evidence_ref="identity-evidence-001",
    )

    assert evidence.source_product_ref == "kr:product:123"
    assert evidence.target_product_ref == "us:product:456"
    assert evidence.authority == "product_identity"
    assert evidence.evidence_ref == "identity-evidence-001"


def test_relationship_evidence_is_immutable():
    evidence = ProductIdentityRelationship(
        relationship=ProductRelationship.RELATED,
    )

    with pytest.raises(FrozenInstanceError):
        evidence.relationship = ProductRelationship.SAME_PRODUCT


def test_contract_does_not_claim_general_identity_resolution():
    forbidden = {
        "resolve",
        "match",
        "normalize",
        "canonicalize",
    }

    public_names = {
        name.lower()
        for name in dir(ProductIdentityRelationship)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(public_names)
