from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.services.recommendation.market_engine import (
    build_market_intelligence,
    normalize_market_intelligence,
)


@dataclass
class SearchContext:
    """
    검색 1회에 대한 공통 컨텍스트.

    모든 추천 엔진과 UI가 동일한 검색·시장 정보를 공유합니다.
    """

    query: str

    # 네이버 DataLab
    trend_score: float = 0.0
    trend_direction: str = "flat"
    trend_boost: float = 0.0

    # 기존 UI 하위 호환 필드
    market_signal: str = ""
    market_message: str = ""

    # 통합 시장 분석 결과
    market_intelligence: Dict[str, Any] = field(
        default_factory=dict
    )

    related_keywords: List[str] = field(
        default_factory=list
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


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


def normalize_trend_boost(
    trend_score: float,
) -> float:
    """
    DataLab 관심도 0~100을 추천 가산점 0~5점으로 변환합니다.
    """
    normalized_score = max(
        0.0,
        min(
            _safe_float(
                trend_score,
                0.0,
            ),
            100.0,
        ),
    )

    return round(
        min(
            normalized_score / 20.0,
            5.0,
        ),
        2,
    )


def build_search_context(
    query: str,
    trend_data: Optional[Dict[str, Any]] = None,
) -> SearchContext:
    """
    검색어와 DataLab 결과를 기반으로 SearchContext를 생성합니다.

    시장 정보는 이 시점에서 한 번만 계산하고,
    이후 추천 엔진과 UI가 동일한 결과를 재사용합니다.
    """
    trend_data = trend_data or {}

    trend_score = _safe_float(
        trend_data.get(
            "latest_ratio"
        ),
        0.0,
    )

    trend_direction = (
        trend_data.get(
            "trend_direction"
        )
        or "flat"
    )

    market_intelligence = (
        build_market_intelligence(
            search_interest=trend_score,
            trend_direction=trend_direction,
        )
    )

    market_intelligence = (
        normalize_market_intelligence(
            market_intelligence
        )
    )

    return SearchContext(
        query=query,
        trend_score=trend_score,
        trend_direction=market_intelligence.get(
            "trend_direction",
            "flat",
        ),
        trend_boost=normalize_trend_boost(
            trend_score
        ),

        # 기존 hero_renderer_v3.py 하위 호환
        market_signal=market_intelligence.get(
            "market_signal",
            "",
        ),
        market_message=market_intelligence.get(
            "market_message",
            "",
        ),

        # 신규 통합 시장 분석 결과
        market_intelligence=market_intelligence,

        related_keywords=list(
            trend_data.get(
                "related_keywords"
            )
            or []
        ),

        metadata={
            "trend_from_cache": trend_data.get(
                "from_cache",
                False,
            ),
            "trend_avg_ratio": _safe_float(
                trend_data.get(
                    "avg_ratio"
                ),
                0.0,
            ),
            "market_score": market_intelligence.get(
                "market_score",
                50.0,
            ),
            "market_stage": market_intelligence.get(
                "market_stage",
                "stable",
            ),
        },
    )