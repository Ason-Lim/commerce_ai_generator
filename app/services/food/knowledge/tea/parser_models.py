from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.food.knowledge.common.parser_models import (
    BaseParseResult,
)
from app.services.food.knowledge.tea.flavor_registry import (
    TeaFlavorMatch,
)
from app.services.food.knowledge.tea.origin_registry import (
    TeaOriginMatch,
)
from app.services.food.knowledge.tea.oxidation_registry import (
    TeaOxidationMatch,
)
from app.services.food.knowledge.tea.processing_registry import (
    TeaProcessingMatch,
)
from app.services.food.knowledge.tea.type_registry import (
    TeaTypeMatch,
)
from app.services.food.knowledge.tea.variety_registry import (
    TeaVarietyMatch,
)


@dataclass(
    frozen=True,
    kw_only=True,
)
class TeaParseResult(BaseParseResult):
    """Tea Parser result contract."""

    tea_type: str | None = None
    origin: str | None = None
    variety: str | None = None
    processing: str | None = None
    oxidation: str | None = None
    flavor: str | None = None

    tea_type_confidence: float = 0.0
    origin_confidence: float = 0.0
    variety_confidence: float = 0.0
    processing_confidence: float = 0.0
    oxidation_confidence: float = 0.0
    flavor_confidence: float = 0.0

    tea_type_match: TeaTypeMatch | None = None
    origin_match: TeaOriginMatch | None = None
    variety_match: TeaVarietyMatch | None = None
    processing_match: TeaProcessingMatch | None = None
    oxidation_match: TeaOxidationMatch | None = None
    flavor_match: TeaFlavorMatch | None = None

    detected_keywords: list[str] = field(
        default_factory=list
    )
    warnings: list[str] = field(
        default_factory=list
    )

    def __post_init__(self) -> None:
        super().__post_init__()

        for field_name in (
            "tea_type_confidence",
            "origin_confidence",
            "variety_confidence",
            "processing_confidence",
            "oxidation_confidence",
            "flavor_confidence",
        ):
            value = max(
                0.0,
                min(
                    1.0,
                    float(getattr(self, field_name)),
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
    def has_tea_type(self) -> bool:
        return self.tea_type is not None

    @property
    def has_origin(self) -> bool:
        return self.origin is not None

    @property
    def has_variety(self) -> bool:
        return self.variety is not None

    @property
    def has_processing(self) -> bool:
        return self.processing is not None

    @property
    def has_oxidation(self) -> bool:
        return self.oxidation is not None

    @property
    def has_flavor(self) -> bool:
        return self.flavor is not None

    @property
    def matched_field_count(self) -> int:
        return sum(
            (
                self.has_tea_type,
                self.has_origin,
                self.has_variety,
                self.has_processing,
                self.has_oxidation,
                self.has_flavor,
            )
        )

    @property
    def is_complete(self) -> bool:
        return self.matched_field_count == 6

    @property
    def is_usable(self) -> bool:
        return (
            self.has_tea_type
            or self.matched_field_count >= 2
        )

    @property
    def has_match(self) -> bool:
        return self.matched_field_count > 0

    def to_dict(self) -> dict[str, Any]:
        payload = super().to_dict()

        payload.update(
            {
                "tea_type": self.tea_type,
                "origin": self.origin,
                "variety": self.variety,
                "processing": self.processing,
                "oxidation": self.oxidation,
                "flavor": self.flavor,
                "tea_type_confidence": self.tea_type_confidence,
                "origin_confidence": self.origin_confidence,
                "variety_confidence": self.variety_confidence,
                "processing_confidence": self.processing_confidence,
                "oxidation_confidence": self.oxidation_confidence,
                "flavor_confidence": self.flavor_confidence,
                "tea_type_match": self._serialize_value(
                    self.tea_type_match
                ),
                "origin_match": self._serialize_value(
                    self.origin_match
                ),
                "variety_match": self._serialize_value(
                    self.variety_match
                ),
                "processing_match": self._serialize_value(
                    self.processing_match
                ),
                "oxidation_match": self._serialize_value(
                    self.oxidation_match
                ),
                "flavor_match": self._serialize_value(
                    self.flavor_match
                ),
                "detected_keywords": list(
                    self.detected_keywords
                ),
                "warnings": list(self.warnings),
                "matched_field_count": self.matched_field_count,
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
            text = str(value).strip()

            if not text or text in seen:
                continue

            seen.add(text)
            result.append(text)

        return result


__all__ = [
    "TeaParseResult",
]
