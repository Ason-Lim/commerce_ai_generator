from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from app.services.food.knowledge.common.parser_base import (
    BaseKnowledgeParser,
)
from app.services.food.knowledge.tea.flavor_registry import (
    TeaFlavorMatch,
    TeaFlavorRegistry,
)
from app.services.food.knowledge.tea.origin_registry import (
    TeaOriginMatch,
    TeaOriginRegistry,
)
from app.services.food.knowledge.tea.oxidation_registry import (
    TeaOxidationMatch,
    TeaOxidationRegistry,
)
from app.services.food.knowledge.tea.parser_models import (
    TeaParseResult,
)
from app.services.food.knowledge.tea.processing_registry import (
    TeaProcessingMatch,
    TeaProcessingRegistry,
)
from app.services.food.knowledge.tea.type_registry import (
    TeaTypeMatch,
    TeaTypeRegistry,
)
from app.services.food.knowledge.tea.variety_registry import (
    TeaVarietyMatch,
    TeaVarietyRegistry,
)


class TeaParser(
    BaseKnowledgeParser[TeaParseResult]
):
    """Tea 상품 Parser."""

    _NAME_FIELDS: tuple[str, ...] = (
        "product_name",
        "title",
        "name",
        "raw_name",
        "display_name",
    )

    _TYPE_FIELDS: tuple[str, ...] = (
        "tea_type",
        "type",
        "style",
        "tea_style",
        "category",
    )

    _ORIGIN_FIELDS: tuple[str, ...] = (
        "origin",
        "country",
        "origin_country",
        "country_of_origin",
        "tea_origin",
        "region",
    )

    _VARIETY_FIELDS: tuple[str, ...] = (
        "variety",
        "cultivar",
        "tea_variety",
        "botanical_variety",
        "species",
    )

    _PROCESSING_FIELDS: tuple[str, ...] = (
        "processing",
        "process",
        "processing_method",
        "process_method",
        "tea_processing",
    )

    _OXIDATION_FIELDS: tuple[str, ...] = (
        "oxidation",
        "oxidation_level",
        "oxidation_type",
        "oxidation_degree",
    )

    _FLAVOR_FIELDS: tuple[str, ...] = (
        "flavor",
        "flavour",
        "aroma",
        "flavor_notes",
        "flavour_notes",
        "tasting_notes",
        "sensory_notes",
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
        type_registry: TeaTypeRegistry | None = None,
        origin_registry: TeaOriginRegistry | None = None,
        variety_registry: TeaVarietyRegistry | None = None,
        processing_registry: TeaProcessingRegistry | None = None,
        oxidation_registry: TeaOxidationRegistry | None = None,
        flavor_registry: TeaFlavorRegistry | None = None,
    ) -> None:
        self.type_registry = (
            type_registry
            if type_registry is not None
            else TeaTypeRegistry()
        )
        self.origin_registry = (
            origin_registry
            if origin_registry is not None
            else TeaOriginRegistry()
        )
        self.variety_registry = (
            variety_registry
            if variety_registry is not None
            else TeaVarietyRegistry()
        )
        self.processing_registry = (
            processing_registry
            if processing_registry is not None
            else TeaProcessingRegistry()
        )
        self.oxidation_registry = (
            oxidation_registry
            if oxidation_registry is not None
            else TeaOxidationRegistry()
        )
        self.flavor_registry = (
            flavor_registry
            if flavor_registry is not None
            else TeaFlavorRegistry()
        )

    def parse(
        self,
        text: str,
    ) -> TeaParseResult:
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
    ) -> TeaParseResult:
        if not isinstance(product, Mapping):
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

        return self._build_result(
            original_text=original_text,
            normalized_text=normalized_text,
            type_match=self._match_structured_first(
                product=product,
                field_names=self._TYPE_FIELDS,
                registry=self.type_registry,
                fallback_text=normalized_text,
            ),
            origin_match=self._match_structured_first(
                product=product,
                field_names=self._ORIGIN_FIELDS,
                registry=self.origin_registry,
                fallback_text=normalized_text,
            ),
            variety_match=self._match_structured_first(
                product=product,
                field_names=self._VARIETY_FIELDS,
                registry=self.variety_registry,
                fallback_text=normalized_text,
            ),
            processing_match=self._match_structured_first(
                product=product,
                field_names=self._PROCESSING_FIELDS,
                registry=self.processing_registry,
                fallback_text=normalized_text,
            ),
            oxidation_match=self._match_structured_first(
                product=product,
                field_names=self._OXIDATION_FIELDS,
                registry=self.oxidation_registry,
                fallback_text=normalized_text,
            ),
            flavor_match=self._match_structured_first(
                product=product,
                field_names=self._FLAVOR_FIELDS,
                registry=self.flavor_registry,
                fallback_text=normalized_text,
            ),
            metadata={
                "source_type": "mapping",
                "source_fields": self._matched_source_fields(
                    product
                ),
                "structured_field_priority": True,
            },
        )

    def _parse_text(
        self,
        *,
        original_text: str,
        normalized_text: str,
    ) -> TeaParseResult:
        return self._build_result(
            original_text=original_text,
            normalized_text=normalized_text,
            type_match=self.type_registry.match(
                normalized_text
            ),
            origin_match=self.origin_registry.match(
                normalized_text
            ),
            variety_match=self.variety_registry.match(
                normalized_text
            ),
            processing_match=self.processing_registry.match(
                normalized_text
            ),
            oxidation_match=self.oxidation_registry.match(
                normalized_text
            ),
            flavor_match=self.flavor_registry.match(
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
        type_match: TeaTypeMatch | None,
        origin_match: TeaOriginMatch | None,
        variety_match: TeaVarietyMatch | None,
        processing_match: TeaProcessingMatch | None,
        oxidation_match: TeaOxidationMatch | None,
        flavor_match: TeaFlavorMatch | None,
        metadata: Mapping[str, Any],
    ) -> TeaParseResult:
        matches = (
            type_match,
            origin_match,
            variety_match,
            processing_match,
            oxidation_match,
            flavor_match,
        )

        matched_field_count = sum(
            match is not None
            for match in matches
        )

        confidences = [
            float(match.confidence)
            for match in matches
            if match is not None
        ]

        confidence = (
            round(
                sum(confidences) / len(confidences),
                4,
            )
            if confidences
            else 0.0
        )

        result_metadata = dict(metadata)
        result_metadata.update(
            {
                "category_id": "tea",
                "matched_field_count": matched_field_count,
                "expected_field_count": 6,
                "is_complete": matched_field_count == 6,
            }
        )

        return TeaParseResult(
            original_text=original_text,
            normalized_text=normalized_text,
            confidence=confidence,
            metadata=result_metadata,
            tea_type=self._canonical_name(type_match),
            origin=self._canonical_name(origin_match),
            variety=self._canonical_name(variety_match),
            processing=self._canonical_name(
                processing_match
            ),
            oxidation=self._canonical_name(
                oxidation_match
            ),
            flavor=self._canonical_name(flavor_match),
            tea_type_confidence=self._match_confidence(
                type_match
            ),
            origin_confidence=self._match_confidence(
                origin_match
            ),
            variety_confidence=self._match_confidence(
                variety_match
            ),
            processing_confidence=self._match_confidence(
                processing_match
            ),
            oxidation_confidence=self._match_confidence(
                oxidation_match
            ),
            flavor_confidence=self._match_confidence(
                flavor_match
            ),
            tea_type_match=type_match,
            origin_match=origin_match,
            variety_match=variety_match,
            processing_match=processing_match,
            oxidation_match=oxidation_match,
            flavor_match=flavor_match,
            detected_keywords=self._detected_keywords(
                matches
            ),
            warnings=self._build_warnings(
                type_match=type_match,
                matched_field_count=matched_field_count,
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

        values = self._deduplicate_texts(values)

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

        return str(match.entry.canonical_name)

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

            if keyword and key not in seen:
                seen.add(key)
                result.append(keyword)

        return result

    @staticmethod
    def _build_warnings(
        *,
        type_match: TeaTypeMatch | None,
        matched_field_count: int,
    ) -> list[str]:
        warnings: list[str] = []

        if matched_field_count == 0:
            warnings.append(
                "Tea Registry에서 일치하는 "
                "속성을 찾지 못했습니다."
            )
            return warnings

        if type_match is None:
            warnings.append(
                "Tea 종류가 명확하게 "
                "확인되지 않았습니다."
            )

        if matched_field_count < 6:
            warnings.append(
                "일부 Tea 속성이 "
                "확인되지 않았습니다."
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
            *cls._ORIGIN_FIELDS,
            *cls._VARIETY_FIELDS,
            *cls._PROCESSING_FIELDS,
            *cls._OXIDATION_FIELDS,
            *cls._FLAVOR_FIELDS,
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

        if isinstance(value, Mapping):
            values = [
                TeaParser._stringify_value(item)
                for item in value.values()
            ]
            return " ".join(
                item
                for item in values
                if item
            )

        if isinstance(
            value,
            (
                list,
                tuple,
                set,
                frozenset,
            ),
        ):
            values = [
                TeaParser._stringify_value(item)
                for item in value
            ]
            return " ".join(
                item
                for item in values
                if item
            )

        if isinstance(
            value,
            (
                int,
                float,
                bool,
            ),
        ):
            return str(value).strip()

        return ""

    @staticmethod
    def _deduplicate_texts(
        values: Sequence[str],
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
    "TeaParser",
]
