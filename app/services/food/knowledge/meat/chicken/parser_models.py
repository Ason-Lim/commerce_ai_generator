from __future__ import annotations

from dataclasses import dataclass, field

from app.services.food.knowledge.common.base_model import (
    RegistryMatch,
)
from app.services.food.knowledge.common.parser_models import (
    BaseParseResult,
)


@dataclass(frozen=True)
class ChickenParseResult(BaseParseResult):
    """
    Chicken Parser 결과.

    Registry에서 탐지한 닭고기 상품 유형, 품종·계통,
    부위 정보를 원본 RegistryMatch와 함께 보존한다.
    """

    chicken_type: str | None = None
    breed: str | None = None
    cut: str | None = None

    chicken_type_confidence: float = 0.0
    breed_confidence: float = 0.0
    cut_confidence: float = 0.0

    chicken_type_match: RegistryMatch | None = None
    breed_match: RegistryMatch | None = None
    cut_match: RegistryMatch | None = None

    detected_keywords: list[str] = field(
        default_factory=list
    )
    warnings: list[str] = field(
        default_factory=list
    )

    @property
    def has_chicken_type(self) -> bool:
        return self.chicken_type is not None

    @property
    def has_breed(self) -> bool:
        return self.breed is not None

    @property
    def has_cut(self) -> bool:
        return self.cut is not None

    @property
    def is_complete(self) -> bool:
        return (
            self.has_chicken_type
            and self.has_breed
            and self.has_cut
        )

    @property
    def is_usable(self) -> bool:
        """
        유형 또는 부위 중 하나 이상을 인식했는지 여부.

        닭 품종·상업 계통은 상품명에 자주 표시되지 않으므로
        품종 누락만으로 결과를 unusable로 판단하지 않는다.
        """
        return (
            self.has_chicken_type
            or self.has_cut
        )


__all__ = [
    "ChickenParseResult",
]
