from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Sequence

from app.services.food.knowledge.coffee.bean_registry import (
    CoffeeBeanMatch,
    CoffeeBeanRegistry,
)
from app.services.food.knowledge.coffee.origin_registry import (
    CoffeeOriginMatch,
    CoffeeOriginRegistry,
)
from app.services.food.knowledge.coffee.parser_models import (
    CoffeeParseResult,
)
from app.services.food.knowledge.coffee.process_registry import (
    CoffeeProcessMatch,
    CoffeeProcessRegistry,
)
from app.services.food.knowledge.coffee.roast_registry import (
    CoffeeRoastMatch,
    CoffeeRoastRegistry,
)
from app.services.food.knowledge.common.parser_base import (
    BaseKnowledgeParser,
)


class CoffeeParser(
    BaseKnowledgeParser[CoffeeParseResult]
):
    """
    Coffee 상품 Parser.

    책임:
    - 상품 텍스트 구성 및 정규화
    - Coffee Registry 검색
    - 구조화 필드 우선 적용
    - confidence와 warning 계산
    - CoffeeParseResult 생성

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

    _BEAN_FIELDS: tuple[str, ...] = (
        "bean",
        "bean_type",
        "coffee_bean",
        "species",
        "coffee_species",
        "composition",
    )

    _ORIGIN_FIELDS: tuple[str, ...] = (
        "origin",
        "country",
        "origin_country",
        "country_of_origin",
        "coffee_origin",
        "region",
    )

    _ROAST_FIELDS: tuple[str, ...] = (
        "roast",
        "roast_level",
        "roasting",
        "roasting_level",
        "roast_type",
    )

    _PROCESS_FIELDS: tuple[str, ...] = (
        "process",
        "processing",
        "process_method",
        "processing_method",
        "coffee_process",
    )

    _OPTION_FIELDS: tuple[str, ...] = (
        "option",
        "option_name",
        "variant",
        "description",
        "summary",
        "flavor_notes",
        "tasting_notes",
    )

    def __init__(
        self,
        *,
        bean_registry: CoffeeBeanRegistry | None = None,
        origin_registry: CoffeeOriginRegistry | None = None,
        roast_registry: CoffeeRoastRegistry | None = None,
        process_registry: CoffeeProcessRegistry | None = None,
    ) -> None:
        self.bean_registry = (
            bean_registry
            if bean_registry is not None
            else CoffeeBeanRegistry()
        )

        self.origin_registry = (
            origin_registry
            if origin_registry is not None
            else CoffeeOriginRegistry()
        )

        self.roast_registry = (
            roast_registry
            if roast_registry is not None
            else CoffeeRoastRegistry()
        )

        self.process_registry = (
            process_registry
            if process_registry is not None
            else CoffeeProcessRegistry()
        )

    def parse(
        self,
        text: str,
    ) -> CoffeeParseResult:
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
    ) -> CoffeeParseResult:
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

        bean_match = self._match_structured_first(
            product=product,
            field_names=self._BEAN_FIELDS,
            registry=self.bean_registry,
            fallback_text=normalized_text,
        )

        origin_match = self._match_structured_first(
            product=product,
            field_names=self._ORIGIN_FIELDS,
            registry=self.origin_registry,
            fallback_text=normalized_text,
        )

        roast_match = self._match_structured_first(
            product=product,
            field_names=self._ROAST_FIELDS,
            registry=self.roast_registry,
            fallback_text=normalized_text,
        )

        process_match = (
            self._match_structured_first(
                product=product,
                field_names=self._PROCESS_FIELDS,
                registry=self.process_registry,
                fallback_text=normalized_text,
            )
        )

        return self._build_result(
            original_text=original_text,
            normalized_text=normalized_text,
            bean_match=bean_match,
            origin_match=origin_match,
            roast_match=roast_match,
            process_match=process_match,
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

    def _parse_text(
        self,
        *,
        original_text: str,
        normalized_text: str,
    ) -> CoffeeParseResult:
        return self._build_result(
            original_text=original_text,
            normalized_text=normalized_text,
            bean_match=self.bean_registry.match(
                normalized_text
            ),
            origin_match=self.origin_registry.match(
                normalized_text
            ),
            roast_match=self.roast_registry.match(
                normalized_text
            ),
            process_match=self.process_registry.match(
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
        bean_match: CoffeeBeanMatch | None,
        origin_match: CoffeeOriginMatch | None,
        roast_match: CoffeeRoastMatch | None,
        process_match: CoffeeProcessMatch | None,
        metadata: Mapping[str, Any],
    ) -> CoffeeParseResult:
        matches = (
            bean_match,
            origin_match,
            roast_match,
            process_match,
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

        result_metadata = dict(metadata)
        result_metadata.update(
            {
                "category_id": "coffee",
                "matched_field_count": (
                    matched_field_count
                ),
                "expected_field_count": 4,
                "is_complete": (
                    matched_field_count == 4
                ),
            }
        )

        return CoffeeParseResult(
            original_text=original_text,
            normalized_text=normalized_text,
            confidence=confidence,
            metadata=result_metadata,
            bean=self._canonical_name(
                bean_match
            ),
            origin=self._canonical_name(
                origin_match
            ),
            roast=self._canonical_name(
                roast_match
            ),
            process=self._canonical_name(
                process_match
            ),
            bean_confidence=(
                self._match_confidence(
                    bean_match
                )
            ),
            origin_confidence=(
                self._match_confidence(
                    origin_match
                )
            ),
            roast_confidence=(
                self._match_confidence(
                    roast_match
                )
            ),
            process_confidence=(
                self._match_confidence(
                    process_match
                )
            ),
            bean_match=bean_match,
            origin_match=origin_match,
            roast_match=roast_match,
            process_match=process_match,
            detected_keywords=(
                self._detected_keywords(
                    matches
                )
            ),
            warnings=self._build_warnings(
                bean_match=bean_match,
                origin_match=origin_match,
                roast_match=roast_match,
                process_match=process_match,
            ),
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
        result: list[str] = []
        seen: set[str] = set()

        for match in matches:
            if match is None:
                continue

            keyword = str(
                match.matched_alias
            ).strip()

            key = keyword.casefold()

            if (
                keyword
                and key not in seen
            ):
                seen.add(key)
                result.append(keyword)

        return result

    @staticmethod
    def _build_warnings(
        *,
        bean_match: CoffeeBeanMatch | None,
        origin_match: CoffeeOriginMatch | None,
        roast_match: CoffeeRoastMatch | None,
        process_match: CoffeeProcessMatch | None,
    ) -> list[str]:
        warnings: list[str] = []

        if bean_match is None:
            warnings.append(
                "원두 종류를 확인하지 못했습니다."
            )

        if origin_match is None:
            warnings.append(
                "커피 원산지를 확인하지 못했습니다."
            )

        if roast_match is None:
            warnings.append(
                "로스팅 단계를 확인하지 못했습니다."
            )

        if process_match is None:
            warnings.append(
                "가공 방식을 확인하지 못했습니다."
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
            *cls._BEAN_FIELDS,
            *cls._ORIGIN_FIELDS,
            *cls._ROAST_FIELDS,
            *cls._PROCESS_FIELDS,
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
    "CoffeeParser",
]
