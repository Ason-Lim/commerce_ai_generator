from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.common import (
    calculate_field_confidence,
    detect_keywords,
    extract_product_name as extract_common_product_name,
    extract_weight_grams as extract_common_weight_grams,
    first_non_empty,
    normalize_text,
)
from app.services.food.knowledge.vegetable.parser_models import (
    VegetableParseResult,
)
from app.services.food.knowledge.vegetable.registries import (
    VEGETABLE_KEYWORDS,
)


_ORIGIN_KEYS = (
    "origin",
    "country_of_origin",
    "origin_name",
    "production_area",
    "region",
)

_VARIETY_KEYS = (
    "variety",
    "cultivar",
    "species",
    "vegetable_type",
)

_GRADE_KEYS = (
    "grade",
    "product_grade",
    "quality_grade",
)

_WEIGHT_KEYS = (
    "weight",
    "quantity",
    "package_weight",
    "net_weight",
)


class VegetableParser:
    """
    Vegetable 도메인의 canonical parser.

    책임:
    - 상품 입력에서 Vegetable 속성 추출
    - 값 정규화
    - Parse confidence 계산
    - VegetableParseResult 생성

    담당하지 않는 책임:
    - Attribute 구성
    - 점수 계산
    - Rule 평가
    - Provider orchestration
    - Registry 데이터 수정
    """

    def parse(
        self,
        product: Mapping[str, Any],
    ) -> VegetableParseResult:
        if not isinstance(product, Mapping):
            raise TypeError(
                "product must be a Mapping"
            )

        product_name = extract_product_name(
            product
        )

        origin = _normalize_optional_text(
            first_non_empty(
                product,
                _ORIGIN_KEYS,
            )
        )

        variety = _normalize_optional_text(
            first_non_empty(
                product,
                _VARIETY_KEYS,
            )
        )

        grade = _normalize_optional_text(
            first_non_empty(
                product,
                _GRADE_KEYS,
            )
        )

        weight = _normalize_optional_text(
            first_non_empty(
                product,
                _WEIGHT_KEYS,
            )
        )

        weight_grams = extract_weight_grams(
            product
        )

        detected_keywords = (
            detect_vegetable_keywords(
                product_name
            )
        )

        confidence = (
            calculate_parse_confidence(
                product_name=product_name,
                origin=origin,
                variety=variety,
                grade=grade,
                weight=weight,
            )
        )

        return VegetableParseResult(
            original_text=product_name,
            normalized_text=normalize_text(
                product_name
            ),
            confidence=confidence,
            origin=origin,
            variety=variety,
            grade=grade,
            weight_grams=weight_grams,
            detected_keywords=(
                detected_keywords
            ),
        )


_DEFAULT_VEGETABLE_PARSER = VegetableParser()


def parse_vegetable(
    product: Mapping[str, Any],
) -> VegetableParseResult:
    """
    VegetableParseResult를 반환하는 canonical 함수 API.
    """
    return _DEFAULT_VEGETABLE_PARSER.parse(
        product
    )


def parse_vegetable_product(
    product: Mapping[str, Any],
) -> dict[str, Any]:
    """
    dict 기반 호출자를 위한 compatibility adapter.
    """
    parsed = parse_vegetable(product)

    weight = _normalize_optional_text(
        first_non_empty(
            product,
            _WEIGHT_KEYS,
        )
    )

    return {
        "product_name": parsed.original_text,
        "origin": parsed.origin,
        "variety": parsed.variety,
        "grade": parsed.grade,
        "weight": weight,
        "weight_grams": parsed.weight_grams,
        "detected_keywords": list(
            parsed.detected_keywords
        ),
        "confidence": parsed.confidence,
    }


def extract_product_name(
    product: Mapping[str, Any],
) -> str:
    return extract_common_product_name(
        product
    )


def extract_weight_grams(
    value: Mapping[str, Any] | Any,
) -> float | None:
    if isinstance(value, Mapping):
        return extract_common_weight_grams(
            value,
            fallback_to_product_name=True,
        )

    temporary_product = {
        "weight": value,
    }

    return extract_common_weight_grams(
        temporary_product,
        fallback_to_product_name=False,
    )


def detect_vegetable_keywords(
    product_name: str,
) -> list[str]:
    return detect_keywords(
        product_name,
        VEGETABLE_KEYWORDS,
        case_sensitive=False,
    )


def calculate_parse_confidence(
    *,
    product_name: str,
    origin: Any,
    variety: Any,
    grade: Any,
    weight: Any,
) -> float:
    return calculate_field_confidence(
        {
            "product_name": product_name,
            "origin": origin,
            "variety": variety,
            "grade": grade,
            "weight": weight,
        },
        weights={
            "product_name": 0.30,
            "origin": 0.20,
            "variety": 0.20,
            "grade": 0.15,
            "weight": 0.15,
        },
    )


def _normalize_optional_text(
    value: Any,
) -> str | None:
    if value is None:
        return None

    normalized = normalize_text(
        str(value)
    )

    return normalized or None


__all__ = [
    "VegetableParser",
    "parse_vegetable",
    "parse_vegetable_product",
    "extract_product_name",
    "extract_weight_grams",
    "detect_vegetable_keywords",
    "calculate_parse_confidence",
]
