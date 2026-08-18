from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


SEARCH_NOISE_TERMS = (
    "추천해줘",
    "추천",
)

PRIORITY_SIGNALS = MappingProxyType(
    {
        "price": (
            "가성비 좋은",
            "가격 좋은",
        ),
        "quality": (
            "고당도 품질 좋은",
            "품질 좋은",
        ),
        "trust": (
            "신뢰도 높은",
        ),
    }
)

GIFT_TARGET_SIGNALS = MappingProxyType(
    {
        "parents": (
            "부모님",
        ),
    }
)

OCCASION_SIGNALS = MappingProxyType(
    {
        "holiday": (
            "명절",
        ),
        "parents_day": (
            "어버이날",
        ),
    }
)

GIFT_SIGNALS = (
    "선물용",
    "선물",
)


@dataclass(frozen=True)
class RecommendationQuery:
    raw_query: str
    search_query: str
    priority_hint: str | None = None
    gift_target: str | None = None
    occasion: str | None = None
    gift_intent: bool = False


def _remove_terms(
    value: str,
    terms: tuple[str, ...],
) -> str:
    result = value

    for term in terms:
        result = result.replace(
            term,
            "",
        )

    return result


def _normalize_spaces(
    value: str,
) -> str:
    return " ".join(
        value.split()
    )


def _detect_mapping_signal(
    value: str,
    signals: Mapping[str, tuple[str, ...]],
) -> str | None:
    for name, terms in signals.items():
        if any(
            term in value
            for term in terms
        ):
            return name

    return None


def parse_recommendation_query(
    query: str | None,
) -> RecommendationQuery:
    raw_query = query or ""

    priority_hint = _detect_mapping_signal(
        raw_query,
        PRIORITY_SIGNALS,
    )

    gift_target = _detect_mapping_signal(
        raw_query,
        GIFT_TARGET_SIGNALS,
    )

    occasion = _detect_mapping_signal(
        raw_query,
        OCCASION_SIGNALS,
    )

    gift_intent = any(
        term in raw_query
        for term in GIFT_SIGNALS
    )

    search_query = raw_query

    for terms in PRIORITY_SIGNALS.values():
        search_query = _remove_terms(
            search_query,
            terms,
        )

    for terms in GIFT_TARGET_SIGNALS.values():
        search_query = _remove_terms(
            search_query,
            terms,
        )

    for terms in OCCASION_SIGNALS.values():
        search_query = _remove_terms(
            search_query,
            terms,
        )

    search_query = _remove_terms(
        search_query,
        GIFT_SIGNALS,
    )

    search_query = _remove_terms(
        search_query,
        SEARCH_NOISE_TERMS,
    )

    search_query = _normalize_spaces(
        search_query
    )

    return RecommendationQuery(
        raw_query=raw_query,
        search_query=search_query,
        priority_hint=priority_hint,
        gift_target=gift_target,
        occasion=occasion,
        gift_intent=gift_intent,
    )
