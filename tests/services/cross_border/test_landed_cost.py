from decimal import Decimal

import pytest

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.landed_cost import (
    LandedCostComponentEvidence,
    LandedCostComponentState,
)
from app.services.cross_border.provenance import (
    EvidenceProvenance,
)


def _context() -> CrossBorderEvaluationContext:
    return CrossBorderEvaluationContext(
        origin_country="KR",
        destination_country="US",
    )


def _provenance() -> EvidenceProvenance:
    return EvidenceProvenance(
        source_id="landed-cost-source-001",
        source_type="landed_cost_component",
    )


def test_known_component_preserves_amount_and_currency():
    evidence = LandedCostComponentEvidence(
        component="item_price",
        state=LandedCostComponentState.KNOWN,
        amount=Decimal("120.50"),
        currency="usd",
    )

    assert evidence.component == "item_price"
    assert evidence.amount == Decimal("120.50")
    assert evidence.currency == "USD"
    assert evidence.is_known is True
    assert evidence.has_amount is True
    assert evidence.is_zero is False


def test_known_zero_is_valid_evidence():
    evidence = LandedCostComponentEvidence(
        component="duty",
        state=LandedCostComponentState.KNOWN,
        amount=Decimal("0"),
        currency="USD",
    )

    assert evidence.has_amount is True
    assert evidence.is_zero is True
    assert evidence.is_unknown is False


@pytest.mark.parametrize(
    "state",
    [
        LandedCostComponentState.ESTIMATED,
        LandedCostComponentState.DERIVED,
    ],
)
def test_non_known_evidence_bearing_states_require_amount(
    state,
):
    evidence = LandedCostComponentEvidence(
        component="shipping",
        state=state,
        amount=Decimal("12.00"),
        currency="USD",
    )

    assert evidence.has_amount is True


@pytest.mark.parametrize(
    "state",
    [
        LandedCostComponentState.KNOWN,
        LandedCostComponentState.ESTIMATED,
        LandedCostComponentState.DERIVED,
    ],
)
def test_evidence_bearing_state_rejects_missing_amount(
    state,
):
    with pytest.raises(
        ValueError,
        match="requires an amount",
    ):
        LandedCostComponentEvidence(
            component="tax",
            state=state,
            currency="USD",
        )


@pytest.mark.parametrize(
    "state",
    [
        LandedCostComponentState.UNKNOWN,
        LandedCostComponentState.UNAVAILABLE,
        LandedCostComponentState.NOT_APPLICABLE,
    ],
)
def test_evidence_absent_state_has_no_amount_or_currency(
    state,
):
    evidence = LandedCostComponentEvidence(
        component="tax",
        state=state,
    )

    assert evidence.amount is None
    assert evidence.currency is None
    assert evidence.has_amount is False
    assert evidence.is_zero is False


@pytest.mark.parametrize(
    "state",
    [
        LandedCostComponentState.UNKNOWN,
        LandedCostComponentState.UNAVAILABLE,
        LandedCostComponentState.NOT_APPLICABLE,
    ],
)
def test_evidence_absent_state_rejects_zero_amount(
    state,
):
    with pytest.raises(
        ValueError,
        match="must not carry an amount",
    ):
        LandedCostComponentEvidence(
            component="duty",
            state=state,
            amount=Decimal("0"),
        )


def test_unknown_is_not_zero():
    evidence = LandedCostComponentEvidence(
        component="duty",
        state=LandedCostComponentState.UNKNOWN,
    )

    assert evidence.is_unknown is True
    assert evidence.is_zero is False
    assert evidence.has_amount is False


def test_negative_amount_is_rejected():
    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        LandedCostComponentEvidence(
            component="shipping",
            state=LandedCostComponentState.KNOWN,
            amount=Decimal("-1"),
            currency="USD",
        )


def test_evidence_bearing_state_requires_currency():
    with pytest.raises(
        ValueError,
        match="requires currency",
    ):
        LandedCostComponentEvidence(
            component="item_price",
            state=LandedCostComponentState.KNOWN,
            amount=Decimal("10"),
        )


def test_component_and_currency_are_normalized():
    evidence = LandedCostComponentEvidence(
        component="  service_fee  ",
        state=LandedCostComponentState.KNOWN,
        amount=Decimal("2.50"),
        currency=" krw ",
    )

    assert evidence.component == "service_fee"
    assert evidence.currency == "KRW"


def test_empty_component_is_rejected():
    with pytest.raises(
        ValueError,
        match="component must be non-empty",
    ):
        LandedCostComponentEvidence(
            component="   ",
            state=LandedCostComponentState.UNKNOWN,
        )


def test_component_can_bind_canonical_provenance():
    provenance = _provenance()

    evidence = LandedCostComponentEvidence(
        component="shipping",
        state=LandedCostComponentState.KNOWN,
        amount=Decimal("12.00"),
        currency="USD",
        provenance=provenance,
    )

    assert evidence.provenance is provenance
    assert (
        evidence.provenance.source_id
        == "landed-cost-source-001"
    )


def test_component_can_bind_canonical_context():
    context = _context()

    evidence = LandedCostComponentEvidence(
        component="tax",
        state=LandedCostComponentState.UNKNOWN,
        context=context,
    )

    assert evidence.context is context
    assert evidence.context.origin_country == "KR"
    assert evidence.context.destination_country == "US"


def test_zero_component_preserves_provenance_and_context():
    provenance = _provenance()
    context = _context()

    evidence = LandedCostComponentEvidence(
        component="duty",
        state=LandedCostComponentState.KNOWN,
        amount=Decimal("0"),
        currency="USD",
        provenance=provenance,
        context=context,
    )

    assert evidence.is_zero is True
    assert evidence.provenance is provenance
    assert evidence.context is context


def test_unknown_component_can_preserve_provenance():
    provenance = _provenance()

    evidence = LandedCostComponentEvidence(
        component="tax",
        state=LandedCostComponentState.UNKNOWN,
        provenance=provenance,
    )

    assert evidence.is_unknown is True
    assert evidence.provenance is provenance


def test_unknown_component_can_preserve_context():
    context = _context()

    evidence = LandedCostComponentEvidence(
        component="tax",
        state=LandedCostComponentState.UNKNOWN,
        context=context,
    )

    assert evidence.is_unknown is True
    assert evidence.context is context


def test_contract_has_no_calculation_authority():
    forbidden = {
        "calculate_landed_cost",
        "calculate_duty",
        "calculate_tax",
        "convert_currency",
        "recommend_route",
        "select_route",
    }

    public_names = {
        name.lower()
        for name in dir(
            LandedCostComponentEvidence
        )
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(
        public_names
    )


def test_canonical_landed_cost_component_vocabulary_is_explicit():
    from app.services.cross_border.landed_cost import (
        CANONICAL_LANDED_COST_COMPONENTS,
    )

    assert CANONICAL_LANDED_COST_COMPONENTS == frozenset(
        {
            "item_price",
            "origin_shipping",
            "international_shipping",
            "shipping",
            "forwarding",
            "consolidation",
            "insurance",
            "duty",
            "tax",
            "customs_fee",
            "service_fee",
            "payment_fee",
            "payment_fx_fee",
            "discount",
            "surcharge",
        }
    )


def test_canonical_component_helper_normalizes_outer_whitespace():
    from app.services.cross_border.landed_cost import (
        is_canonical_landed_cost_component,
    )

    assert is_canonical_landed_cost_component(
        "  insurance  "
    )


def test_open_component_contract_allows_provider_specific_component():
    evidence = LandedCostComponentEvidence(
        component="provider_remote_area_fee",
        state=LandedCostComponentState.KNOWN,
        amount=Decimal("12.50"),
        currency="USD",
    )

    assert (
        evidence.component
        == "provider_remote_area_fee"
    )


def test_provider_specific_component_is_not_canonical_but_remains_valid():
    from app.services.cross_border.landed_cost import (
        is_canonical_landed_cost_component,
    )

    component = "provider_remote_area_fee"

    assert not is_canonical_landed_cost_component(
        component
    )

    evidence = LandedCostComponentEvidence(
        component=component,
        state=LandedCostComponentState.ESTIMATED,
        amount=Decimal("8.25"),
        currency="USD",
    )

    assert evidence.component == component
