import pytest

from app.services.cross_border.external_evidence_ingress import (
    ExternalEvidenceKind,
)
from app.services.cross_border.external_evidence_projection import (
    CanonicalProjectionTarget,
    ExternalEvidenceProjectionEligibility,
    projection_target_for,
)


@pytest.mark.parametrize(
    ("kind", "target"),
    [
        (
            ExternalEvidenceKind.CURRENCY_RATE,
            CanonicalProjectionTarget.CURRENCY_RATE_EVIDENCE,
        ),
        (
            ExternalEvidenceKind.SHIPPING_ROUTE,
            CanonicalProjectionTarget.SHIPPING_ROUTE_EVIDENCE,
        ),
        (
            ExternalEvidenceKind.REGULATORY,
            CanonicalProjectionTarget.REGULATORY_EVIDENCE,
        ),
        (
            ExternalEvidenceKind.LANDED_COST_COMPONENT,
            CanonicalProjectionTarget.LANDED_COST_COMPONENT_EVIDENCE,
        ),
    ],
)
def test_maps_each_external_kind_to_one_canonical_target(
    kind,
    target,
):
    assert projection_target_for(kind) is target


@pytest.mark.parametrize(
    "kind",
    list(ExternalEvidenceKind),
)
def test_projection_eligibility_accepts_only_matching_target(
    kind,
):
    target = projection_target_for(kind)

    eligibility = ExternalEvidenceProjectionEligibility(
        kind=kind,
        target=target,
    )

    assert eligibility.kind is kind
    assert eligibility.target is target


def test_projection_eligibility_rejects_mismatched_target():
    with pytest.raises(
        ValueError,
        match="canonical projection target does not match",
    ):
        ExternalEvidenceProjectionEligibility(
            kind=ExternalEvidenceKind.CURRENCY_RATE,
            target=(
                CanonicalProjectionTarget
                .REGULATORY_EVIDENCE
            ),
        )


def test_projection_lookup_rejects_non_kind_values():
    with pytest.raises(
        TypeError,
        match="kind must be an ExternalEvidenceKind",
    ):
        projection_target_for("currency_rate")


def test_contract_does_not_expose_executable_projector():
    eligibility = ExternalEvidenceProjectionEligibility(
        kind=ExternalEvidenceKind.CURRENCY_RATE,
        target=(
            CanonicalProjectionTarget
            .CURRENCY_RATE_EVIDENCE
        ),
    )

    assert not hasattr(eligibility, "project")
    assert not hasattr(eligibility, "execute")
    assert not hasattr(eligibility, "normalize")
    assert not hasattr(eligibility, "adapter")
