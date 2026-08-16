from __future__ import annotations

import pytest

from app.services.market_intelligence import (
    DEFAULT_MARKET_INTELLIGENCE,
    build_buy_timing,
    build_market_intelligence,
    build_market_signal,
    calculate_market_score,
    classify_market_stage,
    normalize_market_intelligence,
    normalize_trend_direction,
)


# ---------------------------------------------------------
# Canonical trend-direction contract
# ---------------------------------------------------------

@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, "flat"),
        ("", "flat"),
        ("flat", "flat"),
        ("stable", "flat"),
        ("steady", "flat"),
        ("neutral", "flat"),
        ("unknown", "flat"),
        ("보합", "flat"),
        ("유지", "flat"),
        ("unexpected-value", "flat"),
        ("up", "up"),
        ("rise", "up"),
        ("rising", "up"),
        ("increase", "up"),
        ("increasing", "up"),
        ("상승", "up"),
        (" UP ", "up"),
        ("down", "down"),
        ("fall", "down"),
        ("falling", "down"),
        ("decrease", "down"),
        ("decreasing", "down"),
        ("하락", "down"),
    ],
)
def test_canonical_trend_direction_contract(
    raw,
    expected,
):
    assert normalize_trend_direction(raw) == expected


# ---------------------------------------------------------
# Canonical scoring contract
# ---------------------------------------------------------

@pytest.mark.parametrize(
    ("interest", "direction", "expected"),
    [
        (50, "flat", 53.0),
        (50, "up", 60.0),
        (50, "down", 40.0),
        (0, "flat", 3.0),
        (0, "down", 0.0),
        (100, "flat", 100.0),
        (100, "up", 100.0),
        (-20, "flat", 3.0),
        (120, "flat", 100.0),
        (None, "flat", 53.0),
        ("invalid", "flat", 53.0),
        ("25.5", "up", 35.5),
    ],
)
def test_canonical_market_score_contract(
    interest,
    direction,
    expected,
):
    assert calculate_market_score(
        interest,
        direction,
    ) == expected


# ---------------------------------------------------------
# Canonical market-stage boundary contract
# ---------------------------------------------------------

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
def test_canonical_market_stage_contract(
    score,
    direction,
    expected,
):
    assert classify_market_stage(
        score,
        direction,
    ) == expected


# ---------------------------------------------------------
# Canonical user-facing policy contract
# ---------------------------------------------------------

EXPECTED_SIGNALS = {
    "rising": (
        "🔥 시장 관심 상승",
        "최근 검색 관심도가 올라가는 흐름이에요.",
    ),
    "stable_high": (
        "📈 꾸준한 인기",
        "검색 관심도가 높은 수준에서 안정적으로 유지되고 있어요.",
    ),
    "stable": (
        "📊 안정적인 관심",
        "검색 관심도가 안정적인 수준을 유지하고 있어요.",
    ),
    "cooling": (
        "📉 관심 둔화",
        "최근 검색 관심도가 다소 낮아지는 흐름이에요.",
    ),
    "low_interest": (
        "🌱 관심 탐색 단계",
        "아직 시장 관심도가 높지 않은 상품군이에요.",
    ),
}


EXPECTED_BUY_TIMING = {
    "rising": (
        "지금 비교해볼 시점",
        (
            "관심이 빠르게 늘고 있어 인기 상품은 "
            "재고나 가격이 변할 수 있어요."
        ),
    ),
    "stable_high": (
        "지금 구매하기 무난한 시점",
        (
            "수요가 안정적으로 유지되고 있어 "
            "조건이 좋은 상품을 중심으로 비교해보세요."
        ),
    ),
    "stable": (
        "천천히 비교해볼 시점",
        (
            "급격한 시장 변화는 크지 않아 "
            "가격과 품질을 충분히 비교해도 좋아요."
        ),
    ),
    "cooling": (
        "조금 더 비교해볼 시점",
        (
            "관심이 낮아지는 흐름이므로 "
            "가격 변화를 조금 더 살펴봐도 좋아요."
        ),
    ),
    "low_interest": (
        "조건을 꼼꼼히 확인할 시점",
        (
            "상품별 차이가 클 수 있으므로 "
            "후기와 판매 조건을 함께 확인해보세요."
        ),
    ),
}


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
def test_canonical_market_signal_contract(stage):
    assert build_market_signal(stage) == EXPECTED_SIGNALS[stage]


def test_canonical_market_signal_unknown_fallback():
    assert build_market_signal(
        "unknown-stage"
    ) == EXPECTED_SIGNALS["stable"]


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
def test_canonical_buy_timing_contract(stage):
    assert build_buy_timing(stage) == EXPECTED_BUY_TIMING[stage]


def test_canonical_buy_timing_unknown_fallback():
    assert build_buy_timing(
        "unknown-stage"
    ) == EXPECTED_BUY_TIMING["stable"]


# ---------------------------------------------------------
# Canonical complete-result golden contracts
# ---------------------------------------------------------

@pytest.mark.parametrize(
    ("interest", "direction", "expected"),
    [
        (
            50,
            "flat",
            {
                "market_score": 53.0,
                "market_stage": "stable",
                "market_signal": "📊 안정적인 관심",
                "market_message": (
                    "검색 관심도가 안정적인 수준을 유지하고 있어요."
                ),
                "buy_timing": "천천히 비교해볼 시점",
                "buy_timing_message": (
                    "급격한 시장 변화는 크지 않아 "
                    "가격과 품질을 충분히 비교해도 좋아요."
                ),
                "search_interest": 50.0,
                "trend_direction": "flat",
            },
        ),
        (
            60,
            "up",
            {
                "market_score": 70.0,
                "market_stage": "rising",
                "market_signal": "🔥 시장 관심 상승",
                "market_message": (
                    "최근 검색 관심도가 올라가는 흐름이에요."
                ),
                "buy_timing": "지금 비교해볼 시점",
                "buy_timing_message": (
                    "관심이 빠르게 늘고 있어 인기 상품은 "
                    "재고나 가격이 변할 수 있어요."
                ),
                "search_interest": 60.0,
                "trend_direction": "up",
            },
        ),
        (
            80,
            "flat",
            {
                "market_score": 83.0,
                "market_stage": "stable_high",
                "market_signal": "📈 꾸준한 인기",
                "market_message": (
                    "검색 관심도가 높은 수준에서 "
                    "안정적으로 유지되고 있어요."
                ),
                "buy_timing": "지금 구매하기 무난한 시점",
                "buy_timing_message": (
                    "수요가 안정적으로 유지되고 있어 "
                    "조건이 좋은 상품을 중심으로 비교해보세요."
                ),
                "search_interest": 80.0,
                "trend_direction": "flat",
            },
        ),
        (
            80,
            "down",
            {
                "market_score": 70.0,
                "market_stage": "cooling",
                "market_signal": "📉 관심 둔화",
                "market_message": (
                    "최근 검색 관심도가 다소 낮아지는 흐름이에요."
                ),
                "buy_timing": "조금 더 비교해볼 시점",
                "buy_timing_message": (
                    "관심이 낮아지는 흐름이므로 "
                    "가격 변화를 조금 더 살펴봐도 좋아요."
                ),
                "search_interest": 80.0,
                "trend_direction": "down",
            },
        ),
        (
            20,
            "flat",
            {
                "market_score": 23.0,
                "market_stage": "low_interest",
                "market_signal": "🌱 관심 탐색 단계",
                "market_message": (
                    "아직 시장 관심도가 높지 않은 상품군이에요."
                ),
                "buy_timing": "조건을 꼼꼼히 확인할 시점",
                "buy_timing_message": (
                    "상품별 차이가 클 수 있으므로 "
                    "후기와 판매 조건을 함께 확인해보세요."
                ),
                "search_interest": 20.0,
                "trend_direction": "flat",
            },
        ),
    ],
)
def test_canonical_complete_golden_contract(
    interest,
    direction,
    expected,
):
    assert build_market_intelligence(
        interest,
        direction,
    ) == expected


# ---------------------------------------------------------
# Canonical compatibility contract
# ---------------------------------------------------------

def test_canonical_default_payload_contract():
    assert DEFAULT_MARKET_INTELLIGENCE == {
        "market_score": 50.0,
        "market_stage": "stable",
        "market_signal": "📊 안정적인 관심",
        "market_message": (
            "검색 관심도가 안정적인 수준을 유지하고 있어요."
        ),
        "buy_timing": "천천히 비교해볼 시점",
        "buy_timing_message": (
            "급격한 시장 변화는 크지 않아 "
            "가격과 품질을 충분히 비교해도 좋아요."
        ),
        "search_interest": 50.0,
        "trend_direction": "flat",
    }


def test_canonical_normalize_none_contract():
    result = normalize_market_intelligence(None)

    assert result == DEFAULT_MARKET_INTELLIGENCE
    assert result is not DEFAULT_MARKET_INTELLIGENCE


def test_canonical_partial_payload_preserves_defaults():
    result = normalize_market_intelligence(
        {
            "market_stage": "rising",
        }
    )

    assert result["market_stage"] == "rising"
    assert result["market_score"] == 50.0
    assert result["search_interest"] == 50.0
    assert result["trend_direction"] == "flat"


def test_canonical_none_fields_do_not_override_defaults():
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
def test_canonical_normalized_market_score_bounds(
    value,
    expected,
):
    result = normalize_market_intelligence(
        {
            "market_score": value,
        }
    )

    assert result["market_score"] == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (-1, 0.0),
        (101, 100.0),
        ("invalid", 50.0),
        ("72.25", 72.25),
    ],
)
def test_canonical_normalized_search_interest_bounds(
    value,
    expected,
):
    result = normalize_market_intelligence(
        {
            "search_interest": value,
        }
    )

    assert result["search_interest"] == expected


def test_canonical_unknown_extra_fields_are_preserved():
    result = normalize_market_intelligence(
        {
            "future_compatibility_field": "preserve-me",
        }
    )

    assert result["future_compatibility_field"] == "preserve-me"


def test_canonical_normalization_does_not_mutate_input():
    source = {
        "market_score": "72.5",
        "trend_direction": "상승",
    }
    snapshot = dict(source)

    normalize_market_intelligence(source)

    assert source == snapshot


# ---------------------------------------------------------
# Canonical determinism contract
# ---------------------------------------------------------

@pytest.mark.parametrize(
    ("interest", "direction"),
    [
        (0, "flat"),
        (20, "down"),
        (50, "flat"),
        (63.5, "up"),
        (75, "stable"),
        (100, "up"),
        (None, None),
        ("invalid", "invalid"),
    ],
)
def test_canonical_market_intelligence_is_deterministic(
    interest,
    direction,
):
    first = build_market_intelligence(
        interest,
        direction,
    )
    second = build_market_intelligence(
        interest,
        direction,
    )

    assert first == second
