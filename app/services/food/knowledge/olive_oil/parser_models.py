from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.food.knowledge.common.parser_models import (
    BaseParseResult,
)
from app.services.food.knowledge.olive_oil.grade_registry import (
    OliveOilGradeMatch,
)
from app.services.food.knowledge.olive_oil.origin_registry import (
    OliveOilOriginMatch,
)
from app.services.food.knowledge.olive_oil.processing_registry import (
    OliveOilProcessingMatch,
)
from app.services.food.knowledge.olive_oil.type_registry import (
    OliveOilTypeMatch,
)
from app.services.food.knowledge.olive_oil.variety_registry import (
    OliveOilVarietyMatch,
)


@dataclass(
    frozen=True,
    kw_only=True,
)
class OliveOilParseResult(BaseParseResult):
    """Olive Oil Parser result contract."""

    olive_oil_type: str | None = None
    variety: str | None = None
    origin: str | None = None
    processing: str | None = None
    grade: str | None = None

    olive_oil_type_confidence: float = 0.0
    variety_confidence: float = 0.0
    origin_confidence: float = 0.0
    processing_confidence: float = 0.0
    grade_confidence: float = 0.0

    olive_oil_type_match: OliveOilTypeMatch | None = None
    variety_match: OliveOilVarietyMatch | None = None
    origin_match: OliveOilOriginMatch | None = None
    processing_match: OliveOilProcessingMatch | None = None
    grade_match: OliveOilGradeMatch | None = None

    detected_keywords: list[str] = field(
        default_factory=list
    )
    warnings: list[str] = field(
        default_factory=list
    )

    def __post_init__(self) -> None:
        super().__post_init__()

        for field_name in (
            "olive_oil_type_confidence",
            "variety_confidence",
            "origin_confidence",
            "processing_confidence",
            "grade_confidence",
        ):
            normalized_value = max(
                0.0,
                min(
                    1.0,
                    float(getattr(self, field_name)),
                ),
            )

            object.__setattr__(
                self,
                field_name,
                normalized_value,
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
    def has_olive_oil_type(self) -> bool:
        return self.olive_oil_type is not None

    @property
    def has_variety(self) -> bool:
        return self.variety is not None

    @property
    def has_origin(self) -> bool:
        return self.origin is not None

    @property
    def has_processing(self) -> bool:
        return self.processing is not None

    @property
    def has_grade(self) -> bool:
        return self.grade is not None

    @property
    def matched_field_count(self) -> int:
        return sum(
            (
                self.has_olive_oil_type,
                self.has_variety,
                self.has_origin,
                self.has_processing,
                self.has_grade,
            )
        )

    @property
    def is_complete(self) -> bool:
        return self.matched_field_count == 5

    @property
    def is_usable(self) -> bool:
        return (
            self.has_grade
            or self.has_olive_oil_type
            or self.matched_field_count >= 2
        )

    @property
    def has_match(self) -> bool:
        return self.matched_field_count > 0

    def to_dict(self) -> dict[str, Any]:
        payload = super().to_dict()

        payload.update(
            {
                "olive_oil_type": self.olive_oil_type,
                "variety": self.variety,
                "origin": self.origin,
                "processing": self.processing,
                "grade": self.grade,
                "olive_oil_type_confidence": (
                    self.olive_oil_type_confidence
                ),
                "variety_confidence": (
                    self.variety_confidence
                ),
                "origin_confidence": (
                    self.origin_confidence
                ),
                "processing_confidence": (
                    self.processing_confidence
                ),
                "grade_confidence": (
                    self.grade_confidence
                ),
                "olive_oil_type_match": (
                    self._serialize_value(
                        self.olive_oil_type_match
                    )
                ),
                "variety_match": self._serialize_value(
                    self.variety_match
                ),
                "origin_match": self._serialize_value(
                    self.origin_match
                ),
                "processing_match": (
                    self._serialize_value(
                        self.processing_match
                    )
                ),
                "grade_match": self._serialize_value(
                    self.grade_match
                ),
                "detected_keywords": list(
                    self.detected_keywords
                ),
                "warnings": list(self.warnings),
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
            text = str(value).strip()

            if not text or text in seen:
                continue

            seen.add(text)
            result.append(text)

        return result


__all__ = [
    "OliveOilParseResult",
]
