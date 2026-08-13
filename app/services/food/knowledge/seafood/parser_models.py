from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.food.knowledge.common.parser_models import (
    BaseParseResult,
)


@dataclass(
    frozen=True,
    kw_only=True,
)
class SeafoodParseResult(BaseParseResult):
    """
    Seafood Parser의 표준 결과 모델.

    Parser가 탐지·정규화한 Seafood 도메인 정보만 보존한다.
    점수 계산과 Provider orchestration은 수행하지 않는다.
    """

    seafood_group: str | None = None
    species: str | None = None
    origin: str | None = None
    grade: str | None = None
    wild_farmed_status: str | None = None
    processing_state: str | None = None
    weight_grams: float | None = None

    detected_keywords: list[str] = field(
        default_factory=list
    )
    warnings: list[str] = field(
        default_factory=list
    )

    @property
    def matched_field_count(self) -> int:
        return sum(
            value is not None
            for value in (
                self.seafood_group,
                self.species,
                self.origin,
                self.grade,
                self.wild_farmed_status,
                self.processing_state,
                self.weight_grams,
            )
        )

    @property
    def has_match(self) -> bool:
        return (
            self.matched_field_count > 0
            or bool(self.detected_keywords)
        )

    @property
    def is_complete(self) -> bool:
        return (
            self.species is not None
            and self.seafood_group is not None
        )

    @property
    def is_usable(self) -> bool:
        return (
            self.has_match
            or self.confidence >= 0.5
        )

    def to_dict(self) -> dict[str, Any]:
        payload = super().to_dict()

        payload.update(
            {
                "seafood_group": self.seafood_group,
                "species": self.species,
                "origin": self.origin,
                "grade": self.grade,
                "wild_farmed_status": (
                    self.wild_farmed_status
                ),
                "processing_state": (
                    self.processing_state
                ),
                "weight_grams": self.weight_grams,
                "detected_keywords": list(
                    self.detected_keywords
                ),
                "warnings": list(
                    self.warnings
                ),
                "matched_field_count": (
                    self.matched_field_count
                ),
                "is_complete": self.is_complete,
                "is_usable": self.is_usable,
            }
        )

        return payload


__all__ = [
    "SeafoodParseResult",
]
