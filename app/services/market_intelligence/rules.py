from __future__ import annotations

from typing import Any

from .parser import (
    normalize_trend_direction,
    safe_float,
)


def classify_market_stage(
    market_score: Any,
    trend_direction: str | None = "flat",
) -> str:
    """
    Classify the market using the legacy stage rules.
    """
    score = safe_float(
        market_score,
        50.0,
    )

    direction = normalize_trend_direction(
        trend_direction
    )

    if direction == "up":
        return "rising"

    if direction == "down":
        return "cooling"

    if score >= 75:
        return "stable_high"

    if score >= 45:
        return "stable"

    return "low_interest"


def build_market_signal(
    market_stage: str,
) -> tuple[str, str]:
    """
    Return the legacy market signal and message.
    """
    signals = {
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

    return signals.get(
        market_stage,
        signals["stable"],
    )


def build_buy_timing(
    market_stage: str,
) -> tuple[str, str]:
    """
    Return the legacy buy-timing guidance.
    """
    timing = {
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

    return timing.get(
        market_stage,
        timing["stable"],
    )
