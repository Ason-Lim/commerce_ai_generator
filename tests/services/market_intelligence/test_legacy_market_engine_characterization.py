from __future__ import annotations

import pytest

from app.services.recommendation.market_engine import (
    DEFAULT_MARKET_INTELLIGENCE,
    build_buy_timing,
    build_market_intelligence,
    build_market_signal,
    calculate_market_score,
    classify_market_stage,
    normalize_market_intelligence,
    normalize_trend_direction,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, "flat"),
        ("", "flat"),
        ("up", "up"),
        ("rise", "up"),
        ("rising", "up"),
        ("increase", "up"),
        ("increasing", "up"),
        ("상승", "up"),
        ("down", "down"),
        ("fall", "down"),
        ("falling", "down"),
        ("decrease", "down"),
        ("decreasing", "down"),
        ("하락", "down"),
        ("flat", "flat"),
        ("stable", "flat"),
        ("steady", "flat"),
        ("neutral", "flat"),
        ("unknown", "flat"),
        ("보합", "flat"),
        ("유지", "flat"),
        ("unexpected-value", "flat"),
        (" UP ", "up"),
    ],
)
def test_normalize_trend_direction_characterization(
    raw,
    expected,
):
    assert normalize_trend_direction(raw) == expected


@pytest.mark.parametrize(
    ("score", "direction", "expected"),
    [
        (50, "flat", 53.0),
        (50, "up", 60.0),
        (50, "down", 40.0),
        (0, "down", 0.0),
        (100, "up", 100.0),
        (-20, "flat", 3.0),
        (120, "flat", 100.0),
        (None, "flat", 53.0),
        ("invalid", "flat", 53.0),
        ("25.5", "up", 35.5),
    ],
)
def test_calculate_market_score_characterization(
    score,
    direction,
    expected,
):
    assert calculate_market_score(
        score,
        direction,
    ) == expected


@pytest.mark.parametrize(
    ("score", "direction", "expected"),
    [
        (0, "up", "rising"),
        (100, "up", "rising"),
        (0, "down", "cooling"),
        (100, "down", "cooling"),
        (75, "flat", "stable_high"),
        (74.99, "flat", "stable"),
        (45, "flat", "stable"),
        (44.99, "flat", "low_interest"),
        (None, "flat", "stable"),
        ("invalid", "flat", "stable"),
    ],
)
def test_classify_market_stage_characterization(
    score,
    direction,
    expected,
):
    assert classify_market_stage(
        score,
        direction,
    ) == expected


@pytest.mark.parametrize(
    "stage",
    [
        "rising",
        "stable_high",
        "stable",
        "cooling",
        "low_interest",
    ],
)
def test_market_signal_is_defined_for_each_stage(stage):
    signal, message = build_market_signal(stage)

    assert isinstance(signal, str)
    assert signal
    assert isinstance(message, str)
    assert message


def test_unknown_market_signal_falls_back_to_stable():
    assert build_market_signal(
        "not-a-stage"
    ) == build_market_signal("stable")


@pytest.mark.parametrize(
    "stage",
    [
        "rising",
        "stable_high",
        "stable",
        "cooling",
        "low_interest",
    ],
)
def test_buy_timing_is_defined_for_each_stage(stage):
    timing, message = build_buy_timing(stage)

    assert isinstance(timing, str)
    assert timing
    assert isinstance(message, str)
    assert message


def test_unknown_buy_timing_falls_back_to_stable():
    assert build_buy_timing(
        "not-a-stage"
    ) == build_buy_timing("stable")


def test_build_market_intelligence_exact_legacy_shape():
    result = build_market_intelligence(
        search_interest=50,
        trend_direction="flat",
    )

    assert set(result) == {
        "market_score",
        "market_stage",
        "market_signal",
        "market_message",
        "buy_timing",
        "buy_timing_message",
        "search_interest",
        "trend_direction",
    }

    assert result["market_score"] == 53.0
    assert result["market_stage"] == "stable"
    assert result["search_interest"] == 50.0
    assert result["trend_direction"] == "flat"


@pytest.mark.parametrize(
    ("interest", "direction", "expected_interest", "expected_direction"),
    [
        (None, None, 50.0, "flat"),
        ("invalid", "invalid", 50.0, "flat"),
        (-1, "flat", 0.0, "flat"),
        (101, "flat", 100.0, "flat"),
        ("42.25", "상승", 42.25, "up"),
    ],
)
def test_build_market_intelligence_input_normalization(
    interest,
    direction,
    expected_interest,
    expected_direction,
):
    result = build_market_intelligence(
        interest,
        direction,
    )

    assert result["search_interest"] == expected_interest
    assert result["trend_direction"] == expected_direction


def test_build_market_intelligence_is_deterministic():
    first = build_market_intelligence(63.5, "up")
    second = build_market_intelligence(63.5, "up")

    assert first == second


def test_normalize_none_returns_legacy_defaults():
    result = normalize_market_intelligence(None)

    assert result == DEFAULT_MARKET_INTELLIGENCE
    assert result is not DEFAULT_MARKET_INTELLIGENCE


def test_normalize_partial_dictionary_preserves_defaults():
    result = normalize_market_intelligence(
        {
            "market_stage": "rising",
        }
    )

    assert result["market_stage"] == "rising"
    assert result["market_score"] == 50.0
    assert result["search_interest"] == 50.0
    assert result["trend_direction"] == "flat"


def test_normalize_none_field_does_not_override_default():
    result = normalize_market_intelligence(
        {
            "market_score": None,
            "market_stage": None,
            "trend_direction": None,
        }
    )

    assert result["market_score"] == 50.0
    assert result["market_stage"] == "stable"
    assert result["trend_direction"] == "flat"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (-1, 0.0),
        (101, 100.0),
        ("invalid", 50.0),
        ("72.25", 72.25),
    ],
)
def test_normalize_market_score_bounds(value, expected):
    result = normalize_market_intelligence(
        {
            "market_score": value,
        }
    )

    assert result["market_score"] == expected


def test_normalize_preserves_unknown_extra_fields():
    result = normalize_market_intelligence(
        {
            "future_compatibility_field": "preserve-me",
        }
    )

    assert (
        result["future_compatibility_field"]
        == "preserve-me"
    )


def test_normalize_does_not_mutate_input():
    source = {
        "market_score": "72.5",
        "trend_direction": "상승",
    }
    original = dict(source)

    normalize_market_intelligence(source)

    assert source == original
