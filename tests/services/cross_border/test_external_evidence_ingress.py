from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.external_evidence_ingress import (
    ExternalEvidenceIngress,
    ExternalEvidenceKind,
)
from app.services.cross_border.provenance import (
    EvidenceProvenance,
)


def _provenance() -> EvidenceProvenance:
    return EvidenceProvenance(
        source_id="provider-x",
        source_type="external_provider",
        record_id="record-001",
        retrieved_at="2026-08-25T09:00:00+09:00",
    )


def _context() -> CrossBorderEvaluationContext:
    return CrossBorderEvaluationContext(
        origin_country="KR",
        destination_country="US",
        currency="USD",
        evaluated_at="2026-08-25T09:05:00+09:00",
    )


def test_external_evidence_kind_has_bounded_projection_vocabulary():
    assert {
        kind.value
        for kind in ExternalEvidenceKind
    } == {
        "currency_rate",
        "shipping_route",
        "regulatory",
        "landed_cost_component",
    }


@pytest.mark.parametrize(
    "kind",
    list(ExternalEvidenceKind),
)
def test_ingress_preserves_projection_kind(kind):
    ingress = ExternalEvidenceIngress(
        kind=kind,
        provenance=_provenance(),
        context=_context(),
    )

    assert ingress.kind is kind


def test_ingress_preserves_existing_provenance_authority():
    provenance = _provenance()

    ingress = ExternalEvidenceIngress(
        kind=ExternalEvidenceKind.CURRENCY_RATE,
        provenance=provenance,
        context=_context(),
    )

    assert ingress.provenance is provenance
    assert ingress.provenance.source_id == "provider-x"
    assert ingress.provenance.record_id == "record-001"


def test_ingress_preserves_existing_context_authority():
    context = _context()

    ingress = ExternalEvidenceIngress(
        kind=ExternalEvidenceKind.SHIPPING_ROUTE,
        provenance=_provenance(),
        context=context,
    )

    assert ingress.context is context
    assert ingress.context.origin_country == "KR"
    assert ingress.context.destination_country == "US"


def test_ingress_is_immutable():
    ingress = ExternalEvidenceIngress(
        kind=ExternalEvidenceKind.REGULATORY,
        provenance=_provenance(),
        context=_context(),
    )

    with pytest.raises(FrozenInstanceError):
        ingress.kind = ExternalEvidenceKind.CURRENCY_RATE


def test_ingress_does_not_duplicate_existing_evidence_authorities():
    ingress = ExternalEvidenceIngress(
        kind=ExternalEvidenceKind.LANDED_COST_COMPONENT,
        provenance=_provenance(),
        context=_context(),
    )

    forbidden = {
        "provider_id",
        "source_id",
        "source_type",
        "record_id",
        "source_reference",
        "retrieved_at",
        "effective_at",
        "observed_at",
        "freshness",
        "state",
        "value",
        "raw_payload",
        "payload",
        "confidence",
        "http_status",
        "credentials",
    }

    assert forbidden.isdisjoint(
        set(vars(ingress))
    )


def test_ingress_does_not_expose_provider_specific_surface():
    import app.services.cross_border.external_evidence_ingress as module

    forbidden = {
        "dhl",
        "zonos",
        "fedex",
        "ups",
        "easypost",
        "hanjin",
        "ems",
    }

    public_names = {
        name.lower()
        for name in dir(module)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(public_names)
