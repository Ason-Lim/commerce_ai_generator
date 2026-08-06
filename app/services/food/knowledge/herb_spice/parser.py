from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from app.services.food.knowledge.common.parser_base import (
    BaseKnowledgeParser,
)
from app.services.food.knowledge.herb_spice.form_registry import (
    HerbSpiceFormMatch,
    HerbSpiceFormRegistry,
)
from app.services.food.knowledge.herb_spice.herb_registry import (
    HerbMatch,
    HerbRegistry,
)
from app.services.food.knowledge.herb_spice.origin_registry import (
    HerbSpiceOriginMatch,
    HerbSpiceOriginRegistry,
)
from app.services.food.knowledge.herb_spice.parser_models import (
    HerbSpiceParseResult,
)
from app.services.food.knowledge.herb_spice.spice_registry import (
    SpiceMatch,
    SpiceRegistry,
)
from app.services.food.knowledge.herb_spice.usage_registry import (
    HerbSpiceUsageMatch,
    HerbSpiceUsageRegistry,
)


class HerbSpiceParser(
    BaseKnowledgeParser[HerbSpiceParseResult]
):
    """
    Herb & Spice 상품 Parser.

    책임:
    - 상품 텍스트 구성 및 정규화
    - 구조화 필드 우선 처리
    - Herb/Spice Registry 검색
    - Origin/Form/Usage Registry 검색
    - Registry evidence 기반 ingredient 분류
    - confidence와 warning 계산
    - HerbSpiceParseResult 생성

    담당하지 않는 책임:
    - Attribute 구성
    - 점수 계산
    - Rule 적용
    - Provider orchestration
    - Registry 데이터 수정
    - 공통 Runtime 계약 변경
    """

    _NAME_FIELDS: tuple[str, ...] = (
        "product_name",
        "title",
        "name",
        "raw_name",
        "display_name",
    )

    _INGREDIENT_FIELDS: tuple[str, ...] = (
        "ingredient",
        "ingredient_name",
        "herb_spice",
        "herb_spice_name",
        "primary_ingredient",
    )

    _HERB_FIELDS: tuple[str, ...] = (
        "herb",
        "herb_name",
        "culinary_herb",
    )

    _SPICE_FIELDS: tuple[str, ...] = (
        "spice",
        "spice_name",
        "culinary_spice",
    )

    _CLASSIFICATION_FIELDS: tuple[str, ...] = (
        "classification",
        "ingredient_type",
        "herb_spice_type",
        "product_type",
    )

    _ORIGIN_FIELDS: tuple[str, ...] = (
        "origin",
        "country",
        "origin_country",
        "country_of_origin",
        "region",
        "production_region",
    )

    _FORM_FIELDS: tuple[str, ...] = (
        "form",
        "product_form",
        "ingredient_form",
        "spice_form",
        "herb_form",
        "format",
    )

    _USAGE_FIELDS: tuple[str, ...] = (
        "usage",
        "intended_usage",
        "recommended_usage",
        "culinary_usage",
        "use_case",
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
        herb_registry: HerbRegistry | None = None,
        spice_registry: SpiceRegistry | None = None,
        origin_registry: HerbSpiceOriginRegistry | None = None,
        form_registry: HerbSpiceFormRegistry | None = None,
        usage_registry: HerbSpiceUsageRegistry | None = None,
    ) -> None:
        self.herb_registry = (
            herb_registry
            if herb_registry is not None
            else HerbRegistry()
        )
        self.spice_registry = (
            spice_registry
            if spice_registry is not None
            else SpiceRegistry()
        )
        self.origin_registry = (
            origin_registry
            if origin_registry is not None
            else HerbSpiceOriginRegistry()
        )
        self.form_registry = (
            form_registry
            if form_registry is not None
            else HerbSpiceFormRegistry()
        )
        self.usage_registry = (
            usage_registry
            if usage_registry is not None
            else HerbSpiceUsageRegistry()
        )

    def parse(
        self,
        text: str,
    ) -> HerbSpiceParseResult:
        """일반 상품 텍스트를 파싱한다."""
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
    ) -> HerbSpiceParseResult:
        """구조화된 상품 Mapping을 파싱한다."""
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

        classification_hint = (
            self._classification_hint(product)
        )

        herb_match = self._match_ingredient_registry(
            product=product,
            specific_fields=self._HERB_FIELDS,
            registry=self.herb_registry,
            fallback_text=normalized_text,
            classification_hint=classification_hint,
            expected_classification="herb",
        )

        spice_match = self._match_ingredient_registry(
            product=product,
            specific_fields=self._SPICE_FIELDS,
            registry=self.spice_registry,
            fallback_text=normalized_text,
            classification_hint=classification_hint,
            expected_classification="spice",
        )

        return self._build_result(
            original_text=original_text,
            normalized_text=normalized_text,
            herb_match=herb_match,
            spice_match=spice_match,
            origin_match=self._match_structured_first(
                product=product,
                field_names=self._ORIGIN_FIELDS,
                registry=self.origin_registry,
                fallback_text=normalized_text,
            ),
            form_match=self._match_structured_first(
                product=product,
                field_names=self._FORM_FIELDS,
                registry=self.form_registry,
                fallback_text=normalized_text,
            ),
            usage_match=self._match_structured_first(
                product=product,
                field_names=self._USAGE_FIELDS,
                registry=self.usage_registry,
                fallback_text=normalized_text,
            ),
            metadata={
                "source_type": "mapping",
                "source_fields": self._matched_source_fields(
                    product
                ),
                "structured_field_priority": True,
                "classification_hint": classification_hint,
            },
        )

    def _parse_text(
        self,
        *,
        original_text: str,
        normalized_text: str,
    ) -> HerbSpiceParseResult:
        return self._build_result(
            original_text=original_text,
            normalized_text=normalized_text,
            herb_match=self.herb_registry.match(
                normalized_text
            ),
            spice_match=self.spice_registry.match(
                normalized_text
            ),
            origin_match=self.origin_registry.match(
                normalized_text
            ),
            form_match=self.form_registry.match(
                normalized_text
            ),
            usage_match=self.usage_registry.match(
                normalized_text
            ),
            metadata={
                "source_type": "text",
                "source_fields": [],
                "structured_field_priority": False,
                "classification_hint": None,
            },
        )

    def _build_result(
        self,
        *,
        original_text: str,
        normalized_text: str,
        herb_match: HerbMatch | None,
        spice_match: SpiceMatch | None,
        origin_match: HerbSpiceOriginMatch | None,
        form_match: HerbSpiceFormMatch | None,
        usage_match: HerbSpiceUsageMatch | None,
        metadata: Mapping[str, Any],
    ) -> HerbSpiceParseResult:
        (
            classification,
            ingredient_match,
        ) = self._select_ingredient_match(
            herb_match=herb_match,
            spice_match=spice_match,
        )

        matches = (
            ingredient_match,
            origin_match,
            form_match,
            usage_match,
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

        ingredient = self._canonical_name(
            ingredient_match
        )
        ingredient_confidence = (
            self._match_confidence(
                ingredient_match
            )
        )

        result_metadata = dict(metadata)
        result_metadata.update(
            {
                "category_id": "herb_spice",
                "matched_field_count": (
                    matched_field_count
                ),
                "expected_field_count": 4,
                "is_complete": (
                    matched_field_count == 4
                ),
                "ingredient_conflict": (
                    herb_match is not None
                    and spice_match is not None
                ),
            }
        )

        return HerbSpiceParseResult(
            original_text=original_text,
            normalized_text=normalized_text,
            confidence=confidence,
            metadata=result_metadata,
            classification=classification,
            ingredient=ingredient,
            origin=self._canonical_name(
                origin_match
            ),
            form=self._canonical_name(
                form_match
            ),
            usage=self._canonical_name(
                usage_match
            ),
            classification_confidence=(
                ingredient_confidence
            ),
            ingredient_confidence=(
                ingredient_confidence
            ),
            origin_confidence=(
                self._match_confidence(
                    origin_match
                )
            ),
            form_confidence=(
                self._match_confidence(
                    form_match
                )
            ),
            usage_confidence=(
                self._match_confidence(
                    usage_match
                )
            ),
            herb_match=herb_match,
            spice_match=spice_match,
            origin_match=origin_match,
            form_match=form_match,
            usage_match=usage_match,
            detected_keywords=(
                self._detected_keywords(
                    (
                        herb_match,
                        spice_match,
                        origin_match,
                        form_match,
                        usage_match,
                    )
                )
            ),
            warnings=self._build_warnings(
                classification=classification,
                ingredient=ingredient,
                herb_match=herb_match,
                spice_match=spice_match,
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

    def _match_ingredient_registry(
        self,
        *,
        product: Mapping[str, Any],
        specific_fields: Sequence[str],
        registry: Any,
        fallback_text: str,
        classification_hint: str | None,
        expected_classification: str,
    ) -> Any:
        values: list[str] = []

        for field_name in (
            *specific_fields,
            *self._INGREDIENT_FIELDS,
        ):
            value = self._stringify_value(
                product.get(field_name)
            )

            if value:
                values.append(value)

        if values:
            structured_text = " ".join(
                self._deduplicate_texts(
                    values
                )
            )

            match = registry.match(
                structured_text
            )

            if match is not None:
                return match

        if (
            classification_hint is not None
            and classification_hint
            != expected_classification
        ):
            return None

        return registry.match(
            fallback_text
        )

    def _match_structured_first(
        self,
        *,
        product: Mapping[str, Any],
        field_names: Sequence[str],
        registry: Any,
        fallback_text: str,
    ) -> Any:
        values = [
            self._stringify_value(
                product.get(field_name)
            )
            for field_name in field_names
        ]

        values = [
            value
            for value in values
            if value
        ]

        if values:
            structured_text = " ".join(
                self._deduplicate_texts(
                    values
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
    def _select_ingredient_match(
        *,
        herb_match: HerbMatch | None,
        spice_match: SpiceMatch | None,
    ) -> tuple[
        str | None,
        HerbMatch | SpiceMatch | None,
    ]:
        if (
            herb_match is None
            and spice_match is None
        ):
            return None, None

        if herb_match is not None and spice_match is None:
            return "herb", herb_match

        if spice_match is not None and herb_match is None:
            return "spice", spice_match

        assert herb_match is not None
        assert spice_match is not None

        herb_rank = (
            bool(herb_match.exact_match),
            len(str(herb_match.matched_alias)),
            float(herb_match.confidence),
            1,
        )
        spice_rank = (
            bool(spice_match.exact_match),
            len(str(spice_match.matched_alias)),
            float(spice_match.confidence),
            0,
        )

        if herb_rank >= spice_rank:
            return "herb", herb_match

        return "spice", spice_match

    @classmethod
    def _classification_hint(
        cls,
        product: Mapping[str, Any],
    ) -> str | None:
        for field_name in cls._CLASSIFICATION_FIELDS:
            value = cls._stringify_value(
                product.get(field_name)
            )

            if not value:
                continue

            normalized = value.strip().casefold()

            if normalized in {
                "herb",
                "허브",
            }:
                return "herb"

            if normalized in {
                "spice",
                "향신료",
            }:
                return "spice"

        return None

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

            if not keyword or key in seen:
                continue

            seen.add(key)
            result.append(keyword)

        return result

    @staticmethod
    def _build_warnings(
        *,
        classification: str | None,
        ingredient: str | None,
        herb_match: HerbMatch | None,
        spice_match: SpiceMatch | None,
        matched_field_count: int,
    ) -> list[str]:
        warnings: list[str] = []

        if matched_field_count == 0:
            warnings.append(
                "Herb & Spice Registry에서 일치하는 "
                "속성을 찾지 못했습니다."
            )
            return warnings

        if (
            herb_match is not None
            and spice_match is not None
        ):
            warnings.append(
                "Herb와 Spice 성분이 동시에 탐지되어 "
                "Registry evidence 우선순위로 "
                "대표 성분을 선택했습니다."
            )

        if ingredient is None:
            warnings.append(
                "Herb 또는 Spice 성분이 "
                "명확하게 확인되지 않았습니다."
            )

        if classification is None:
            warnings.append(
                "Herb/Spice 분류가 "
                "확인되지 않았습니다."
            )

        if matched_field_count < 4:
            warnings.append(
                "일부 Herb & Spice 속성이 "
                "확인되지 않았습니다."
            )

        return warnings

    @staticmethod
    def _stringify_value(
        value: Any,
    ) -> str:
        """
        구조화 필드 값을 Parser 검색용 문자열로 변환한다.

        Mapping은 직접 문자열화하지 않으며,
        Sequence 값은 요소를 공백으로 결합한다.
        """
        if value is None:
            return ""

        if isinstance(value, str):
            return value.strip()

        if isinstance(value, Mapping):
            return ""

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
                str(item).strip()
                for item in value
                if str(item).strip()
            ]

            return " ".join(values)

        return str(value).strip()

    @staticmethod
    def _deduplicate_texts(
        values: Sequence[str],
    ) -> list[str]:
        """입력 순서를 유지하며 중복 텍스트를 제거한다."""
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
        """실제 Parser 입력에 사용된 구조화 필드명을 반환한다."""
        result: list[str] = []

        for field_name in cls._all_text_fields():
            value = cls._stringify_value(
                product.get(field_name)
            )

            if value:
                result.append(field_name)

        return result

    @classmethod
    def _all_text_fields(
        cls,
    ) -> tuple[str, ...]:
        result: list[str] = []
        seen: set[str] = set()

        for field_name in (
            *cls._NAME_FIELDS,
            *cls._INGREDIENT_FIELDS,
            *cls._HERB_FIELDS,
            *cls._SPICE_FIELDS,
            *cls._CLASSIFICATION_FIELDS,
            *cls._ORIGIN_FIELDS,
            *cls._FORM_FIELDS,
            *cls._USAGE_FIELDS,
            *cls._OPTION_FIELDS,
        ):
            if field_name in seen:
                continue

            seen.add(field_name)
            result.append(field_name)

        return tuple(result)


__all__ = [
    "HerbSpiceParser",
]
