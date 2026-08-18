import pytest

from app.services.recommendation.market_adapter import (
    adapt_canonical_market,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, 0.0),
        (25, 25.0),
        (50, 50.0),
        (75, 75.0),
        (100, 100.0),
    ],
)
def test_canonical_market_score_is_adapted(
    value,
    expected,
):
    result = adapt_canonical_market(
        {
            "market_score": value,
        }
    )
    assert result == expected


@pytest.mark.parametrize(
    "item",
    [
        {"trend_score": 90},
        {"trend_direction": "up"},
        {
            "trend_score": 90,
            "trend_direction": "up",
        },
        {"market_signal_score": 90},
        {"market_signal_score_final": 90},
        {"propagated_market_signal_score": 90},
        {"market_stage": "stable_high"},
        {
            "market_stage": "stable_high",
            "trend_score": 90,
        },
        {
            "rating": 4.9,
            "review_count": 10000,
            "purchase_count": 5000,
        },
    ],
)
def test_noncanonical_or_raw_market_evidence_is_not_adapted(
    item,
):
    result = adapt_canonical_market(item)
    assert result is None


def test_missing_market_evidence_is_unavailable():
    result = adapt_canonical_market({})
    assert result is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (-10, 0.0),
        (0, 0.0),
        (50, 50.0),
        (100, 100.0),
        (120, 100.0),
    ],
)
def test_market_score_is_clamped_to_canonical_range(
    value,
    expected,
):
    result = adapt_canonical_market(
        {
            "market_score": value,
        }
    )
    assert result == expected


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "not-a-score",
        object(),
    ],
)
def test_invalid_market_score_is_unavailable(
    value,
):
    result = adapt_canonical_market(
        {
            "market_score": value,
        }
    )
    assert result is None


@pytest.mark.parametrize(
    "value",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_nonfinite_market_score_is_unavailable(
    value,
):
    result = adapt_canonical_market(
        {
            "market_score": value,
        }
    )
    assert result is None


def test_zero_is_real_available_market_evidence():
    result = adapt_canonical_market(
        {
            "market_score": 0,
            "trend_score": 100,
        }
    )
    assert result == 0.0


def test_market_score_has_absolute_precedence_over_raw_inputs():
    result = adapt_canonical_market(
        {
            "market_score": 40,
            "trend_score": 100,
            "market_signal_score": 100,
            "market_signal_score_final": 100,
        }
    )
    assert result == 40.0


def test_adapter_is_deterministic():
    item = {
        "market_score": 72,
        "trend_score": 95,
        "trend_direction": "up",
    }

    first = adapt_canonical_market(item)
    second = adapt_canonical_market(item)

    assert first == second
