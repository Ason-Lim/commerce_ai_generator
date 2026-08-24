from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

import app.services.recommendation.cross_border_bound_price_signal_composition as module
from app.services.recommendation.cross_border_bound_price_signal_composition import (
    BoundCrossBorderPriceSignals,
    compose_bound_cross_border_price_signals,
)
from app.services.recommendation.cross_border_price_signal_adapter import (
    CrossBorderPriceSignal,
)
from app.services.recommendation.cross_border_scoring_binding import (
    BoundCrossBorderScoringInput,
    CrossBorderScoringDirection,
)


def _input(
    *,
    first=Decimal("100"),
    second=Decimal("200"),
    direction=CrossBorderScoringDirection.FIRST,
):
    return BoundCrossBorderScoringInput(
        first_candidate_ref="candidate-a",
        second_candidate_ref="candidate-b",
        first_landed_cost=first,
        second_landed_cost=second,
        currency="KRW",
        direction=direction,
        first_evidence_quality="authoritative",
        second_evidence_quality="authoritative",
        source_schema_id="cross-border-test",
        source_schema_version="1.0",
    )


def test_first_candidate_alignment_is_preserved():
    scoring_input = _input()

    result = compose_bound_cross_border_price_signals(
        scoring_input
    )

    assert result.scoring_input is scoring_input

    assert result.first_price == CrossBorderPriceSignal(
        landed_cost=100.0,
        utility=100.0,
        available=True,
    )

    assert result.second_price == CrossBorderPriceSignal(
        landed_cost=200.0,
        utility=0.0,
        available=True,
    )


def test_second_candidate_alignment_is_preserved():
    scoring_input = _input(
        first=Decimal("200"),
        second=Decimal("100"),
        direction=CrossBorderScoringDirection.SECOND,
    )

    result = compose_bound_cross_border_price_signals(
        scoring_input
    )

    assert result.first_price.utility == 0.0
    assert result.second_price.utility == 100.0

    assert (
        result.scoring_input.first_candidate_ref
        == "candidate-a"
    )

    assert (
        result.scoring_input.second_candidate_ref
        == "candidate-b"
    )


def test_equal_landed_costs_remain_neutral():
    scoring_input = _input(
        first=Decimal("100"),
        second=Decimal("100"),
        direction=CrossBorderScoringDirection.EQUAL,
    )

    result = compose_bound_cross_border_price_signals(
        scoring_input
    )

    assert result.first_price.utility == 50.0
    assert result.second_price.utility == 50.0


def test_composition_delegates_exact_landed_cost_values(
    monkeypatch,
):
    scoring_input = _input(
        first=Decimal("123.45"),
        second=Decimal("678.90"),
    )

    captured = {}

    expected = (
        CrossBorderPriceSignal(
            landed_cost=123.45,
            utility=100.0,
            available=True,
        ),
        CrossBorderPriceSignal(
            landed_cost=678.90,
            utility=0.0,
            available=True,
        ),
    )

    def fake_adapter(first, second):
        captured["first"] = first
        captured["second"] = second
        return expected

    monkeypatch.setattr(
        module,
        "adapt_pairwise_landed_cost_to_price_signals",
        fake_adapter,
    )

    result = compose_bound_cross_border_price_signals(
        scoring_input
    )

    assert captured["first"] is (
        scoring_input.first_landed_cost
    )

    assert captured["second"] is (
        scoring_input.second_landed_cost
    )

    assert result.first_price is expected[0]
    assert result.second_price is expected[1]


def test_composition_does_not_reinterpret_direction():
    scoring_input = _input(
        first=Decimal("100"),
        second=Decimal("200"),
        direction=CrossBorderScoringDirection.SECOND,
    )

    result = compose_bound_cross_border_price_signals(
        scoring_input
    )

    assert (
        result.scoring_input.direction
        is CrossBorderScoringDirection.SECOND
    )

    # Price semantics follow the monetary evidence.
    # This composition does not rewrite or enforce direction.
    assert result.first_price.utility == 100.0
    assert result.second_price.utility == 0.0


def test_result_is_immutable():
    result = compose_bound_cross_border_price_signals(
        _input()
    )

    with pytest.raises(
        FrozenInstanceError,
    ):
        result.first_price = result.second_price


def test_result_type_is_bounded_composition_contract():
    result = compose_bound_cross_border_price_signals(
        _input()
    )

    assert isinstance(
        result,
        BoundCrossBorderPriceSignals,
    )


def test_result_has_no_scoring_ranking_or_transaction_surface():
    result = compose_bound_cross_border_price_signals(
        _input()
    )

    forbidden = {
        "final_score",
        "score",
        "rank",
        "ranking",
        "winner",
        "selected_candidate",
        "best_candidate",
        "checkout",
        "payment",
        "purchase",
        "dispatch",
        "book_shipment",
        "production_enabled",
        "rollout_started",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(
        public_names
    )
