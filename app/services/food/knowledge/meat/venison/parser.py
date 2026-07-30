from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.common.parser_base import (
    BaseKnowledgeParser,
)
from app.services.food.knowledge.meat.venison.breed_registry import (
    VenisonBreedMatch,
    VenisonBreedRegistry,
)
from app.services.food.knowledge.meat.venison.cut_registry import (
    VenisonCutMatch,
    VenisonCutRegistry,
)
from app.services.food.knowledge.meat.venison.parser_models import (
    VenisonParseResult,
)
from app.services.food.knowledge.meat.venison.type_registry import (
    VenisonTypeMatch,
    VenisonTypeRegistry,
)


class VenisonParser(
    BaseKnowledgeParser[VenisonParseResult]
):
    """
    사슴고기 상품 Parser.

    담당 책임:
    - 입력 상품 텍스트 구성
    - 사슴고기 유형 Registry 검색
    - 품종·종 Registry 검색
    - 부위 Registry 검색
    - 필드별 confidence 계산
    - VenisonParseResult 생성

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
        "venison_type",
        "deer_type",
        "meat_type",
        "product_type",
        "species_type",
    )

    _BREED_FIELDS: tuple[str, ...] = (
        "breed",
        "venison_breed",
        "deer_breed",
        "species",
        "deer_species",
    )

    _CUT_FIELDS: tuple[str, ...] = (
        "cut",
        "part",
        "venison_cut",
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
        type_registry: VenisonTypeRegistry | None = None,
        breed_registry: VenisonBreedRegistry | None = None,
        cut_registry: VenisonCutRegistry | None = None,
    ) -> None:
        self.type_registry = (
            type_registry
            if type_registry is not None
            else VenisonTypeRegistry()
        )
        self.breed_registry = (
            breed_registry
            if breed_registry is not None
            else VenisonBreedRegistry()
        )
        self.cut_registry = (
            cut_registry
            if cut_registry is not None
            else VenisonCutRegistry()
        )

    def parse(
        self,
        text: str,
    ) -> VenisonParseResult:
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
    ) -> VenisonParseResult:
        """
        구조화 상품 데이터를 분석한다.

        명시적인 도메인 필드가 존재하면 해당 필드를
        일반 상품명보다 우선하여 Registry에 매칭한다.

        우선순위:
        1. venison_type 계열 필드
        2. breed/species 계열 필드
        3. cut/part 계열 필드
        4. 매칭되지 않은 필드만 전체 결합 텍스트로 보완
        """
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

        combined_result = self._parse_text(
            original_text=original_text,
            normalized_text=normalized_text,
        )

        explicit_type_text = (
            self._build_selected_field_text(
                product,
                self._TYPE_FIELDS,
            )
        )
        explicit_breed_text = (
            self._build_selected_field_text(
                product,
                self._BREED_FIELDS,
            )
        )
        explicit_cut_text = (
            self._build_selected_field_text(
                product,
                self._CUT_FIELDS,
            )
        )

        explicit_type_match = (
            self.type_registry.match(
                explicit_type_text
            )
            if explicit_type_text
            else None
        )
        explicit_breed_match = (
            self.breed_registry.match(
                explicit_breed_text
            )
            if explicit_breed_text
            else None
        )
        explicit_cut_match = (
            self.cut_registry.match(
                explicit_cut_text
            )
            if explicit_cut_text
            else None
        )

        type_match = (
            explicit_type_match
            if explicit_type_match is not None
            else combined_result.venison_type_match
        )
        breed_match = (
            explicit_breed_match
            if explicit_breed_match is not None
            else combined_result.breed_match
        )
        cut_match = (
            explicit_cut_match
            if explicit_cut_match is not None
            else combined_result.cut_match
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

        detected_keywords = (
            self._detected_keywords(
                type_match=type_match,
                breed_match=breed_match,
                cut_match=cut_match,
            )
        )

        warnings = self._build_warnings(
            normalized_text=normalized_text,
            type_match=type_match,
            breed_match=breed_match,
            cut_match=cut_match,
        )

        metadata = {
            "category_id": "venison",
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
            "source_type": "mapping",
            "source_fields": (
                self._matched_source_fields(
                    product
                )
            ),
            "structured_field_priority": True,
            "explicit_match_fields": [
                field_name
                for field_name, match in (
                    (
                        "venison_type",
                        explicit_type_match,
                    ),
                    (
                        "breed",
                        explicit_breed_match,
                    ),
                    (
                        "cut",
                        explicit_cut_match,
                    ),
                )
                if match is not None
            ],
        }

        return VenisonParseResult(
            original_text=original_text,
            normalized_text=normalized_text,
            confidence=confidence,
            metadata=metadata,
            venison_type=self._canonical_name(
                type_match
            ),
            breed=self._canonical_name(
                breed_match
            ),
            cut=self._canonical_name(
                cut_match
            ),
            venison_type_confidence=(
                type_confidence
            ),
            breed_confidence=(
                breed_confidence
            ),
            cut_confidence=cut_confidence,
            venison_type_match=type_match,
            breed_match=breed_match,
            cut_match=cut_match,
            detected_keywords=(
                detected_keywords
            ),
            warnings=warnings,
        )

    def _build_selected_field_text(
        self,
        product: Mapping[str, Any],
        field_names: tuple[str, ...],
    ) -> str:
        """
        지정된 구조화 필드만 결합한다.

        빈 값과 중복 값은 제거하며, 일반 상품명이나
        다른 도메인 필드는 포함하지 않는다.
        """
        values: list[str] = []

        for field_name in field_names:
            value = self._stringify_value(
                product.get(field_name)
            )

            if value:
                values.append(value)

        return " ".join(
            self._deduplicate_texts(
                values
            )
        )

    def _parse_text(
        self,
        *,
        original_text: str,
        normalized_text: str,
    ) -> VenisonParseResult:
        type_match = self.type_registry.match(
            normalized_text
        )
        breed_match = self.breed_registry.match(
            normalized_text
        )
        cut_match = self.cut_registry.match(
            normalized_text
        )

        venison_type = self._canonical_name(
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

        return VenisonParseResult(
            original_text=original_text,
            normalized_text=normalized_text,
            confidence=confidence,
            metadata={
                "category_id": "venison",
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
            venison_type=venison_type,
            breed=breed,
            cut=cut,
            venison_type_confidence=(
                type_confidence
            ),
            breed_confidence=breed_confidence,
            cut_confidence=cut_confidence,
            venison_type_match=type_match,
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
        if value is None:
            return ""

        if isinstance(value, str):
            return value.strip()

        if isinstance(value, (int, float)):
            return str(value).strip()

        if isinstance(
            value,
            (list, tuple, set),
        ):
            parts = [
                VenisonParser._stringify_value(
                    item
                )
                for item in value
            ]

            return " ".join(
                part
                for part in parts
                if part
            )

        return ""

    @staticmethod
    def _deduplicate_texts(
        values: list[str],
    ) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()

        for value in values:
            text = str(value).strip()
            normalized = text.casefold()

            if (
                not text
                or normalized in seen
            ):
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
            VenisonTypeMatch
            | VenisonBreedMatch
            | VenisonCutMatch
            | None
        ),
    ) -> str | None:
        if match is None:
            return None

        return match.canonical_name

    @staticmethod
    def _match_confidence(
        match: (
            VenisonTypeMatch
            | VenisonBreedMatch
            | VenisonCutMatch
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
        type_match: VenisonTypeMatch | None,
        breed_match: VenisonBreedMatch | None,
        cut_match: VenisonCutMatch | None,
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
                    average
                    * (
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
        type_match: VenisonTypeMatch | None,
        breed_match: VenisonBreedMatch | None,
        cut_match: VenisonCutMatch | None,
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
                "사슴고기 유형, 품종 또는 부위를 "
                "인식하지 못했습니다."
            )
            return warnings

        if type_match is None:
            warnings.append(
                "사슴고기 상품 유형을 인식하지 "
                "못했습니다."
            )

        if breed_match is None:
            warnings.append(
                "사슴 품종 또는 종을 인식하지 "
                "못했습니다."
            )

        if cut_match is None:
            warnings.append(
                "사슴고기 부위를 인식하지 못했습니다."
            )

        return warnings


__all__ = [
    "VenisonParser",
]
