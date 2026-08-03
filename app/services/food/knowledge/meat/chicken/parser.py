from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.common.parser_base import (
    BaseKnowledgeParser,
)
from app.services.food.knowledge.meat.chicken.breed_registry import (
    ChickenBreedMatch,
    ChickenBreedRegistry,
)
from app.services.food.knowledge.meat.chicken.cut_registry import (
    ChickenCutMatch,
    ChickenCutRegistry,
)
from app.services.food.knowledge.meat.chicken.parser_models import (
    ChickenParseResult,
)
from app.services.food.knowledge.meat.chicken.type_registry import (
    ChickenTypeMatch,
    ChickenTypeRegistry,
)


class ChickenParser(
    BaseKnowledgeParser[ChickenParseResult]
):
    """
    닭고기 상품 Parser.

    담당 책임:
    - 입력 상품 텍스트 구성
    - 상품 유형 Registry 검색
    - 품종·상업 계통 Registry 검색
    - 부위 Registry 검색
    - 필드별 confidence 계산
    - ChickenParseResult 생성

    담당하지 않는 책임:
    - Registry 점수 계산
    - 추천 또는 최종 점수 계산
    - 비즈니스 규칙 적용
    - UI 렌더링
    """

    _NAME_FIELDS: tuple[str, ...] = (
        "product_name",
        "title",
        "name",
        "raw_name",
        "display_name",
    )

    _TYPE_FIELDS: tuple[str, ...] = (
        "chicken_type",
        "poultry_type",
        "meat_type",
        "product_type",
        "species",
    )

    _BREED_FIELDS: tuple[str, ...] = (
        "breed",
        "chicken_breed",
        "poultry_breed",
        "strain",
        "line",
    )

    _CUT_FIELDS: tuple[str, ...] = (
        "cut",
        "part",
        "chicken_cut",
        "cut_name",
        "meat_part",
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
        type_registry: ChickenTypeRegistry | None = None,
        breed_registry: ChickenBreedRegistry | None = None,
        cut_registry: ChickenCutRegistry | None = None,
    ) -> None:
        self.type_registry = (
            type_registry
            if type_registry is not None
            else ChickenTypeRegistry()
        )
        self.breed_registry = (
            breed_registry
            if breed_registry is not None
            else ChickenBreedRegistry()
        )
        self.cut_registry = (
            cut_registry
            if cut_registry is not None
            else ChickenCutRegistry()
        )

    def parse(
        self,
        text: str,
    ) -> ChickenParseResult:
        normalized_text = self.validate_text(
            text
        )

        return self._parse_text(
            original_text=str(text),
            normalized_text=normalized_text,
        )

    def parse_product(
        self,
        product: Mapping[str, Any],
    ) -> ChickenParseResult:
        if not isinstance(
            product,
            Mapping,
        ):
            raise TypeError(
                "product must be a Mapping"
            )

        original_text = self._build_product_text(
            product
        )
        normalized_text = self.validate_text(
            original_text
        )

        result = self._parse_text(
            original_text=original_text,
            normalized_text=normalized_text,
        )

        metadata = dict(result.metadata)
        metadata.update(
            {
                "source_type": "mapping",
                "source_fields": (
                    self._matched_source_fields(
                        product
                    )
                ),
            }
        )

        return ChickenParseResult(
            original_text=result.original_text,
            normalized_text=result.normalized_text,
            confidence=result.confidence,
            metadata=metadata,
            chicken_type=result.chicken_type,
            breed=result.breed,
            cut=result.cut,
            chicken_type_confidence=(
                result.chicken_type_confidence
            ),
            breed_confidence=(
                result.breed_confidence
            ),
            cut_confidence=(
                result.cut_confidence
            ),
            chicken_type_match=(
                result.chicken_type_match
            ),
            breed_match=result.breed_match,
            cut_match=result.cut_match,
            detected_keywords=list(
                result.detected_keywords
            ),
            warnings=list(result.warnings),
        )

    def _parse_text(
        self,
        *,
        original_text: str,
        normalized_text: str,
    ) -> ChickenParseResult:
        type_match = self.type_registry.match(
            normalized_text
        )
        breed_match = self.breed_registry.match(
            normalized_text
        )
        cut_match = self.cut_registry.match(
            normalized_text
        )

        chicken_type = self._canonical_name(
            type_match
        )
        breed = self._canonical_name(
            breed_match
        )
        cut = self._canonical_name(
            cut_match
        )

        type_confidence = self._match_confidence(
            type_match
        )
        breed_confidence = self._match_confidence(
            breed_match
        )
        cut_confidence = self._match_confidence(
            cut_match
        )

        detected_keywords = (
            self._detected_keywords(
                type_match=type_match,
                breed_match=breed_match,
                cut_match=cut_match,
            )
        )

        matched_field_count = sum(
            match is not None
            for match in (
                type_match,
                breed_match,
                cut_match,
            )
        )

        confidence = self._calculate_confidence(
            type_confidence=type_confidence,
            breed_confidence=breed_confidence,
            cut_confidence=cut_confidence,
        )

        warnings = self._build_warnings(
            normalized_text=normalized_text,
            type_match=type_match,
            breed_match=breed_match,
            cut_match=cut_match,
        )

        return ChickenParseResult(
            original_text=original_text,
            normalized_text=normalized_text,
            confidence=confidence,
            metadata={
                "category_id": "chicken",
                "matched_field_count": (
                    matched_field_count
                ),
                "expected_field_count": 3,
                "is_complete": (
                    matched_field_count == 3
                ),
                "is_usable": (
                    type_match is not None
                    or cut_match is not None
                ),
            },
            chicken_type=chicken_type,
            breed=breed,
            cut=cut,
            chicken_type_confidence=(
                type_confidence
            ),
            breed_confidence=breed_confidence,
            cut_confidence=cut_confidence,
            chicken_type_match=type_match,
            breed_match=breed_match,
            cut_match=cut_match,
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

    def _matched_source_fields(
        self,
        product: Mapping[str, Any],
    ) -> list[str]:
        result: list[str] = []

        for field_name in self._all_text_fields():
            value = self._stringify_value(
                product.get(field_name)
            )

            if value:
                result.append(field_name)

        return result


    @staticmethod
    def _stringify_value(
        value: Any,
    ) -> str:
        """
        상품 Mapping의 값을 Parser 입력 문자열로 변환한다.

        문자열과 숫자는 직접 변환하고,
        list/tuple/set은 비어 있지 않은 항목만 결합한다.
        Mapping과 그 외 복합 객체는 Parser 입력에서 제외한다.
        """
        if value is None:
            return ""

        if isinstance(value, str):
            return value.strip()

        if isinstance(value, (int, float)):
            return str(value).strip()

        if isinstance(value, (list, tuple, set)):
            parts = [
                ChickenParser._stringify_value(item)
                for item in value
            ]
            return " ".join(
                part for part in parts if part
            )

        return ""

    @staticmethod
    def _deduplicate_texts(
        values: list[str],
    ) -> list[str]:
        """
        입력 순서를 유지하면서 중복 텍스트를 제거한다.
        """
        result: list[str] = []
        seen: set[str] = set()

        for value in values:
            text = str(value).strip()
            normalized = text.casefold()

            if not text or normalized in seen:
                continue

            seen.add(normalized)
            result.append(text)

        return result

    @classmethod
    def _all_text_fields(
        cls,
    ) -> tuple[str, ...]:
        ordered: list[str] = []
        seen: set[str] = set()

        for field_name in (
            *cls._NAME_FIELDS,
            *cls._TYPE_FIELDS,
            *cls._BREED_FIELDS,
            *cls._CUT_FIELDS,
            *cls._OPTION_FIELDS,
        ):
            if field_name in seen:
                continue

            seen.add(field_name)
            ordered.append(field_name)

        return tuple(ordered)

    @staticmethod
    def _canonical_name(
        match: (
            ChickenTypeMatch
            | ChickenBreedMatch
            | ChickenCutMatch
            | None
        ),
    ) -> str | None:
        if match is None:
            return None

        return match.canonical_name

    @staticmethod
    def _match_confidence(
        match: (
            ChickenTypeMatch
            | ChickenBreedMatch
            | ChickenCutMatch
            | None
        ),
    ) -> float:
        if match is None:
            return 0.0

        return max(
            0.0,
            min(
                1.0,
                float(match.confidence),
            ),
        )

    @staticmethod
    def _detected_keywords(
        *,
        type_match: ChickenTypeMatch | None,
        breed_match: ChickenBreedMatch | None,
        cut_match: ChickenCutMatch | None,
    ) -> list[str]:
        keywords: list[str] = []
        seen: set[str] = set()

        for match in (
            type_match,
            breed_match,
            cut_match,
        ):
            if match is None:
                continue

            keyword = str(
                match.matched_alias
            ).strip()

            normalized = keyword.casefold()

            if (
                not keyword
                or normalized in seen
            ):
                continue

            seen.add(normalized)
            keywords.append(keyword)

        return keywords

    @staticmethod
    def _calculate_confidence(
        *,
        type_confidence: float,
        breed_confidence: float,
        cut_confidence: float,
    ) -> float:
        available = [
            value
            for value in (
                type_confidence,
                breed_confidence,
                cut_confidence,
            )
            if value > 0.0
        ]

        if not available:
            return 0.0

        coverage = len(available) / 3.0
        average = sum(available) / len(
            available
        )

        return round(
            max(
                0.0,
                min(
                    1.0,
                    average * (
                        0.70
                        + 0.30 * coverage
                    ),
                ),
            ),
            4,
        )

    @staticmethod
    def _build_warnings(
        *,
        normalized_text: str,
        type_match: ChickenTypeMatch | None,
        breed_match: ChickenBreedMatch | None,
        cut_match: ChickenCutMatch | None,
    ) -> list[str]:
        warnings: list[str] = []

        if not normalized_text:
            warnings.append(
                "분석할 상품 텍스트가 없습니다."
            )
            return warnings

        if (
            type_match is None
            and breed_match is None
            and cut_match is None
        ):
            warnings.append(
                "닭고기 유형, 품종 또는 부위를 "
                "인식하지 못했습니다."
            )
            return warnings

        if type_match is None:
            warnings.append(
                "닭고기 상품 유형을 인식하지 "
                "못했습니다."
            )

        if breed_match is None:
            warnings.append(
                "닭 품종 또는 상업 계통을 인식하지 "
                "못했습니다."
            )

        if cut_match is None:
            warnings.append(
                "닭고기 부위를 인식하지 못했습니다."
            )

        return warnings


__all__ = [
    "ChickenParser",
]
