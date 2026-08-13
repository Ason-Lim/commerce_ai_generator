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
class FruitParseResult(BaseParseResult):
    """
    Fruit Parser의 표준 결과 모델.

    Parser가 탐지·정규화한 Fruit 도메인 값만 보존한다.
    점수 계산이나 추천 판단은 수행하지 않는다.
    """

    origin: str | None = None
    variety: str | None = None
    grade: str | None = None
    brix: float | None = None
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
                self.origin,
                self.variety,
                self.grade,
                self.brix,
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
        """
        Fruit 분석의 핵심 식별 정보가 충분한지 표시한다.

        완전성은 품질 점수가 아니며,
        Parser 결과의 정보 충족 여부만 나타낸다.
        """
        return (
            self.variety is not None
            and self.origin is not None
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
                "origin": self.origin,
                "variety": self.variety,
                "grade": self.grade,
                "brix": self.brix,
                "weight_grams": (
                    self.weight_grams
                ),
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
    "FruitParseResult",
]
