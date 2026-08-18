import pytest

from app.services.recommendation.popularity_adapter import (
    adapt_canonical_popularity,
)


@pytest.mark.parametrize(
    ("item", "expected"),
    [
        (
            {"popularity_score": 80},
            80.0,
        ),
        (
            {"reaction_score": 65},
            65.0,
        ),
    ],
)
def test_existing_derived_popularity_signals_are_adapted(
    item,
    expected,
):
    result = adapt_canonical_popularity(item)

    assert result == expected


def test_popularity_score_has_precedence_over_reaction_score():
    result = adapt_canonical_popularity(
        {
            "popularity_score": 80,
            "reaction_score": 60,
        }
    )

    assert result == 80.0


@pytest.mark.parametrize(
    "item",
    [
        {"click_count": 100},
        {"ctr_pct": 20},
        {
            "click_count": 100,
            "ctr_pct": 20,
        },
        {"review_count": 10000},
        {"rating": 4.9},
        {
            "rating": 4.9,
            "review_count": 10000,
        },
        {"purchase_count": 5000},
        {"market_signal_score": 90},
    ],
)
def test_raw_or_cross_axis_evidence_is_not_calculated_inline(
    item,
):
    result = adapt_canonical_popularity(item)

    assert result is None


def test_missing_popularity_evidence_is_unavailable():
    result = adapt_canonical_popularity({})

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
def test_popularity_is_clamped_to_canonical_range(
    value,
    expected,
):
    result = adapt_canonical_popularity(
        {
            "popularity_score": value,
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
def test_invalid_primary_signal_can_fall_through_to_valid_reaction(
    value,
):
    result = adapt_canonical_popularity(
        {
            "popularity_score": value,
            "reaction_score": 70,
        }
    )

    assert result == 70.0


def test_zero_is_real_available_evidence():
    result = adapt_canonical_popularity(
        {
            "popularity_score": 0,
            "reaction_score": 90,
        }
    )

    assert result == 0.0


def test_adapter_is_deterministic():
    item = {
        "popularity_score": 72,
        "reaction_score": 65,
    }

    first = adapt_canonical_popularity(item)
    second = adapt_canonical_popularity(item)

    assert first == second
