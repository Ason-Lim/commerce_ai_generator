from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.preference.models import (
    PreferenceProfile,
)


def decide_adaptive_priority(
    user_pref: (
        PreferenceProfile
        | Mapping[str, Any]
        | None
    ),
    default_priority: str = "trust",
) -> str:
    if not user_pref:
        return default_priority

    if isinstance(
        user_pref,
        PreferenceProfile,
    ):
        scores = user_pref.affinity_scores()
    else:
        scores = {
            "price": float(
                user_pref.get(
                    "price_affinity"
                )
                or 0
            ),
            "quality": float(
                user_pref.get(
                    "quality_affinity"
                )
                or 0
            ),
            "trust": float(
                user_pref.get(
                    "trust_affinity"
                )
                or 0
            ),
            "exploration": float(
                user_pref.get(
                    "exploration_affinity"
                )
                or 0
            ),
        }

    sorted_scores = sorted(
        scores.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    top_mode, top_score = sorted_scores[0]
    _, second_score = sorted_scores[1]

    if top_score < 5:
        return default_priority

    if top_score - second_score < 5:
        return "balanced_adaptive"

    return f"{top_mode}_adaptive"
