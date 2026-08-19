from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class PreferenceProfile:
    session_id: str
    price_affinity: float = 0.0
    quality_affinity: float = 0.0
    trust_affinity: float = 0.0
    exploration_affinity: float = 0.0
    search_count: int = 0
    click_count: int = 0
    last_query: str | None = None
    last_priority: str | None = None

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, Any],
    ) -> "PreferenceProfile":
        return cls(
            session_id=str(
                value.get("session_id") or ""
            ),
            price_affinity=float(
                value.get("price_affinity") or 0
            ),
            quality_affinity=float(
                value.get("quality_affinity") or 0
            ),
            trust_affinity=float(
                value.get("trust_affinity") or 0
            ),
            exploration_affinity=float(
                value.get("exploration_affinity")
                or 0
            ),
            search_count=int(
                value.get("search_count") or 0
            ),
            click_count=int(
                value.get("click_count") or 0
            ),
            last_query=value.get("last_query"),
            last_priority=value.get(
                "last_priority"
            ),
        )

    def affinity_scores(
        self,
    ) -> dict[str, float]:
        return {
            "price": self.price_affinity,
            "quality": self.quality_affinity,
            "trust": self.trust_affinity,
            "exploration": (
                self.exploration_affinity
            ),
        }
