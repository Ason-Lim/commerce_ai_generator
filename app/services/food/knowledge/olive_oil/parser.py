from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from app.services.food.knowledge.common.parser_base import (
    BaseKnowledgeParser,
)
from app.services.food.knowledge.olive_oil.grade_registry import (
    OliveOilGradeMatch,
    OliveOilGradeRegistry,
)
from app.services.food.knowledge.olive_oil.origin_registry import (
    OliveOilOriginMatch,
    OliveOilOriginRegistry,
)
from app.services.food.knowledge.olive_oil.parser_models import (
    OliveOilParseResult,
)
from app.services.food.knowledge.olive_oil.processing_registry import (
    OliveOilProcessingMatch,
    OliveOilProcessingRegistry,
)
from app.services.food.knowledge.olive_oil.type_registry import (
    OliveOilTypeMatch,
    OliveOilTypeRegistry,
)
from app.services.food.knowledge.olive_oil.variety_registry import (
    OliveOilVarietyMatch,
    OliveOilVarietyRegistry,
)


class OliveOilParser(
    BaseKnowledgeParser[OliveOilParseResult]
):
    """
    Olive Oil 상품 Parser.

    책임:
    - 상품 텍스트 구성 및 정규화
    - 구조화 필드 우선 처리
    - Olive Oil Registry 검색
    - confidence와 warning 계산
    - OliveOilParseResult 생성

    담당하지 않는 책임:
    - Attribute 구성
    - 점수 계산
    - Rule 적용
    - Provider orchestration
    - Registry 데이터 수정
    """

    _NAME_FIELDS: tuple[str, ...] = (
        "product_name",
        "title",
        "name",
        "raw_name",
        "display_name",
    )

    _TYPE_FIELDS: tuple[str, ...] = (
        "olive_oil_type",
        "oil_type",
        "type",
        "style",
        "product_type",
    )

    _VARIETY_FIELDS: tuple[str, ...] = (
        "variety",
        "cultivar",
        "olive_variety",
        "olive_cultivar",
        "varietal",
    )

    _ORIGIN_FIELDS: tuple[str, ...] = (
        "origin",
        "country",
        "origin_country",
        "country_of_origin",
        "region",
        "production_region",
    )

    _PROCESSING_FIELDS: tuple[str, ...] = (
        "processing",
        "process",
        "processing_method",
        "extraction_method",
        "pressing_method",
        "filtration",
    )

    _GRADE_FIELDS: tuple[str, ...] = (
        "grade",
        "olive_oil_grade",
        "quality_grade",
        "classification",
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
        type_registry: OliveOilTypeRegistry | None = None,
        variety_registry: OliveOilVarietyRegistry | None = None,
        origin_registry: OliveOilOriginRegistry | None = None,
        processing_registry: OliveOilProcessingRegistry | None = None,
        grade_registry: OliveOilGradeRegistry | None = None,
    ) -> None:
        self.type_registry = (
            type_registry
            if type_registry is not None
            else OliveOilTypeRegistry()
        )
        self.variety_registry = (
            variety_registry
            if variety_registry is not None
            else OliveOilVarietyRegistry()
        )
        self.origin_registry = (
            origin_registry
            if origin_registry is not None
            else OliveOilOriginRegistry()
        )
        self.processing_registry = (
            processing_registry
            if processing_registry is not None
            else OliveOilProcessingRegistry()
        )
        self.grade_registry = (
            grade_registry
            if grade_registry is not None
            else OliveOilGradeRegistry()
        )

    def parse(
        self,
        text: str,
    ) -> OliveOilParseResult:
        """Parse a plain Olive Oil product text."""

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
    ) -> OliveOilParseResult:
        """Parse an Olive Oil product mapping."""

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
            variety_match=self._match_structured_first(
                product=product,
                field_names=self._VARIETY_FIELDS,
                registry=self.variety_registry,
                fallback_text=normalized_text,
            ),
            origin_match=self._match_structured_first(
                product=product,
                field_names=self._ORIGIN_FIELDS,
                registry=self.origin_registry,
                fallback_text=normalized_text,
            ),
            processing_match=self._match_structured_first(
                product=product,
                field_names=self._PROCESSING_FIELDS,
                registry=self.processing_registry,
                fallback_text=normalized_text,
            ),
            grade_match=self._match_structured_first(
                product=product,
                field_names=self._GRADE_FIELDS,
                registry=self.grade_registry,
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
    ) -> OliveOilParseResult:
        return self._build_result(
            original_text=original_text,
            normalized_text=normalized_text,
            type_match=self.type_registry.match(
                normalized_text
            ),
            variety_match=self.variety_registry.match(
                normalized_text
            ),
            origin_match=self.origin_registry.match(
                normalized_text
            ),
            processing_match=self.processing_registry.match(
                normalized_text
            ),
            grade_match=self.grade_registry.match(
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
        type_match: OliveOilTypeMatch | None,
        variety_match: OliveOilVarietyMatch | None,
        origin_match: OliveOilOriginMatch | None,
        processing_match: OliveOilProcessingMatch | None,
        grade_match: OliveOilGradeMatch | None,
        metadata: Mapping[str, Any],
    ) -> OliveOilParseResult:
        matches = (
            type_match,
            variety_match,
            origin_match,
            processing_match,
            grade_match,
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
                "category_id": "olive_oil",
                "matched_field_count": (
                    matched_field_count
                ),
                "expected_field_count": 5,
                "is_complete": (
                    matched_field_count == 5
                ),
            }
        )

        return OliveOilParseResult(
            original_text=original_text,
            normalized_text=normalized_text,
            confidence=confidence,
            metadata=result_metadata,
            olive_oil_type=self._canonical_name(
                type_match
            ),
            variety=self._canonical_name(
                variety_match
            ),
            origin=self._canonical_name(
                origin_match
            ),
            processing=self._canonical_name(
                processing_match
            ),
            grade=self._canonical_name(
                grade_match
            ),
            olive_oil_type_confidence=(
                self._match_confidence(
                    type_match
                )
            ),
            variety_confidence=(
                self._match_confidence(
                    variety_match
                )
            ),
            origin_confidence=(
                self._match_confidence(
                    origin_match
                )
            ),
            processing_confidence=(
                self._match_confidence(
                    processing_match
                )
            ),
            grade_confidence=(
                self._match_confidence(
                    grade_match
                )
            ),
            olive_oil_type_match=type_match,
            variety_match=variety_match,
            origin_match=origin_match,
            processing_match=processing_match,
            grade_match=grade_match,
            detected_keywords=(
                self._detected_keywords(
                    matches
                )
            ),
            warnings=self._build_warnings(
                type_match=type_match,
                grade_match=grade_match,
                matched_field_count=(
                    matched_field_count
                ),
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

        return str(
            match.entry.canonical_name
        )

    @staticmethod
    def _match_confidence(
        match: Any,
    ) -> float:
        if match is None:
            return 0.0

        return float(
            match.confidence
        )

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

            if not keyword or key in seen:
                continue

            seen.add(key)
            result.append(keyword)

        return result

    @staticmethod
    def _build_warnings(
        *,
        type_match: OliveOilTypeMatch | None,
        grade_match: OliveOilGradeMatch | None,
        matched_field_count: int,
    ) -> list[str]:
        warnings: list[str] = []

        if matched_field_count == 0:
            warnings.append(
                "Olive Oil Registry에서 일치하는 "
                "속성을 찾지 못했습니다."
            )
            return warnings

        if (
            type_match is None
            and grade_match is None
        ):
            warnings.append(
                "Olive Oil 종류 또는 등급이 "
                "명확하게 확인되지 않았습니다."
            )

        if matched_field_count < 5:
            warnings.append(
                "일부 Olive Oil 속성이 "
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
            *cls._VARIETY_FIELDS,
            *cls._ORIGIN_FIELDS,
            *cls._PROCESSING_FIELDS,
            *cls._GRADE_FIELDS,
            *cls._OPTION_FIELDS,
        ):
            if field_name in seen:
                continue

            seen.add(field_name)
            result.append(field_name)

        return tuple(result)

    @staticmethod
    def _stringify_value(
        value: Any,
    ) -> str:
        if value is None:
            return ""

        if isinstance(
            value,
            (list, tuple, set, frozenset),
        ):
            return " ".join(
                str(item).strip()
                for item in value
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
            text = str(value).strip()
            key = text.casefold()

            if not text or key in seen:
                continue

            seen.add(key)
            result.append(text)

        return result

    @classmethod
    def _matched_source_fields(
        cls,
        product: Mapping[str, Any],
    ) -> list[str]:
        result: list[str] = []

        for field_name in cls._all_text_fields():
            if cls._stringify_value(
                product.get(field_name)
            ):
                result.append(field_name)

        return result


__all__ = [
    "OliveOilParser",
]
