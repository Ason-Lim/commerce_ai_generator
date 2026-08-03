from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Sequence

from app.services.food.knowledge.cheese.aging_registry import (
    CheeseAgingMatch,
    CheeseAgingRegistry,
)
from app.services.food.knowledge.cheese.milk_source_registry import (
    CheeseMilkSourceMatch,
    CheeseMilkSourceRegistry,
)
from app.services.food.knowledge.cheese.origin_registry import (
    CheeseOriginMatch,
    CheeseOriginRegistry,
)
from app.services.food.knowledge.cheese.parser_models import (
    CheeseParseResult,
)
from app.services.food.knowledge.cheese.texture_registry import (
    CheeseTextureMatch,
    CheeseTextureRegistry,
)
from app.services.food.knowledge.cheese.type_registry import (
    CheeseTypeMatch,
    CheeseTypeRegistry,
)
from app.services.food.knowledge.common.parser_base import (
    BaseKnowledgeParser,
)


class CheeseParser(
    BaseKnowledgeParser[CheeseParseResult]
):
    """
    Cheese 상품 Parser.

    책임:
    - 상품 텍스트 구성 및 정규화
    - Cheese Registry 검색
    - 구조화 필드 우선 적용
    - confidence와 warning 계산
    - CheeseParseResult 생성

    담당하지 않는 책임:
    - Attribute 구성
    - 점수 계산
    - 추천 이유 생성
    - Provider orchestration
    """

    _NAME_FIELDS: tuple[str, ...] = (
        "product_name",
        "title",
        "name",
        "raw_name",
        "display_name",
    )

    _TYPE_FIELDS: tuple[str, ...] = (
        "cheese_type",
        "type",
        "style",
        "cheese_style",
        "variety",
    )

    _MILK_SOURCE_FIELDS: tuple[str, ...] = (
        "milk_source",
        "milk_type",
        "source_milk",
        "raw_milk",
    )

    _ORIGIN_FIELDS: tuple[str, ...] = (
        "origin",
        "country",
        "origin_country",
        "country_of_origin",
    )

    _TEXTURE_FIELDS: tuple[str, ...] = (
        "texture",
        "cheese_texture",
        "firmness",
    )

    _AGING_FIELDS: tuple[str, ...] = (
        "aging",
        "aging_type",
        "maturity",
        "maturation",
        "aged",
    )

    _OPTION_FIELDS: tuple[str, ...] = (
        "option",
        "option_name",
        "variant",
        "description",
        "summary",
    )

    def __init__(
        self,
        *,
        type_registry: CheeseTypeRegistry | None = None,
        milk_source_registry: (
            CheeseMilkSourceRegistry | None
        ) = None,
        origin_registry: (
            CheeseOriginRegistry | None
        ) = None,
        texture_registry: (
            CheeseTextureRegistry | None
        ) = None,
        aging_registry: CheeseAgingRegistry | None = None,
    ) -> None:
        self.type_registry = (
            type_registry
            if type_registry is not None
            else CheeseTypeRegistry()
        )

        self.milk_source_registry = (
            milk_source_registry
            if milk_source_registry is not None
            else CheeseMilkSourceRegistry()
        )

        self.origin_registry = (
            origin_registry
            if origin_registry is not None
            else CheeseOriginRegistry()
        )

        self.texture_registry = (
            texture_registry
            if texture_registry is not None
            else CheeseTextureRegistry()
        )

        self.aging_registry = (
            aging_registry
            if aging_registry is not None
            else CheeseAgingRegistry()
        )

    def parse(
        self,
        text: str,
    ) -> CheeseParseResult:
        original_text = str(text or "").strip()

        normalized_text = self.validate_text(
            original_text
        )

        return self._parse_text(
            original_text=original_text,
            normalized_text=normalized_text,
        )

    def parse_product(
        self,
        product: Mapping[str, Any],
    ) -> CheeseParseResult:
        if not isinstance(
            product,
            Mapping,
        ):
            raise TypeError(
                "product must be a Mapping"
            )

        if not product:
            raise ValueError(
                "product must not be empty"
            )

        original_text = self._build_product_text(
            product
        )

        normalized_text = self.validate_text(
            original_text
        )

        type_match = self._match_structured_first(
            product=product,
            field_names=self._TYPE_FIELDS,
            registry=self.type_registry,
            fallback_text=normalized_text,
        )

        milk_source_match = (
            self._match_structured_first(
                product=product,
                field_names=(
                    self._MILK_SOURCE_FIELDS
                ),
                registry=(
                    self.milk_source_registry
                ),
                fallback_text=normalized_text,
            )
        )

        origin_match = self._match_structured_first(
            product=product,
            field_names=self._ORIGIN_FIELDS,
            registry=self.origin_registry,
            fallback_text=normalized_text,
        )

        texture_match = (
            self._match_structured_first(
                product=product,
                field_names=self._TEXTURE_FIELDS,
                registry=self.texture_registry,
                fallback_text=normalized_text,
            )
        )

        aging_match = self._match_structured_first(
            product=product,
            field_names=self._AGING_FIELDS,
            registry=self.aging_registry,
            fallback_text=normalized_text,
        )

        result = self._build_result(
            original_text=original_text,
            normalized_text=normalized_text,
            type_match=type_match,
            milk_source_match=milk_source_match,
            origin_match=origin_match,
            texture_match=texture_match,
            aging_match=aging_match,
            metadata={
                "source_type": "mapping",
                "source_fields": (
                    self._matched_source_fields(
                        product
                    )
                ),
                "structured_field_priority": True,
            },
        )

        return result

    def _parse_text(
        self,
        *,
        original_text: str,
        normalized_text: str,
    ) -> CheeseParseResult:
        return self._build_result(
            original_text=original_text,
            normalized_text=normalized_text,
            type_match=self.type_registry.match(
                normalized_text
            ),
            milk_source_match=(
                self.milk_source_registry.match(
                    normalized_text
                )
            ),
            origin_match=self.origin_registry.match(
                normalized_text
            ),
            texture_match=(
                self.texture_registry.match(
                    normalized_text
                )
            ),
            aging_match=self.aging_registry.match(
                normalized_text
            ),
            metadata={
                "source_type": "text",
                "source_fields": [],
                "structured_field_priority": False,
            },
        )

    def _build_result(
        self,
        *,
        original_text: str,
        normalized_text: str,
        type_match: CheeseTypeMatch | None,
        milk_source_match: (
            CheeseMilkSourceMatch | None
        ),
        origin_match: CheeseOriginMatch | None,
        texture_match: CheeseTextureMatch | None,
        aging_match: CheeseAgingMatch | None,
        metadata: Mapping[str, Any],
    ) -> CheeseParseResult:
        matches = (
            type_match,
            milk_source_match,
            origin_match,
            texture_match,
            aging_match,
        )

        matched_field_count = sum(
            match is not None
            for match in matches
        )

        confidences = [
            match.confidence
            for match in matches
            if match is not None
        ]

        confidence = (
            round(
                sum(confidences)
                / len(confidences),
                4,
            )
            if confidences
            else 0.0
        )

        detected_keywords = (
            self._detected_keywords(
                matches
            )
        )

        warnings = self._build_warnings(
            type_match=type_match,
            milk_source_match=(
                milk_source_match
            ),
            origin_match=origin_match,
            texture_match=texture_match,
            aging_match=aging_match,
        )

        result_metadata = dict(metadata)
        result_metadata.update(
            {
                "category_id": "cheese",
                "matched_field_count": (
                    matched_field_count
                ),
                "expected_field_count": 5,
                "is_complete": (
                    matched_field_count == 5
                ),
            }
        )

        return CheeseParseResult(
            original_text=original_text,
            normalized_text=normalized_text,
            confidence=confidence,
            metadata=result_metadata,
            cheese_type=(
                self._canonical_name(
                    type_match
                )
            ),
            milk_source=(
                self._canonical_name(
                    milk_source_match
                )
            ),
            origin=(
                self._canonical_name(
                    origin_match
                )
            ),
            texture=(
                self._canonical_name(
                    texture_match
                )
            ),
            aging=(
                self._canonical_name(
                    aging_match
                )
            ),
            cheese_type_confidence=(
                self._match_confidence(
                    type_match
                )
            ),
            milk_source_confidence=(
                self._match_confidence(
                    milk_source_match
                )
            ),
            origin_confidence=(
                self._match_confidence(
                    origin_match
                )
            ),
            texture_confidence=(
                self._match_confidence(
                    texture_match
                )
            ),
            aging_confidence=(
                self._match_confidence(
                    aging_match
                )
            ),
            cheese_type_match=type_match,
            milk_source_match=milk_source_match,
            origin_match=origin_match,
            texture_match=texture_match,
            aging_match=aging_match,
            detected_keywords=detected_keywords,
            warnings=warnings,
        )

    def _build_product_text(
        self,
        product: Mapping[str, Any],
    ) -> str:
        values: list[str] = []

        for field_name in self._all_text_fields():
            value = self._stringify_value(
                product.get(field_name)
            )

            if value:
                values.append(value)

        values = self._deduplicate_texts(
            values
        )

        if not values:
            raise ValueError(
                "product does not contain "
                "a usable text field"
            )

        return " ".join(values)

    def _match_structured_first(
        self,
        *,
        product: Mapping[str, Any],
        field_names: Sequence[str],
        registry: Any,
        fallback_text: str,
    ) -> Any:
        structured_values = [
            self._stringify_value(
                product.get(field_name)
            )
            for field_name in field_names
        ]

        structured_values = [
            value
            for value in structured_values
            if value
        ]

        if structured_values:
            structured_text = " ".join(
                self._deduplicate_texts(
                    structured_values
                )
            )

            match = registry.match(
                structured_text
            )

            if match is not None:
                return match

        return registry.match(
            fallback_text
        )

    @staticmethod
    def _canonical_name(
        match: Any,
    ) -> str | None:
        if match is None:
            return None

        return match.entry.canonical_name

    @staticmethod
    def _match_confidence(
        match: Any,
    ) -> float:
        if match is None:
            return 0.0

        return float(match.confidence)

    @staticmethod
    def _detected_keywords(
        matches: Sequence[Any],
    ) -> list[str]:
        keywords: list[str] = []
        seen: set[str] = set()

        for match in matches:
            if match is None:
                continue

            keyword = str(
                match.matched_alias
            ).strip()

            normalized = keyword.casefold()

            if (
                keyword
                and normalized not in seen
            ):
                seen.add(normalized)
                keywords.append(keyword)

        return keywords

    @staticmethod
    def _build_warnings(
        *,
        type_match: CheeseTypeMatch | None,
        milk_source_match: (
            CheeseMilkSourceMatch | None
        ),
        origin_match: CheeseOriginMatch | None,
        texture_match: CheeseTextureMatch | None,
        aging_match: CheeseAgingMatch | None,
    ) -> list[str]:
        warnings: list[str] = []

        if type_match is None:
            warnings.append(
                "치즈 종류를 확인하지 못했습니다."
            )

        if milk_source_match is None:
            warnings.append(
                "원유 종류를 확인하지 못했습니다."
            )

        if origin_match is None:
            warnings.append(
                "치즈 원산지를 확인하지 못했습니다."
            )

        if texture_match is None:
            warnings.append(
                "치즈 질감을 확인하지 못했습니다."
            )

        if aging_match is None:
            warnings.append(
                "치즈 숙성 정보를 확인하지 못했습니다."
            )

        return warnings

    @classmethod
    def _all_text_fields(
        cls,
    ) -> tuple[str, ...]:
        result: list[str] = []
        seen: set[str] = set()

        for field_name in (
            *cls._NAME_FIELDS,
            *cls._TYPE_FIELDS,
            *cls._MILK_SOURCE_FIELDS,
            *cls._ORIGIN_FIELDS,
            *cls._TEXTURE_FIELDS,
            *cls._AGING_FIELDS,
            *cls._OPTION_FIELDS,
        ):
            if field_name in seen:
                continue

            seen.add(field_name)
            result.append(field_name)

        return tuple(result)

    @classmethod
    def _matched_source_fields(
        cls,
        product: Mapping[str, Any],
    ) -> list[str]:
        return [
            field_name
            for field_name in cls._all_text_fields()
            if cls._stringify_value(
                product.get(field_name)
            )
        ]

    @staticmethod
    def _stringify_value(
        value: Any,
    ) -> str:
        if value is None:
            return ""

        if isinstance(value, str):
            return value.strip()

        if isinstance(
            value,
            (list, tuple, set, frozenset),
        ):
            return " ".join(
                str(item).strip()
                for item in value
                if str(item).strip()
            )

        if isinstance(value, Mapping):
            return " ".join(
                str(item).strip()
                for item in value.values()
                if str(item).strip()
            )

        return str(value).strip()

    @staticmethod
    def _deduplicate_texts(
        values: Sequence[str],
    ) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()

        for value in values:
            normalized = str(value).strip()

            if not normalized:
                continue

            key = normalized.casefold()

            if key in seen:
                continue

            seen.add(key)
            result.append(normalized)

        return result


__all__ = [
    "CheeseParser",
]
