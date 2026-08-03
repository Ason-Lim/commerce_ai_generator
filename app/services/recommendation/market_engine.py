"""
Market Intelligence Engine

네이버 DataLab 검색 관심도를 바탕으로
시장 점수, 시장 단계, 시장 메시지, 구매 시점을 생성합니다.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple


DEFAULT_MARKET_INTELLIGENCE: Dict[str, Any] = {
    "market_score": 50.0,
    "market_stage": "stable",
    "market_signal": "📊 안정적인 관심",
    "market_message": "검색 관심도가 안정적인 수준을 유지하고 있어요.",
    "buy_timing": "천천히 비교해볼 시점",
    "buy_timing_message": (
        "급격한 시장 변화는 크지 않아 "
        "가격과 품질을 충분히 비교해도 좋아요."
    ),
    "search_interest": 50.0,
    "trend_direction": "flat",
}


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """
    값을 안전하게 float로 변환합니다.
    """
    try:
        if value is None:
            return float(default)

        return float(value)

    except (TypeError, ValueError):
        return float(default)


def normalize_trend_direction(
    trend_direction: Optional[str],
) -> str:
    """
    트렌드 방향 문자열을 up/down/flat으로 표준화합니다.
    알 수 없는 값은 flat으로 처리합니다.
    """
    normalized = str(
        trend_direction or "flat"
    ).strip().lower()

    direction_aliases = {
        "up": "up",
        "rise": "up",
        "rising": "up",
        "increase": "up",
        "increasing": "up",
        "상승": "up",

        "down": "down",
        "fall": "down",
        "falling": "down",
        "decrease": "down",
        "decreasing": "down",
        "하락": "down",

        "flat": "flat",
        "stable": "flat",
        "steady": "flat",
        "neutral": "flat",
        "unknown": "flat",
        "보합": "flat",
        "유지": "flat",
    }

    return direction_aliases.get(
        normalized,
        "flat",
    )


def calculate_market_score(
    trend_score: Any,
    trend_direction: Optional[str] = "flat",
) -> float:
    """
    DataLab 상대 관심도와 트렌드 방향을 결합해
    시장 점수 0~100을 생성합니다.
    """
    search_interest = max(
        0.0,
        min(
            _safe_float(
                trend_score,
                50.0,
            ),
            100.0,
        ),
    )

    direction = normalize_trend_direction(
        trend_direction
    )

    direction_adjustment = {
        "up": 10.0,
        "flat": 3.0,
        "down": -10.0,
    }.get(
        direction,
        0.0,
    )

    market_score = (
        search_interest
        + direction_adjustment
    )

    return round(
        max(
            0.0,
            min(
                market_score,
                100.0,
            ),
        ),
        2,
    )


def classify_market_stage(
    market_score: Any,
    trend_direction: Optional[str] = "flat",
) -> str:
    """
    시장 상태를 다음 단계로 분류합니다.

    rising
    stable_high
    stable
    cooling
    low_interest
    """
    score = _safe_float(
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
) -> Tuple[str, str]:
    """
    시장 단계에 맞는 사용자용 시장 신호와 설명을 반환합니다.
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
) -> Tuple[str, str]:
    """
    시장 상태를 바탕으로 구매 시점 안내를 생성합니다.
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


def build_market_intelligence(
    search_interest: Any,
    trend_direction: Optional[str] = "flat",
) -> Dict[str, Any]:
    """
    검색 관심도와 트렌드 방향을 바탕으로
    완성된 시장 분석 결과를 반환합니다.

    이 함수가 Market Intelligence Engine의 대표 진입점입니다.
    """
    normalized_interest = max(
        0.0,
        min(
            _safe_float(
                search_interest,
                50.0,
            ),
            100.0,
        ),
    )

    normalized_direction = normalize_trend_direction(
        trend_direction
    )

    market_score = calculate_market_score(
        trend_score=normalized_interest,
        trend_direction=normalized_direction,
    )

    market_stage = classify_market_stage(
        market_score=market_score,
        trend_direction=normalized_direction,
    )

    market_signal, market_message = build_market_signal(
        market_stage
    )

    buy_timing, buy_timing_message = build_buy_timing(
        market_stage
    )

    return {
        "market_score": market_score,
        "market_stage": market_stage,
        "market_signal": market_signal,
        "market_message": market_message,
        "buy_timing": buy_timing,
        "buy_timing_message": buy_timing_message,
        "search_interest": round(
            normalized_interest,
            2,
        ),
        "trend_direction": normalized_direction,
    }


def normalize_market_intelligence(
    value: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    시장 분석 결과에 일부 필드가 없더라도
    UI가 안전하게 사용할 수 있도록 기본값을 보강합니다.
    """
    normalized = dict(
        DEFAULT_MARKET_INTELLIGENCE
    )

    if isinstance(value, dict):
        normalized.update(
            {
                key: field_value
                for key, field_value in value.items()
                if field_value is not None
            }
        )

    normalized["market_score"] = round(
        max(
            0.0,
            min(
                _safe_float(
                    normalized.get(
                        "market_score"
                    ),
                    50.0,
                ),
                100.0,
            ),
        ),
        2,
    )

    normalized["search_interest"] = round(
        max(
            0.0,
            min(
                _safe_float(
                    normalized.get(
                        "search_interest"
                    ),
                    50.0,
                ),
                100.0,
            ),
        ),
        2,
    )

    normalized["trend_direction"] = (
        normalize_trend_direction(
            normalized.get(
                "trend_direction"
            )
        )
    )

    return normalized