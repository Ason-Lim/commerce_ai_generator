from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any, TypeVar

from app.services.food.knowledge.common.base_model import (
    RegistryMatch,
)
from app.services.food.knowledge.common.parser_base import (
    BaseKnowledgeParser,
)
from app.services.food.knowledge.wine.acidity_registry import (
    WineAcidityMatch,
    WineAcidityRegistry,
)
from app.services.food.knowledge.wine.body_registry import (
    WineBodyMatch,
    WineBodyRegistry,
)
from app.services.food.knowledge.wine.grape_registry import (
    WineGrapeMatch,
    WineGrapeRegistry,
)
from app.services.food.knowledge.wine.parser_models import (
    WineParseResult,
)
from app.services.food.knowledge.wine.region_registry import (
    WineRegionMatch,
    WineRegionRegistry,
)
from app.services.food.knowledge.wine.sweetness_registry import (
    WineSweetnessMatch,
    WineSweetnessRegistry,
)
from app.services.food.knowledge.wine.type_registry import (
    WineTypeMatch,
    WineTypeRegistry,
)


MatchT = TypeVar(
    "MatchT",
    bound=RegistryMatch[Any],
)


_VINTAGE_PATTERN = re.compile(
    r"(?<!\d)(18\d{2}|19\d{2}|20\d{2}|2100)(?!\d)"
)

_ALCOHOL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"(?<!\d)(\d{1,2}(?:\.\d+)?)\s*(?:%|도)(?!\w)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\babv\s*[:=]?\s*(\d{1,2}(?:\.\d+)?)\s*%?",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?<!\d)(\d{1,2}(?:\.\d+)?)\s*\babv\b",
        re.IGNORECASE,
    ),
)


class WineParser(
    BaseKnowledgeParser[WineParseResult]
):
    """
    Wine 상품 Parser.

    책임:
    - 상품 텍스트 구성 및 정규화
    - Wine Registry 검색
    - 구조화 필드 우선 적용
    - 빈티지 및 알코올 도수 추출
    - confidence와 warning 계산
    - WineParseResult 생성

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
        "wine_type",
        "type",
        "style",
        "wine_style",
        "color",
    )

    _GRAPE_FIELDS: tuple[str, ...] = (
        "grape",
        "grape_variety",
        "variety",
        "varietal",
    )

    _REGION_FIELDS: tuple[str, ...] = (
        "region",
        "wine_region",
        "origin_region",
        "appellation",
        "origin",
        "country",
    )

    _SWEETNESS_FIELDS: tuple[str, ...] = (
        "sweetness",
        "sweetness_type",
        "sugar_level",
    )

    _BODY_FIELDS: tuple[str, ...] = (
        "body",
        "body_type",
        "body_level",
    )

    _ACIDITY_FIELDS: tuple[str, ...] = (
        "acidity",
        "acidity_type",
        "acidity_level",
    )

    _VINTAGE_FIELDS: tuple[str, ...] = (
        "vintage",
        "vintage_year",
        "year",
    )

    _ALCOHOL_FIELDS: tuple[str, ...] = (
        "alcohol_percent",
        "alcohol",
        "abv",
        "alcohol_content",
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
        type_registry: WineTypeRegistry | None = None,
        grape_registry: WineGrapeRegistry | None = None,
        region_registry: WineRegionRegistry | None = None,
        sweetness_registry: WineSweetnessRegistry | None = None,
        body_registry: WineBodyRegistry | None = None,
        acidity_registry: WineAcidityRegistry | None = None,
    ) -> None:
        self.type_registry = (
            type_registry
            if type_registry is not None
            else WineTypeRegistry()
        )
        self.grape_registry = (
            grape_registry
            if grape_registry is not None
            else WineGrapeRegistry()
        )
        self.region_registry = (
            region_registry
            if region_registry is not None
            else WineRegionRegistry()
        )
        self.sweetness_registry = (
            sweetness_registry
            if sweetness_registry is not None
            else WineSweetnessRegistry()
        )
        self.body_registry = (
            body_registry
            if body_registry is not None
            else WineBodyRegistry()
        )
        self.acidity_registry = (
            acidity_registry
            if acidity_registry is not None
            else WineAcidityRegistry()
        )

    def parse(
        self,
        text: str,
    ) -> WineParseResult:
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
    ) -> WineParseResult:
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

        type_match = self._match_structured_first(
            product=product,
            field_names=self._TYPE_FIELDS,
            registry=self.type_registry,
            fallback_text=normalized_text,
        )
        grape_match = self._match_structured_first(
            product=product,
            field_names=self._GRAPE_FIELDS,
            registry=self.grape_registry,
            fallback_text=normalized_text,
        )
        region_match = self._match_structured_first(
            product=product,
            field_names=self._REGION_FIELDS,
            registry=self.region_registry,
            fallback_text=normalized_text,
        )
        sweetness_match = self._match_structured_first(
            product=product,
            field_names=self._SWEETNESS_FIELDS,
            registry=self.sweetness_registry,
            fallback_text=normalized_text,
        )
        body_match = self._match_structured_first(
            product=product,
            field_names=self._BODY_FIELDS,
            registry=self.body_registry,
            fallback_text=normalized_text,
        )
        acidity_match = self._match_structured_first(
            product=product,
            field_names=self._ACIDITY_FIELDS,
            registry=self.acidity_registry,
            fallback_text=normalized_text,
        )

        vintage = self._extract_structured_int(
            product,
            self._VINTAGE_FIELDS,
        )
        if vintage is None:
            vintage = self._extract_vintage(
                normalized_text
            )

        alcohol_percent = self._extract_structured_float(
            product,
            self._ALCOHOL_FIELDS,
        )
        if alcohol_percent is None:
            alcohol_percent = self._extract_alcohol_percent(
                normalized_text
            )

        return self._build_result(
            original_text=original_text,
            normalized_text=normalized_text,
            type_match=type_match,
            grape_match=grape_match,
            region_match=region_match,
            sweetness_match=sweetness_match,
            body_match=body_match,
            acidity_match=acidity_match,
            vintage=vintage,
            alcohol_percent=alcohol_percent,
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
    ) -> WineParseResult:
        return self._build_result(
            original_text=original_text,
            normalized_text=normalized_text,
            type_match=self.type_registry.match(
                normalized_text
            ),
            grape_match=self.grape_registry.match(
                normalized_text
            ),
            region_match=self.region_registry.match(
                normalized_text
            ),
            sweetness_match=(
                self.sweetness_registry.match(
                    normalized_text
                )
            ),
            body_match=self.body_registry.match(
                normalized_text
            ),
            acidity_match=self.acidity_registry.match(
                normalized_text
            ),
            vintage=self._extract_vintage(
                normalized_text
            ),
            alcohol_percent=(
                self._extract_alcohol_percent(
                    normalized_text
                )
            ),
            metadata={
                "source_type": "text",
                "structured_field_priority": False,
            },
        )

    def _build_result(
        self,
        *,
        original_text: str,
        normalized_text: str,
        type_match: WineTypeMatch | None,
        grape_match: WineGrapeMatch | None,
        region_match: WineRegionMatch | None,
        sweetness_match: WineSweetnessMatch | None,
        body_match: WineBodyMatch | None,
        acidity_match: WineAcidityMatch | None,
        vintage: int | None,
        alcohol_percent: float | None,
        metadata: Mapping[str, Any],
    ) -> WineParseResult:
        matches: tuple[RegistryMatch[Any] | None, ...] = (
            type_match,
            grape_match,
            region_match,
            sweetness_match,
            body_match,
            acidity_match,
        )

        detected_keywords = [
            match.matched_alias
            for match in matches
            if match is not None
        ]

        if vintage is not None:
            detected_keywords.append(
                str(vintage)
            )

        if alcohol_percent is not None:
            detected_keywords.append(
                f"{alcohol_percent:g}%"
            )

        warnings: list[str] = []

        if not any(
            match is not None
            for match in matches
        ):
            warnings.append(
                "Wine Registry에서 일치하는 "
                "속성을 찾지 못했습니다."
            )

        confidence = self._calculate_confidence(
            matches
        )

        return WineParseResult(
            original_text=original_text,
            normalized_text=normalized_text,
            confidence=confidence,
            metadata=dict(metadata),
            wine_type=self._registry_key(
                type_match
            ),
            grape=self._registry_key(
                grape_match
            ),
            region=self._registry_key(
                region_match
            ),
            sweetness=self._registry_key(
                sweetness_match
            ),
            body=self._registry_key(
                body_match
            ),
            acidity=self._registry_key(
                acidity_match
            ),
            vintage=vintage,
            alcohol_percent=alcohol_percent,
            wine_type_confidence=self._match_confidence(
                type_match
            ),
            grape_confidence=self._match_confidence(
                grape_match
            ),
            region_confidence=self._match_confidence(
                region_match
            ),
            sweetness_confidence=self._match_confidence(
                sweetness_match
            ),
            body_confidence=self._match_confidence(
                body_match
            ),
            acidity_confidence=self._match_confidence(
                acidity_match
            ),
            wine_type_match=type_match,
            grape_match=grape_match,
            region_match=region_match,
            sweetness_match=sweetness_match,
            body_match=body_match,
            acidity_match=acidity_match,
            detected_keywords=detected_keywords,
            warnings=warnings,
        )

    def _build_product_text(
        self,
        product: Mapping[str, Any],
    ) -> str:
        values: list[str] = []

        for field_name in (
            *self._NAME_FIELDS,
            *self._OPTION_FIELDS,
            *self._TYPE_FIELDS,
            *self._GRAPE_FIELDS,
            *self._REGION_FIELDS,
            *self._SWEETNESS_FIELDS,
            *self._BODY_FIELDS,
            *self._ACIDITY_FIELDS,
            *self._VINTAGE_FIELDS,
            *self._ALCOHOL_FIELDS,
        ):
            raw_value = product.get(
                field_name
            )

            if raw_value is None:
                continue

            if isinstance(
                raw_value,
                (list, tuple, set, frozenset),
            ):
                values.extend(
                    str(value).strip()
                    for value in raw_value
                    if str(value).strip()
                )
                continue

            text = str(raw_value).strip()

            if text:
                values.append(text)

        result: list[str] = []
        seen: set[str] = set()

        for value in values:
            key = value.casefold()

            if key in seen:
                continue

            seen.add(key)
            result.append(value)

        return " ".join(result).strip()

    def _match_structured_first(
        self,
        *,
        product: Mapping[str, Any],
        field_names: Sequence[str],
        registry: Any,
        fallback_text: str,
    ) -> Any:
        for field_name in field_names:
            raw_value = product.get(
                field_name
            )

            if raw_value is None:
                continue

            values = (
                raw_value
                if isinstance(
                    raw_value,
                    (list, tuple, set, frozenset),
                )
                else (raw_value,)
            )

            for value in values:
                text = str(value).strip()

                if not text:
                    continue

                match = registry.match(text)

                if match is not None:
                    return match

        return registry.match(
            fallback_text
        )

    def _matched_source_fields(
        self,
        product: Mapping[str, Any],
    ) -> list[str]:
        field_names = (
            *self._NAME_FIELDS,
            *self._TYPE_FIELDS,
            *self._GRAPE_FIELDS,
            *self._REGION_FIELDS,
            *self._SWEETNESS_FIELDS,
            *self._BODY_FIELDS,
            *self._ACIDITY_FIELDS,
            *self._VINTAGE_FIELDS,
            *self._ALCOHOL_FIELDS,
            *self._OPTION_FIELDS,
        )

        return [
            field_name
            for field_name in field_names
            if (
                field_name in product
                and product[field_name] is not None
                and str(product[field_name]).strip()
            )
        ]

    @staticmethod
    def _registry_key(
        match: RegistryMatch[Any] | None,
    ) -> str | None:
        if match is None:
            return None

        return match.entry.registry_key

    @staticmethod
    def _match_confidence(
        match: RegistryMatch[Any] | None,
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

    def _calculate_confidence(
        self,
        matches: Sequence[
            RegistryMatch[Any] | None
        ],
    ) -> float:
        values = [
            self._match_confidence(match)
            for match in matches
            if match is not None
        ]

        if not values:
            return 0.0

        return round(
            sum(values) / len(values),
            4,
        )

    @staticmethod
    def _extract_vintage(
        text: str,
    ) -> int | None:
        match = _VINTAGE_PATTERN.search(
            text
        )

        if match is None:
            return None

        return int(match.group(1))

    @staticmethod
    def _extract_alcohol_percent(
        text: str,
    ) -> float | None:
        for pattern in _ALCOHOL_PATTERNS:
            match = pattern.search(text)

            if match is None:
                continue

            value = float(match.group(1))

            if 0.0 <= value <= 100.0:
                return value

        return None

    @staticmethod
    def _extract_structured_int(
        product: Mapping[str, Any],
        field_names: Sequence[str],
    ) -> int | None:
        for field_name in field_names:
            if field_name not in product:
                continue

            raw_value = product[field_name]

            if raw_value is None:
                continue

            match = re.search(
                r"\d{4}",
                str(raw_value),
            )

            if match is None:
                continue

            return int(match.group(0))

        return None

    @staticmethod
    def _extract_structured_float(
        product: Mapping[str, Any],
        field_names: Sequence[str],
    ) -> float | None:
        for field_name in field_names:
            if field_name not in product:
                continue

            raw_value = product[field_name]

            if raw_value is None:
                continue

            match = re.search(
                r"\d{1,3}(?:\.\d+)?",
                str(raw_value),
            )

            if match is None:
                continue

            return float(match.group(0))

        return None


__all__ = [
    "WineParser",
]
