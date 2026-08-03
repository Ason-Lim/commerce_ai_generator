from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.common.parser_base import (
    BaseKnowledgeParser,
)
from app.services.food.knowledge.meat.lamb.age_registry import (
    LambAgeMatch,
    LambAgeRegistry,
)
from app.services.food.knowledge.meat.lamb.breed_registry import (
    LambBreedMatch,
    LambBreedRegistry,
)
from app.services.food.knowledge.meat.lamb.cut_registry import (
    LambCutMatch,
    LambCutRegistry,
)
from app.services.food.knowledge.meat.lamb.parser_models import (
    LambParseResult,
)


class LambParser(
    BaseKnowledgeParser[LambParseResult]
):
    """
    양고기 상품 Parser.

    담당 책임:
    - 입력 상품 텍스트 구성
    - 텍스트 정규화
    - 연령 분류 Registry 검색
    - 품종 Registry 검색
    - 부위 Registry 검색
    - 필드별 confidence 계산
    - LambParseResult 생성

    담당하지 않는 책임:
    - 상품 추천 점수 계산
    - 비즈니스 규칙 적용
    - 최종 점수 계산
    - UI 렌더링
    """

    _NAME_FIELDS: tuple[str, ...] = (
        "product_name",
        "title",
        "name",
        "raw_name",
        "display_name",
    )

    _AGE_FIELDS: tuple[str, ...] = (
        "age",
        "age_classification",
        "lamb_age",
        "meat_age",
    )

    _BREED_FIELDS: tuple[str, ...] = (
        "breed",
        "lamb_breed",
        "sheep_breed",
        "species",
    )

    _CUT_FIELDS: tuple[str, ...] = (
        "cut",
        "part",
        "lamb_cut",
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
        age_registry: LambAgeRegistry | None = None,
        breed_registry: LambBreedRegistry | None = None,
        cut_registry: LambCutRegistry | None = None,
    ) -> None:
        """
        Registry 생성자 주입을 지원한다.

        테스트에서는 별도의 Loader 또는 Registry를
        전달할 수 있다.
        """
        self.age_registry = (
            age_registry
            if age_registry is not None
            else LambAgeRegistry()
        )

        self.breed_registry = (
            breed_registry
            if breed_registry is not None
            else LambBreedRegistry()
        )

        self.cut_registry = (
            cut_registry
            if cut_registry is not None
            else LambCutRegistry()
        )

    def parse(
        self,
        text: str,
    ) -> LambParseResult:
        """
        하나의 문자열을 분석한다.
        """
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
    ) -> LambParseResult:
        """
        상품 Mapping에서 분석 대상 텍스트를 구성하고 파싱한다.
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

        return LambParseResult(
            original_text=result.original_text,
            normalized_text=(
                result.normalized_text
            ),
            confidence=result.confidence,
            metadata=metadata,
            age=result.age,
            breed=result.breed,
            cut=result.cut,
            age_confidence=(
                result.age_confidence
            ),
            breed_confidence=(
                result.breed_confidence
            ),
            cut_confidence=(
                result.cut_confidence
            ),
            age_match=result.age_match,
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
    ) -> LambParseResult:
        age_match = self.age_registry.match(
            normalized_text
        )
        breed_match = self.breed_registry.match(
            normalized_text
        )
        cut_match = self.cut_registry.match(
            normalized_text
        )

        age = self._canonical_name(
            age_match
        )
        breed = self._canonical_name(
            breed_match
        )
        cut = self._canonical_name(
            cut_match
        )

        age_confidence = self._match_confidence(
            age_match
        )
        breed_confidence = self._match_confidence(
            breed_match
        )
        cut_confidence = self._match_confidence(
            cut_match
        )

        detected_keywords = (
            self._detected_keywords(
                age_match=age_match,
                breed_match=breed_match,
                cut_match=cut_match,
            )
        )

        matched_field_count = sum(
            match is not None
            for match in (
                age_match,
                breed_match,
                cut_match,
            )
        )

        confidence = self._calculate_confidence(
            age_confidence=age_confidence,
            breed_confidence=breed_confidence,
            cut_confidence=cut_confidence,
        )

        warnings = self._build_warnings(
            normalized_text=normalized_text,
            age_match=age_match,
            breed_match=breed_match,
            cut_match=cut_match,
        )

        return LambParseResult(
            original_text=original_text,
            normalized_text=normalized_text,
            confidence=confidence,
            metadata={
                "category_id": "lamb",
                "matched_field_count": (
                    matched_field_count
                ),
                "expected_field_count": 3,
                "is_complete": (
                    matched_field_count == 3
                ),
            },
            age=age,
            breed=breed,
            cut=cut,
            age_confidence=age_confidence,
            breed_confidence=breed_confidence,
            cut_confidence=cut_confidence,
            age_match=age_match,
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
            raw_value = product.get(
                field_name
            )

            value = self._stringify_value(
                raw_value
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

    @classmethod
    def _all_text_fields(
        cls,
    ) -> tuple[str, ...]:
        ordered: list[str] = []
        seen: set[str] = set()

        for field_name in (
            *cls._NAME_FIELDS,
            *cls._AGE_FIELDS,
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
    def _stringify_value(
        value: Any,
    ) -> str:
        if value is None:
            return ""

        if isinstance(
            value,
            str,
        ):
            return value.strip()

        if isinstance(
            value,
            (list, tuple, set, frozenset),
        ):
            parts = [
                str(item).strip()
                for item in value
                if str(item).strip()
            ]

            return " ".join(parts)

        if isinstance(
            value,
            Mapping,
        ):
            return " ".join(
                str(item).strip()
                for item in value.values()
                if str(item).strip()
            )

        return str(value).strip()

    @staticmethod
    def _deduplicate_texts(
        values: list[str],
    ) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()

        for value in values:
            normalized = value.casefold().strip()

            if (
                not normalized
                or normalized in seen
            ):
                continue

            seen.add(normalized)
            result.append(value)

        return result

    @staticmethod
    def _canonical_name(
        match: (
            LambAgeMatch
            | LambBreedMatch
            | LambCutMatch
            | None
        ),
    ) -> str | None:
        if match is None:
            return None

        return match.entry.canonical_name

    @staticmethod
    def _match_confidence(
        match: (
            LambAgeMatch
            | LambBreedMatch
            | LambCutMatch
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
    def _calculate_confidence(
        *,
        age_confidence: float,
        breed_confidence: float,
        cut_confidence: float,
    ) -> float:
        """
        탐지된 필드 수와 필드별 매칭 신뢰도를 반영한다.

        세 필드가 모두 정확히 탐지되면 최대 1.0이다.
        """
        values = (
            age_confidence,
            breed_confidence,
            cut_confidence,
        )

        return max(
            0.0,
            min(
                1.0,
                sum(values) / len(values),
            ),
        )

    @staticmethod
    def _detected_keywords(
        *,
        age_match: LambAgeMatch | None,
        breed_match: LambBreedMatch | None,
        cut_match: LambCutMatch | None,
    ) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()

        for match in (
            age_match,
            breed_match,
            cut_match,
        ):
            if match is None:
                continue

            keyword = str(
                match.matched_alias
            ).strip()

            dedupe_key = keyword.casefold()

            if (
                not keyword
                or dedupe_key in seen
            ):
                continue

            seen.add(dedupe_key)
            result.append(keyword)

        return result

    @staticmethod
    def _build_warnings(
        *,
        normalized_text: str,
        age_match: LambAgeMatch | None,
        breed_match: LambBreedMatch | None,
        cut_match: LambCutMatch | None,
    ) -> list[str]:
        warnings: list[str] = []

        if age_match is None:
            warnings.append(
                "양고기 연령 분류를 "
                "확인하지 못했습니다."
            )

        if breed_match is None:
            warnings.append(
                "양 품종을 확인하지 못했습니다."
            )

        if cut_match is None:
            warnings.append(
                "양고기 부위를 확인하지 못했습니다."
            )

        if not normalized_text:
            warnings.append(
                "분석 가능한 상품명이 없습니다."
            )

        return warnings


__all__ = [
    "LambParser",
]
