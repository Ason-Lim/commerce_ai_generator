from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

from .models import (
    RecommendationPriority,
    RecommendationScoreComponents,
    RecommendationScoreResult,
)


QUALITY_WEIGHTS = MappingProxyType(
    {
        "quality": 0.55,
        "price": 0.15,
        "trust": 0.15,
        "popularity": 0.05,
        "market": 0.05,
        "identity": 0.05,
    }
)

PRICE_WEIGHTS = MappingProxyType(
    {
        "quality": 0.10,
        "price": 0.55,
        "trust": 0.10,
        "popularity": 0.05,
        "market": 0.05,
        "identity": 0.15,
    }
)

TRUST_WEIGHTS = MappingProxyType(
    {
        "quality": 0.15,
        "price": 0.10,
        "trust": 0.40,
        "popularity": 0.10,
        "market": 0.05,
        "identity": 0.20,
    }
)

MIX_WEIGHTS = MappingProxyType(
    {
        "quality": 0.30,
        "price": 0.25,
        "trust": 0.15,
        "popularity": 0.10,
        "market": 0.10,
        "identity": 0.10,
    }
)


def clamp_score(
    value: float,
) -> float:
    return round(
        max(
            0.0,
            min(
                100.0,
                float(value),
            ),
        ),
        1,
    )


def get_priority_weights(
    priority: RecommendationPriority,
) -> Mapping[str, float]:
    if priority is RecommendationPriority.QUALITY:
        return QUALITY_WEIGHTS

    if priority is RecommendationPriority.PRICE:
        return PRICE_WEIGHTS

    if priority is RecommendationPriority.TRUST:
        return TRUST_WEIGHTS

    return MIX_WEIGHTS


def normalize_components(
    components: RecommendationScoreComponents,
) -> RecommendationScoreComponents:
    return RecommendationScoreComponents(
        quality=clamp_score(
            components.quality
        ),
        price=clamp_score(
            components.price
        ),
        trust=clamp_score(
            components.trust
        ),
        popularity=clamp_score(
            components.popularity
        ),
        market=clamp_score(
            components.market
        ),
        identity=clamp_score(
            components.identity
        ),
        available=components.available,
    )


def build_effective_weights(
    components: RecommendationScoreComponents,
    configured_weights: Mapping[str, float],
) -> Mapping[str, float]:
    """
    Renormalize configured weights over available evidence only.

    Missing evidence contributes neither a score nor a weight.
    """

    available_weights = {
        name: float(weight)
        for name, weight
        in configured_weights.items()
        if components.is_available(
            name
        )
    }

    denominator = sum(
        available_weights.values()
    )

    if denominator <= 0:
        return MappingProxyType(
            {}
        )

    return MappingProxyType(
        {
            name: (
                weight
                / denominator
            )
            for name, weight
            in available_weights.items()
        }
    )


def build_reason_codes(
    components: RecommendationScoreComponents,
) -> tuple[str, ...]:
    reason_codes: list[str] = []

    if (
        components.is_available(
            "quality"
        )
        and components.quality >= 80
    ):
        reason_codes.append(
            "high_quality"
        )

    if (
        components.is_available(
            "price"
        )
        and components.price >= 75
    ):
        reason_codes.append(
            "good_price"
        )

    if (
        components.is_available(
            "trust"
        )
        and components.trust >= 70
    ):
        reason_codes.append(
            "high_trust"
        )

    if (
        components.is_available(
            "identity"
        )
        and components.identity < 45
    ):
        reason_codes.append(
            "identity_warning"
        )

    if (
        components.is_available(
            "market"
        )
        and components.market >= 70
    ):
        reason_codes.append(
            "market_interest"
        )

    return tuple(
        reason_codes
    )


def calculate_recommendation_score(
    components: RecommendationScoreComponents,
    priority: RecommendationPriority = RecommendationPriority.MIX,
    *,
    version: str = "canonical-v8",
) -> RecommendationScoreResult:
    normalized = normalize_components(
        components
    )

    configured_weights = (
        get_priority_weights(
            priority
        )
    )

    effective_weights = (
        build_effective_weights(
            normalized,
            configured_weights,
        )
    )

    values = normalized.as_mapping()

    if effective_weights:
        raw_score = sum(
            values[name] * weight
            for name, weight
            in effective_weights.items()
        )

        final_score = clamp_score(
            raw_score
        )

    else:
        final_score = 0.0

    reason_codes = build_reason_codes(
        normalized
    )

    warnings: list[str] = []

    if not effective_weights:
        warnings.append(
            "insufficient_evidence"
        )

    if (
        normalized.is_available(
            "identity"
        )
        and normalized.identity < 45
    ):
        warnings.append(
            "identity_warning"
        )

    return RecommendationScoreResult(
        final_score=final_score,
        priority=priority,
        components=normalized,
        weights=effective_weights,
        reason_codes=reason_codes,
        warnings=tuple(
            warnings
        ),
        version=version,
    )
