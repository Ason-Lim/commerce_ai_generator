from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.food.knowledge.cheese.aging_registry import (
    CheeseAgingMatch,
)
from app.services.food.knowledge.cheese.milk_source_registry import (
    CheeseMilkSourceMatch,
)
from app.services.food.knowledge.cheese.origin_registry import (
    CheeseOriginMatch,
)
from app.services.food.knowledge.cheese.texture_registry import (
    CheeseTextureMatch,
)
from app.services.food.knowledge.cheese.type_registry import (
    CheeseTypeMatch,
)
from app.services.food.knowledge.common.parser_models import (
    BaseParseResult,
)


@dataclass(
    frozen=True,
    kw_only=True,
)
class CheeseParseResult(BaseParseResult):
    """
    Cheese Parser 결과.

    각 Registry에서 탐지된 표준값과 RegistryMatch를 함께 보존한다.
    """

    # Parsed values
    cheese_type: str | None = None
    milk_source: str | None = None
    origin: str | None = None
    texture: str | None = None
    aging: str | None = None

    # Field confidence
    cheese_type_confidence: float = 0.0
    milk_source_confidence: float = 0.0
    origin_confidence: float = 0.0
    texture_confidence: float = 0.0
    aging_confidence: float = 0.0

    # Registry matches
    cheese_type_match: CheeseTypeMatch | None = None
    milk_source_match: CheeseMilkSourceMatch | None = None
    origin_match: CheeseOriginMatch | None = None
    texture_match: CheeseTextureMatch | None = None
    aging_match: CheeseAgingMatch | None = None

    # Parsing evidence
    detected_keywords: list[str] = field(
        default_factory=list
    )
    warnings: list[str] = field(
        default_factory=list
    )

    def __post_init__(self) -> None:
        super().__post_init__()

        for field_name in (
            "cheese_type_confidence",
            "milk_source_confidence",
            "origin_confidence",
            "texture_confidence",
            "aging_confidence",
        ):
            value = max(
                0.0,
                min(
                    1.0,
                    float(
                        getattr(self, field_name)
                    ),
                ),
            )

            object.__setattr__(
                self,
                field_name,
                value,
            )

        object.__setattr__(
            self,
            "detected_keywords",
            self._deduplicate_strings(
                self.detected_keywords
            ),
        )

        object.__setattr__(
            self,
            "warnings",
            self._deduplicate_strings(
                self.warnings
            ),
        )

    @property
    def has_cheese_type(self) -> bool:
        return self.cheese_type is not None

    @property
    def has_milk_source(self) -> bool:
        return self.milk_source is not None

    @property
    def has_origin(self) -> bool:
        return self.origin is not None

    @property
    def has_texture(self) -> bool:
        return self.texture is not None

    @property
    def has_aging(self) -> bool:
        return self.aging is not None

    @property
    def matched_field_count(self) -> int:
        return sum(
            (
                self.has_cheese_type,
                self.has_milk_source,
                self.has_origin,
                self.has_texture,
                self.has_aging,
            )
        )

    @property
    def is_complete(self) -> bool:
        return self.matched_field_count == 5

    @property
    def is_usable(self) -> bool:
        """
        치즈 종류가 확인되거나,
        종류 이외의 독립 속성이 둘 이상 확인되면 사용 가능하다.

        원유 하나만 탐지된 일반 유제품 문자열은 Cheese 결과로
        확정하지 않는다.
        """
        return (
            self.has_cheese_type
            or self.matched_field_count >= 2
        )

    @property
    def has_match(self) -> bool:
        return self.matched_field_count > 0

    def to_dict(self) -> dict[str, Any]:
        payload = super().to_dict()

        payload.update(
            {
                "cheese_type": self.cheese_type,
                "milk_source": self.milk_source,
                "origin": self.origin,
                "texture": self.texture,
                "aging": self.aging,
                "cheese_type_confidence": (
                    self.cheese_type_confidence
                ),
                "milk_source_confidence": (
                    self.milk_source_confidence
                ),
                "origin_confidence": (
                    self.origin_confidence
                ),
                "texture_confidence": (
                    self.texture_confidence
                ),
                "aging_confidence": (
                    self.aging_confidence
                ),
                "cheese_type_match": (
                    self._serialize_value(
                        self.cheese_type_match
                    )
                ),
                "milk_source_match": (
                    self._serialize_value(
                        self.milk_source_match
                    )
                ),
                "origin_match": (
                    self._serialize_value(
                        self.origin_match
                    )
                ),
                "texture_match": (
                    self._serialize_value(
                        self.texture_match
                    )
                ),
                "aging_match": (
                    self._serialize_value(
                        self.aging_match
                    )
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

    @staticmethod
    def _deduplicate_strings(
        values: list[str],
    ) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()

        for value in values:
            normalized = str(value).strip()

            if (
                not normalized
                or normalized in seen
            ):
                continue

            seen.add(normalized)
            result.append(normalized)

        return result


__all__ = [
    "CheeseParseResult",
]
