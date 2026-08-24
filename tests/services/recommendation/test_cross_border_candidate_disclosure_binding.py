from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from app.services.cross_border.landed_cost_aggregation import (
    LandedCostAggregationQuality,
    LandedCostAggregationState,
)
from app.services.cross_border.landed_cost_estimate_disclosure import (
    LandedCostEstimateDisclosureEvidence,
)
from app.services.cross_border.landed_cost_temporal_evaluation import (
    LandedCostTemporalEvaluationState,
)
from app.services.recommendation.cross_border_candidate_disclosure_binding import (
    CrossBorderCandidateDisclosureBinding,
    bind_cross_border_candidate_disclosures,
)
from app.services.recommendation.cross_border_candidate_reference_binding import (
    bind_cross_border_candidate_reference,
)
from app.services.recommendation.cross_border_candidate_reference_binding_set import (
    validate_cross_border_candidate_reference_bindings,
)


def _reference_set(*, reversed_order=False):
    first = bind_cross_border_candidate_reference(
        candidate_ref="candidate:first",
        candidate_position=1,
        binding_source="cross_border_handoff",
    )
    second = bind_cross_border_candidate_reference(
        candidate_ref="candidate:second",
        candidate_position=2,
        binding_source="cross_border_handoff",
    )

    supplied = (
        (second, first)
        if reversed_order
        else (first, second)
    )

    return validate_cross_border_candidate_reference_bindings(
        supplied
    )


def _disclosure(total: str):
    return LandedCostEstimateDisclosureEvidence(
        total=Decimal(total),
        currency="USD",
        aggregation_state=(
            LandedCostAggregationState.AGGREGATED
        ),
        aggregation_quality=(
            LandedCostAggregationQuality.ESTIMATED
        ),
        aggregation_reason="estimated landed cost",
        temporal_state=(
            LandedCostTemporalEvaluationState.EVALUABLE
        ),
        temporal_reason="currency evidence is fresh",
        fx_base_currency="USD",
        fx_quote_currency="KRW",
        fx_rate=Decimal("1390"),
        fx_retrieved_at="2026-08-24T07:00:00Z",
        fx_effective_at="2026-08-24T06:55:00Z",
    )


def test_binds_disclosures_by_explicit_candidate_position():
    first_disclosure = _disclosure("78.00")
    second_disclosure = _disclosure("92.00")

    result = bind_cross_border_candidate_disclosures(
        reference_bindings=_reference_set(),
        disclosures=(
            first_disclosure,
            second_disclosure,
        ),
    )

    assert result[0].candidate_ref == "candidate:first"
    assert result[0].candidate_position == 1
    assert result[0].disclosure is first_disclosure

    assert result[1].candidate_ref == "candidate:second"
    assert result[1].candidate_position == 2
    assert result[1].disclosure is second_disclosure


def test_reference_binding_tuple_order_does_not_define_position():
    first_disclosure = _disclosure("78.00")
    second_disclosure = _disclosure("92.00")

    result = bind_cross_border_candidate_disclosures(
        reference_bindings=_reference_set(
            reversed_order=True
        ),
        disclosures=(
            first_disclosure,
            second_disclosure,
        ),
    )

    assert result[0].candidate_position == 2
    assert result[0].candidate_ref == "candidate:second"
    assert result[0].disclosure is second_disclosure

    assert result[1].candidate_position == 1
    assert result[1].candidate_ref == "candidate:first"
    assert result[1].disclosure is first_disclosure


def test_binding_preserves_disclosure_object_without_copy_or_rewrite():
    disclosure = _disclosure("78.00")

    result = bind_cross_border_candidate_disclosures(
        reference_bindings=_reference_set(),
        disclosures=(
            disclosure,
            _disclosure("92.00"),
        ),
    )

    assert result[0].disclosure is disclosure
    assert result[0].disclosure.total == Decimal("78.00")
    assert result[0].disclosure.fx_rate == Decimal("1390")


@pytest.mark.parametrize(
    "disclosures",
    [
        (),
        (_disclosure("78.00"),),
        (
            _disclosure("78.00"),
            _disclosure("92.00"),
            _disclosure("110.00"),
        ),
    ],
)
def test_exactly_two_disclosures_are_required(disclosures):
    with pytest.raises(
        ValueError,
        match="exactly two disclosure evidence",
    ):
        bind_cross_border_candidate_disclosures(
            reference_bindings=_reference_set(),
            disclosures=disclosures,
        )


def test_candidate_disclosure_binding_is_immutable():
    result = bind_cross_border_candidate_disclosures(
        reference_bindings=_reference_set(),
        disclosures=(
            _disclosure("78.00"),
            _disclosure("92.00"),
        ),
    )

    assert isinstance(
        result[0],
        CrossBorderCandidateDisclosureBinding,
    )

    with pytest.raises(FrozenInstanceError):
        result[0].candidate_ref = "replacement"


def test_binding_does_not_expose_scoring_ranking_or_payment_authority():
    result = bind_cross_border_candidate_disclosures(
        reference_bindings=_reference_set(),
        disclosures=(
            _disclosure("78.00"),
            _disclosure("92.00"),
        ),
    )

    forbidden = {
        "score",
        "components",
        "rank",
        "winner",
        "recommended_route",
        "converted_total",
        "payment_fee",
        "payment_fx_fee",
        "card_fee",
        "checkout_total",
        "final_payment_amount",
        "display_text",
        "customer_notice",
    }

    public_names = {
        name.lower()
        for name in dir(result[0])
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(public_names)
