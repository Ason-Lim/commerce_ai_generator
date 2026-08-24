from __future__ import annotations

from decimal import Decimal

import pytest

from app.services.cross_border.landed_cost import (
    LandedCostComponentState,
)
from app.services.cross_border.landed_cost_normalization import (
    normalize_landed_cost_component_evidence,
)
from app.services.cross_border.provenance import (
    EvidenceProvenance,
)


def _provenance() -> EvidenceProvenance:
    return EvidenceProvenance(
        source_id="provider-x",
        source_type="landed_cost_provider",
        record_id="quote-001",
    )


def test_normalizes_canonical_component_observation():
    result = normalize_landed_cost_component_evidence(
        component=" insurance ",
        state=LandedCostComponentState.ESTIMATED,
        amount="4.25",
        currency=" usd ",
        provenance=_provenance(),
        canonical_required=True,
    )

    assert result.component == "insurance"
    assert result.state is LandedCostComponentState.ESTIMATED
    assert result.amount == Decimal("4.25")
    assert result.currency == "USD"
    assert result.provenance == _provenance()


def test_open_vocabulary_preserves_provider_specific_component():
    result = normalize_landed_cost_component_evidence(
        component=" provider_remote_area_fee ",
        state=LandedCostComponentState.KNOWN,
        amount=12.5,
        currency="usd",
        provenance=_provenance(),
    )

    assert result.component == "provider_remote_area_fee"
    assert result.amount == Decimal("12.5")
    assert result.currency == "USD"


def test_canonical_required_rejects_provider_specific_component():
    with pytest.raises(
        ValueError,
        match="not canonical",
    ):
        normalize_landed_cost_component_evidence(
            component="provider_remote_area_fee",
            state=LandedCostComponentState.KNOWN,
            amount="12.50",
            currency="USD",
            canonical_required=True,
        )


def test_unknown_preserves_absence_without_manufacturing_zero():
    result = normalize_landed_cost_component_evidence(
        component="duty",
        state=LandedCostComponentState.UNKNOWN,
        amount=None,
        currency=None,
        provenance=_provenance(),
        canonical_required=True,
    )

    assert result.amount is None
    assert result.currency is None
    assert result.is_unknown


def test_unknown_rejects_manufactured_amount():
    with pytest.raises(
        ValueError,
        match="must not carry an amount",
    ):
        normalize_landed_cost_component_evidence(
            component="tax",
            state=LandedCostComponentState.UNKNOWN,
            amount="0",
            currency=None,
            canonical_required=True,
        )


def test_evidence_bearing_state_requires_currency():
    with pytest.raises(
        ValueError,
        match="requires currency",
    ):
        normalize_landed_cost_component_evidence(
            component="customs_fee",
            state=LandedCostComponentState.ESTIMATED,
            amount="5.00",
            canonical_required=True,
        )


@pytest.mark.parametrize(
    "amount",
    [
        "not-a-number",
        "NaN",
        "Infinity",
        "-Infinity",
    ],
)
def test_invalid_amount_is_rejected(amount):
    with pytest.raises(ValueError):
        normalize_landed_cost_component_evidence(
            component="service_fee",
            state=LandedCostComponentState.KNOWN,
            amount=amount,
            currency="USD",
        )


def test_negative_amount_remains_rejected_by_canonical_contract():
    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        normalize_landed_cost_component_evidence(
            component="service_fee",
            state=LandedCostComponentState.KNOWN,
            amount="-1.00",
            currency="USD",
        )


def test_blank_component_is_rejected():
    with pytest.raises(
        ValueError,
        match="must be non-empty",
    ):
        normalize_landed_cost_component_evidence(
            component="   ",
            state=LandedCostComponentState.UNKNOWN,
        )


def test_normalization_has_no_provider_schema_mapping_surface():
    import app.services.cross_border.landed_cost_normalization as module

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
