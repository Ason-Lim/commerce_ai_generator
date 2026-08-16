from __future__ import annotations

import pytest

from app.services.market_intelligence import (
    DEFAULT_MARKET_INTELLIGENCE as NEW_DEFAULTS,
)
from app.services.market_intelligence import (
    build_buy_timing as new_build_buy_timing,
)
from app.services.market_intelligence import (
    build_market_intelligence as new_build_market_intelligence,
)
from app.services.market_intelligence import (
    build_market_signal as new_build_market_signal,
)
from app.services.market_intelligence import (
    calculate_market_score as new_calculate_market_score,
)
from app.services.market_intelligence import (
    classify_market_stage as new_classify_market_stage,
)
from app.services.market_intelligence import (
    normalize_market_intelligence as new_normalize_market_intelligence,
)
from app.services.market_intelligence import (
    normalize_trend_direction as new_normalize_trend_direction,
)

from app.services.recommendation.market_engine import (
    DEFAULT_MARKET_INTELLIGENCE as LEGACY_DEFAULTS,
)
from app.services.recommendation.market_engine import (
    build_buy_timing as legacy_build_buy_timing,
)
from app.services.recommendation.market_engine import (
    build_market_intelligence as legacy_build_market_intelligence,
)
from app.services.recommendation.market_engine import (
    build_market_signal as legacy_build_market_signal,
)
from app.services.recommendation.market_engine import (
    calculate_market_score as legacy_calculate_market_score,
)
from app.services.recommendation.market_engine import (
    classify_market_stage as legacy_classify_market_stage,
)
from app.services.recommendation.market_engine import (
    normalize_market_intelligence as legacy_normalize_market_intelligence,
)
from app.services.recommendation.market_engine import (
    normalize_trend_direction as legacy_normalize_trend_direction,
)


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "up",
        "rise",
        "상승",
        "down",
        "하락",
        "flat",
        "stable",
        "unknown",
        "unexpected",
        " UP ",
    ],
)
def test_trend_direction_parity(value):
    assert (
        new_normalize_trend_direction(value)
        == legacy_normalize_trend_direction(value)
    )


@pytest.mark.parametrize(
    ("score", "direction"),
    [
        (None, None),
        ("invalid", "flat"),
        (-20, "flat"),
        (0, "down"),
        (20, "up"),
        (44.99, "flat"),
        (45, "flat"),
        (50, "flat"),
        (74.99, "flat"),
        (75, "flat"),
        (100, "up"),
        (120, "down"),
    ],
)
def test_market_score_parity(score, direction):
    assert new_calculate_market_score(
        score,
        direction,
    ) == legacy_calculate_market_score(
        score,
        direction,
    )


@pytest.mark.parametrize(
    ("score", "direction"),
    [
        (0, "up"),
        (100, "up"),
        (0, "down"),
        (100, "down"),
        (44.99, "flat"),
        (45, "flat"),
        (74.99, "flat"),
        (75, "flat"),
        (None, "flat"),
        ("invalid", "flat"),
    ],
)
def test_market_stage_parity(score, direction):
    assert new_classify_market_stage(
        score,
        direction,
    ) == legacy_classify_market_stage(
        score,
        direction,
    )


@pytest.mark.parametrize(
    "stage",
    [
        "rising",
        "stable_high",
        "stable",
        "cooling",
        "low_interest",
        "invalid-stage",
    ],
)
def test_market_signal_parity(stage):
    assert (
        new_build_market_signal(stage)
        == legacy_build_market_signal(stage)
    )


@pytest.mark.parametrize(
    "stage",
    [
        "rising",
        "stable_high",
        "stable",
        "cooling",
        "low_interest",
        "invalid-stage",
    ],
)
def test_buy_timing_parity(stage):
    assert (
        new_build_buy_timing(stage)
        == legacy_build_buy_timing(stage)
    )


@pytest.mark.parametrize(
    ("interest", "direction"),
    [
        (None, None),
        ("invalid", "invalid"),
        (-1, "flat"),
        (0, "down"),
        (25.5, "up"),
        (42.25, "상승"),
        (50, "flat"),
        (75, "stable"),
        (100, "up"),
        (101, "down"),
    ],
)
def test_complete_market_intelligence_parity(
    interest,
    direction,
):
    assert new_build_market_intelligence(
        interest,
        direction,
    ) == legacy_build_market_intelligence(
        interest,
        direction,
    )


@pytest.mark.parametrize(
    "payload",
    [
        None,
        {},
        {"market_stage": "rising"},
        {"market_score": None},
        {"market_score": -1},
        {"market_score": 101},
        {"market_score": "invalid"},
        {"search_interest": -10},
        {"search_interest": 120},
        {"trend_direction": "상승"},
        {
            "market_score": "72.5",
            "trend_direction": "하락",
        },
        {
            "future_compatibility_field": "preserve-me",
        },
    ],
)
def test_compatibility_normalization_parity(payload):
    assert new_normalize_market_intelligence(
        payload
    ) == legacy_normalize_market_intelligence(
        payload
    )


def test_default_payload_parity():
    assert NEW_DEFAULTS == LEGACY_DEFAULTS
