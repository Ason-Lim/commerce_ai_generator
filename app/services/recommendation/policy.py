from __future__ import annotations

from dataclasses import dataclass

from .models import RecommendationPriority


@dataclass(frozen=True)
class RecommendationPolicy:
    """
    Canonical recommendation policy resolution result.

    This object separates canonical priority from compatibility metadata.
    """

    priority: RecommendationPriority
    adaptive: bool
    requested_priority: str


_PRIORITY_ALIASES = {
    "ranking": RecommendationPriority.MIX,
    "mix": RecommendationPriority.MIX,
    "balanced": RecommendationPriority.MIX,
    "value": RecommendationPriority.PRICE,
    "price": RecommendationPriority.PRICE,
    "quality": RecommendationPriority.QUALITY,
    "taste": RecommendationPriority.QUALITY,
    "trust": RecommendationPriority.TRUST,
    "exploration": RecommendationPriority.EXPLORATION,
    "discovery": RecommendationPriority.DISCOVERY,
    "revisit": RecommendationPriority.REVISIT,
}


def resolve_recommendation_policy(
    priority: str | None,
) -> RecommendationPolicy:
    """
    Resolve external / legacy priority vocabulary into canonical policy.

    Responsibilities:
    - detect the ``*_adaptive`` compatibility suffix;
    - resolve legacy aliases;
    - return canonical RecommendationPriority;
    - preserve the requested base priority for compatibility/audit use.

    Non-responsibilities:
    - user preference persistence;
    - adaptive priority decision;
    - scoring;
    - ranking;
    - parsing;
    - API/UI response construction.
    """

    raw = str(
        priority or "ranking"
    ).strip()

    adaptive = raw.endswith(
        "_adaptive"
    )

    base = (
        raw[:-9]
        if adaptive
        else raw
    )

    if not base:
        base = "ranking"

    canonical = _PRIORITY_ALIASES.get(
        base,
        RecommendationPriority.MIX,
    )

    return RecommendationPolicy(
        priority=canonical,
        adaptive=adaptive,
        requested_priority=base,
    )
