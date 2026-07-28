from __future__ import annotations

from dataclasses import dataclass, field

from app.services.food.knowledge.common.base_model import (
    RegistryMatch,
)
from app.services.food.knowledge.common.parser_models import (
    BaseParseResult,
)


@dataclass(frozen=True)
class LambParseResult(BaseParseResult):
    """
    Lamb Parser 결과.

    Registry에서 탐지한 연령 분류, 품종, 부위 정보를
    원본 RegistryMatch와 함께 보존한다.
    """

    # -------------------------
    # Parsed Values
    # -------------------------

    age: str | None = None
    breed: str | None = None
    cut: str | None = None

    # -------------------------
    # Confidence
    # -------------------------

    age_confidence: float = 0.0
    breed_confidence: float = 0.0
    cut_confidence: float = 0.0

    # -------------------------
    # Registry Match
    # -------------------------

    age_match: RegistryMatch | None = None
    breed_match: RegistryMatch | None = None
    cut_match: RegistryMatch | None = None

    # -------------------------
    # Parsing Metadata
    # -------------------------

    detected_keywords: list[str] = field(
        default_factory=list
    )

    warnings: list[str] = field(
        default_factory=list
    )

    # -------------------------
    # Convenience Properties
    # -------------------------

    @property
    def has_age(self) -> bool:
        return self.age is not None

    @property
    def has_breed(self) -> bool:
        return self.breed is not None

    @property
    def has_cut(self) -> bool:
        return self.cut is not None

    @property
    def is_complete(self) -> bool:
        """
        연령 분류, 품종, 부위를 모두 인식했는지 여부.
        """
        return (
            self.has_age
            and self.has_breed
            and self.has_cut
        )


__all__ = [
    "LambParseResult",
]
