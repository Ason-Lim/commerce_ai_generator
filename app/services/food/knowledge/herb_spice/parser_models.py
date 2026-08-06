from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from app.services.food.knowledge.common.parser_models import (
    BaseParseResult,
)

if TYPE_CHECKING:
    from app.services.food.knowledge.herb_spice.form_registry import (
        HerbSpiceFormMatch,
    )
    from app.services.food.knowledge.herb_spice.herb_registry import (
        HerbMatch,
    )
    from app.services.food.knowledge.herb_spice.origin_registry import (
        HerbSpiceOriginMatch,
    )
    from app.services.food.knowledge.herb_spice.spice_registry import (
        SpiceMatch,
    )
    from app.services.food.knowledge.herb_spice.usage_registry import (
        HerbSpiceUsageMatch,
    )


@dataclass(
    frozen=True,
    kw_only=True,
)
class HerbSpiceParseResult(BaseParseResult):
    """
    Herb & Spice Parser result contract.

    Public parsing dimensions:
    - classification: herb or spice
    - ingredient: canonical Herb/Spice ingredient
    - origin: canonical origin
    - form: canonical product form
    - usage: canonical culinary usage

    Herb Registry와 Spice Registry의 검색 결과는 각각
    herb_match와 spice_match에 보존한다.

    이 모델은 다음 작업을 수행하지 않는다.
    - Registry 검색
    - 상품명 파싱
    - Attribute 구성
    - 점수 계산
    - Rule 적용
    - Provider orchestration
    """

    classification: str | None = None
    ingredient: str | None = None
    origin: str | None = None
    form: str | None = None
    usage: str | None = None

    classification_confidence: float = 0.0
    ingredient_confidence: float = 0.0
    origin_confidence: float = 0.0
    form_confidence: float = 0.0
    usage_confidence: float = 0.0

    herb_match: HerbMatch | None = None
    spice_match: SpiceMatch | None = None
    origin_match: HerbSpiceOriginMatch | None = None
    form_match: HerbSpiceFormMatch | None = None
    usage_match: HerbSpiceUsageMatch | None = None

    detected_keywords: list[str] = field(
        default_factory=list
    )
    warnings: list[str] = field(
        default_factory=list
    )

    def __post_init__(self) -> None:
        super().__post_init__()

        classification = self._normalize_classification(
            self.classification
        )
        ingredient = self._optional_string(
            self.ingredient
        )
        origin = self._optional_string(
            self.origin
        )
        form = self._optional_string(
            self.form
        )
        usage = self._optional_string(
            self.usage
        )

        object.__setattr__(
            self,
            "classification",
            classification,
        )
        object.__setattr__(
            self,
            "ingredient",
            ingredient,
        )
        object.__setattr__(
            self,
            "origin",
            origin,
        )
        object.__setattr__(
            self,
            "form",
            form,
        )
        object.__setattr__(
            self,
            "usage",
            usage,
        )

        for field_name in (
            "classification_confidence",
            "ingredient_confidence",
            "origin_confidence",
            "form_confidence",
            "usage_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                self._clamp_confidence(
                    getattr(self, field_name)
                ),
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
    def has_classification(self) -> bool:
        return self.classification is not None

    @property
    def has_ingredient(self) -> bool:
        return self.ingredient is not None

    @property
    def has_origin(self) -> bool:
        return self.origin is not None

    @property
    def has_form(self) -> bool:
        return self.form is not None

    @property
    def has_usage(self) -> bool:
        return self.usage is not None

    @property
    def has_herb_match(self) -> bool:
        return self.herb_match is not None

    @property
    def has_spice_match(self) -> bool:
        return self.spice_match is not None

    @property
    def has_ingredient_conflict(self) -> bool:
        """
        Herb와 Spice Registry가 동시에 일치했는지 반환한다.

        충돌 해결은 Parser 또는 Rule 계층의 책임이며,
        이 모델은 관찰 가능한 상태만 제공한다.
        """
        return (
            self.herb_match is not None
            and self.spice_match is not None
        )

    @property
    def matched_field_count(self) -> int:
        """
        핵심 분석 축 중 확인된 필드 수를 반환한다.

        classification은 ingredient에서 파생되는 분류 정보이므로
        별도 완성도 축으로 중복 계산하지 않는다.
        """
        return sum(
            (
                self.has_ingredient,
                self.has_origin,
                self.has_form,
                self.has_usage,
            )
        )

    @property
    def is_complete(self) -> bool:
        return self.matched_field_count == 4

    @property
    def is_usable(self) -> bool:
        """
        Ingredient가 확인되었거나,
        보조 속성이 두 개 이상 확인되면 사용 가능하다.
        """
        return (
            self.has_ingredient
            or self.matched_field_count >= 2
        )

    @property
    def has_match(self) -> bool:
        return self.matched_field_count > 0

    def to_dict(self) -> dict[str, Any]:
        payload = super().to_dict()

        payload.update(
            {
                "classification": self.classification,
                "ingredient": self.ingredient,
                "origin": self.origin,
                "form": self.form,
                "usage": self.usage,
                "classification_confidence": (
                    self.classification_confidence
                ),
                "ingredient_confidence": (
                    self.ingredient_confidence
                ),
                "origin_confidence": (
                    self.origin_confidence
                ),
                "form_confidence": (
                    self.form_confidence
                ),
                "usage_confidence": (
                    self.usage_confidence
                ),
                "herb_match": self._serialize_value(
                    self.herb_match
                ),
                "spice_match": self._serialize_value(
                    self.spice_match
                ),
                "origin_match": self._serialize_value(
                    self.origin_match
                ),
                "form_match": self._serialize_value(
                    self.form_match
                ),
                "usage_match": self._serialize_value(
                    self.usage_match
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
                "has_match": self.has_match,
                "has_ingredient_conflict": (
                    self.has_ingredient_conflict
                ),
            }
        )

        return payload

    @staticmethod
    def _normalize_classification(
        value: Any,
    ) -> str | None:
        normalized = str(
            value or ""
        ).strip().casefold()

        if not normalized:
            return None

        if normalized not in {
            "herb",
            "spice",
        }:
            raise ValueError(
                "classification must be "
                "'herb', 'spice', or None"
            )

        return normalized

    @staticmethod
    def _optional_string(
        value: Any,
    ) -> str | None:
        if value is None:
            return None

        normalized = str(value).strip()

        return normalized or None

    @staticmethod
    def _clamp_confidence(
        value: Any,
    ) -> float:
        try:
            normalized = float(value)
        except (TypeError, ValueError):
            normalized = 0.0

        return max(
            0.0,
            min(
                1.0,
                normalized,
            ),
        )

    @staticmethod
    def _deduplicate_strings(
        values: list[str],
    ) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()

        for value in values:
            text = str(value).strip()
            key = text.casefold()

            if not text or key in seen:
                continue

            seen.add(key)
            result.append(text)

        return result


__all__ = [
    "HerbSpiceParseResult",
]
