from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.food.knowledge.coffee.bean_registry import (
    CoffeeBeanMatch,
)
from app.services.food.knowledge.coffee.origin_registry import (
    CoffeeOriginMatch,
)
from app.services.food.knowledge.coffee.process_registry import (
    CoffeeProcessMatch,
)
from app.services.food.knowledge.coffee.roast_registry import (
    CoffeeRoastMatch,
)
from app.services.food.knowledge.common.parser_models import (
    BaseParseResult,
)


@dataclass(
    frozen=True,
    kw_only=True,
)
class CoffeeParseResult(BaseParseResult):
    """
    Coffee Parser 결과.

    Coffee Registry에서 탐지한 표준값, confidence,
    RegistryMatch 및 파싱 증거를 보존한다.
    """

    # Parsed values
    bean: str | None = None
    origin: str | None = None
    roast: str | None = None
    process: str | None = None

    # Field confidence
    bean_confidence: float = 0.0
    origin_confidence: float = 0.0
    roast_confidence: float = 0.0
    process_confidence: float = 0.0

    # Registry matches
    bean_match: CoffeeBeanMatch | None = None
    origin_match: CoffeeOriginMatch | None = None
    roast_match: CoffeeRoastMatch | None = None
    process_match: CoffeeProcessMatch | None = None

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
            "bean_confidence",
            "origin_confidence",
            "roast_confidence",
            "process_confidence",
        ):
            confidence = max(
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
                confidence,
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
    def has_bean(self) -> bool:
        return self.bean is not None

    @property
    def has_origin(self) -> bool:
        return self.origin is not None

    @property
    def has_roast(self) -> bool:
        return self.roast is not None

    @property
    def has_process(self) -> bool:
        return self.process is not None

    @property
    def matched_field_count(self) -> int:
        return sum(
            (
                self.has_bean,
                self.has_origin,
                self.has_roast,
                self.has_process,
            )
        )

    @property
    def is_complete(self) -> bool:
        return self.matched_field_count == 4

    @property
    def is_usable(self) -> bool:
        """
        원두 종이 확인되거나 독립적인 Coffee 속성이
        둘 이상 확인되면 Coffee 분석에 사용할 수 있다.

        국가명이나 로스팅 단어 하나만 탐지된 경우에는
        Coffee 도메인 결과로 확정하지 않는다.
        """
        return (
            self.has_bean
            or self.matched_field_count >= 2
        )

    @property
    def has_match(self) -> bool:
        return self.matched_field_count > 0

    def to_dict(self) -> dict[str, Any]:
        payload = super().to_dict()

        payload.update(
            {
                "bean": self.bean,
                "origin": self.origin,
                "roast": self.roast,
                "process": self.process,
                "bean_confidence": (
                    self.bean_confidence
                ),
                "origin_confidence": (
                    self.origin_confidence
                ),
                "roast_confidence": (
                    self.roast_confidence
                ),
                "process_confidence": (
                    self.process_confidence
                ),
                "bean_match": self._serialize_value(
                    self.bean_match
                ),
                "origin_match": (
                    self._serialize_value(
                        self.origin_match
                    )
                ),
                "roast_match": (
                    self._serialize_value(
                        self.roast_match
                    )
                ),
                "process_match": (
                    self._serialize_value(
                        self.process_match
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
    "CoffeeParseResult",
]
