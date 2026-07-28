from __future__ import annotations

from dataclasses import dataclass, field

from app.services.food.knowledge.common.base_model import (
    RegistryMatch,
)
from app.services.food.knowledge.common.parser_models import (
    BaseParseResult,
)


@dataclass(frozen=True)
class BeefParseResult(BaseParseResult):
    """
    Beef Parser 결과.

    Registry에서 추출한 정보를 그대로 보존한다.
    """

    # -------------------------
    # Parsed Values
    # -------------------------

    breed: str | None = None
    grade: str | None = None
    cut: str | None = None

    # -------------------------
    # Confidence
    # -------------------------

    breed_confidence: float = 0.0
    grade_confidence: float = 0.0
    cut_confidence: float = 0.0

    # -------------------------
    # Registry Match
    # -------------------------

    breed_match: RegistryMatch | None = None
    grade_match: RegistryMatch | None = None
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
    def has_breed(self) -> bool:
        return self.breed is not None

    @property
    def has_grade(self) -> bool:
        return self.grade is not None

    @property
    def has_cut(self) -> bool:
        return self.cut is not None

    @property
    def is_complete(self) -> bool:
        """
        품종/등급/부위를 모두 인식했는지 여부.
        """
        return (
            self.has_breed
            and self.has_grade
            and self.has_cut
        )