from dataclasses import FrozenInstanceError

import pytest

import app.services.recommendation.cross_border_price_signal_adapter as module
from app.services.recommendation.cross_border_price_signal_adapter import (
    CrossBorderPriceSignal,
    adapt_pairwise_landed_cost_to_price_signals,
)
from app.services.recommendation.price_utility import (
    calculate_price_utilities,
)


def test_first_cheaper_receives_higher_canonical_utility():
    first, second = adapt_pairwise_landed_cost_to_price_signals(
        100,
        200,
    )

    assert first == CrossBorderPriceSignal(
        landed_cost=100.0,
        utility=100.0,
        available=True,
    )

    assert second == CrossBorderPriceSignal(
        landed_cost=200.0,
        utility=0.0,
        available=True,
    )


def test_second_cheaper_receives_higher_canonical_utility():
    first, second = adapt_pairwise_landed_cost_to_price_signals(
        200,
        100,
    )

    assert first.utility == 0.0
    assert second.utility == 100.0

    assert first.available is True
    assert second.available is True


def test_equal_landed_costs_are_neutral():
    first, second = adapt_pairwise_landed_cost_to_price_signals(
        100,
        100,
    )

    assert first.utility == 50.0
    assert second.utility == 50.0

    assert first.available is True
    assert second.available is True


def test_missing_first_evidence_preserves_unavailability():
    first, second = adapt_pairwise_landed_cost_to_price_signals(
        None,
        100,
    )

    assert first.landed_cost is None
    assert first.utility == 0.0
    assert first.available is False

    assert second.landed_cost == 100.0
    assert second.utility == 50.0
    assert second.available is True


def test_missing_second_evidence_preserves_unavailability():
    first, second = adapt_pairwise_landed_cost_to_price_signals(
        100,
        None,
    )

    assert first.landed_cost == 100.0
    assert first.utility == 50.0
    assert first.available is True

    assert second.landed_cost is None
    assert second.utility == 0.0
    assert second.available is False


def test_observed_zero_utility_remains_available():
    _, second = adapt_pairwise_landed_cost_to_price_signals(
        100,
        200,
    )

    assert second.utility == 0.0
    assert second.available is True


def test_adapter_matches_canonical_price_utility_contract():
    landed_costs = (
        12345,
        23456,
    )

    expected = calculate_price_utilities(
        [
            {
                "price": landed_costs[0],
            },
            {
                "price": landed_costs[1],
            },
        ]
    )

    actual = adapt_pairwise_landed_cost_to_price_signals(
        *landed_costs
    )

    assert [
        (
            item.landed_cost,
            item.utility,
            item.available,
        )
        for item in actual
    ] == [
        (
            item.raw_price,
            item.utility,
            item.available,
        )
        for item in expected
    ]


def test_adapter_delegates_to_canonical_price_utility(
    monkeypatch,
):
    captured = {}

    def fake_calculate(candidates):
        captured["candidates"] = candidates

        return calculate_price_utilities(
            candidates
        )

    monkeypatch.setattr(
        module,
        "calculate_price_utilities",
        fake_calculate,
    )

    adapt_pairwise_landed_cost_to_price_signals(
        100,
        200,
    )

    assert captured["candidates"] == [
        {
            "price": 100,
        },
        {
            "price": 200,
        },
    ]


def test_signal_is_immutable():
    first, _ = adapt_pairwise_landed_cost_to_price_signals(
        100,
        200,
    )

    with pytest.raises(
        FrozenInstanceError,
    ):
        first.utility = 10.0


def test_result_has_no_ranking_or_transaction_surface():
    first, _ = adapt_pairwise_landed_cost_to_price_signals(
        100,
        200,
    )

    forbidden = {
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
    }

    public_names = {
        name.lower()
        for name in dir(first)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(
        public_names
    )
