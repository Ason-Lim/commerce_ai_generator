from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.food.knowledge.common.parser_models import (
    BaseParseResult,
)
from app.services.food.knowledge.wine.acidity_registry import (
    WineAcidityMatch,
)
from app.services.food.knowledge.wine.body_registry import (
    WineBodyMatch,
)
from app.services.food.knowledge.wine.grape_registry import (
    WineGrapeMatch,
)
from app.services.food.knowledge.wine.region_registry import (
    WineRegionMatch,
)
from app.services.food.knowledge.wine.sweetness_registry import (
    WineSweetnessMatch,
)
from app.services.food.knowledge.wine.type_registry import (
    WineTypeMatch,
)


@dataclass(
    frozen=True,
    kw_only=True,
)
class WineParseResult(BaseParseResult):
    wine_type: str | None = None
    grape: str | None = None
    region: str | None = None
    sweetness: str | None = None
    body: str | None = None
    acidity: str | None = None

    vintage: int | None = None
    alcohol_percent: float | None = None

    wine_type_confidence: float = 0.0
    grape_confidence: float = 0.0
    region_confidence: float = 0.0
    sweetness_confidence: float = 0.0
    body_confidence: float = 0.0
    acidity_confidence: float = 0.0

    wine_type_match: WineTypeMatch | None = None
    grape_match: WineGrapeMatch | None = None
    region_match: WineRegionMatch | None = None
    sweetness_match: WineSweetnessMatch | None = None
    body_match: WineBodyMatch | None = None
    acidity_match: WineAcidityMatch | None = None

    detected_keywords: list[str] = field(
        default_factory=list
    )
    warnings: list[str] = field(
        default_factory=list
    )

    def __post_init__(self) -> None:
        super().__post_init__()

        for field_name in (
            "wine_type_confidence",
            "grape_confidence",
            "region_confidence",
            "sweetness_confidence",
            "body_confidence",
            "acidity_confidence",
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

        if self.vintage is not None:
            vintage = int(self.vintage)

            if vintage < 1800 or vintage > 2100:
                object.__setattr__(
                    self,
                    "vintage",
                    None,
                )

        if self.alcohol_percent is not None:
            alcohol = max(
                0.0,
                min(
                    100.0,
                    float(self.alcohol_percent),
                ),
            )
            object.__setattr__(
                self,
                "alcohol_percent",
                alcohol,
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
    def matched_field_count(self) -> int:
        return sum(
            value is not None
            for value in (
                self.wine_type,
                self.grape,
                self.region,
                self.sweetness,
                self.body,
                self.acidity,
            )
        )

    @property
    def is_complete(self) -> bool:
        return self.matched_field_count == 6

    @property
    def is_usable(self) -> bool:
        return (
            self.wine_type is not None
            or self.grape is not None
            or self.region is not None
            or self.matched_field_count >= 2
        )

    @property
    def has_match(self) -> bool:
        return self.matched_field_count > 0

    def to_dict(self) -> dict[str, Any]:
        payload = super().to_dict()

        payload.update(
            {
                "wine_type": self.wine_type,
                "grape": self.grape,
                "region": self.region,
                "sweetness": self.sweetness,
                "body": self.body,
                "acidity": self.acidity,
                "vintage": self.vintage,
                "alcohol_percent": self.alcohol_percent,
                "wine_type_confidence": (
                    self.wine_type_confidence
                ),
                "grape_confidence": (
                    self.grape_confidence
                ),
                "region_confidence": (
                    self.region_confidence
                ),
                "sweetness_confidence": (
                    self.sweetness_confidence
                ),
                "body_confidence": (
                    self.body_confidence
                ),
                "acidity_confidence": (
                    self.acidity_confidence
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
            text = str(value).strip()

            if not text or text in seen:
                continue

            seen.add(text)
            result.append(text)

        return result