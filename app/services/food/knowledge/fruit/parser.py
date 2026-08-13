from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.common import (
    calculate_field_confidence,
    detect_keywords,
    extract_product_name as extract_common_product_name,
    extract_weight_grams as extract_common_weight_grams,
    first_non_empty,
    normalize_text,
    safe_float,
)
from app.services.food.knowledge.fruit.parser_models import (
    FruitParseResult,
)
from app.services.food.knowledge.fruit.registries import (
    FRUIT_KEYWORDS,
)
from app.services.food.knowledge.fruit.rules import (
    BRIX_PATTERNS,
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

_BRIX_KEYS = (
    "brix",
    "sugar_content",
    "sweetness_brix",
)

class FruitParser:
    """
    Fruit 도메인의 canonical parser.

    책임:
    - 상품 입력에서 Fruit 속성 추출
    - 값 정규화
    - Parse confidence 계산
    - FruitParseResult 생성

    점수 계산, Rule 평가, Provider orchestration은 수행하지 않는다.
    """

    def parse(
        self,
        product: Mapping[str, Any],
    ) -> FruitParseResult:
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

        brix = extract_brix(product)

        weight_grams = extract_weight_grams(
            product
        )

        detected_keywords = (
            detect_fruit_keywords(
                product_name
            )
        )

        confidence = (
            calculate_parse_confidence(
                product_name=product_name,
                origin=origin,
                grade=grade,
                brix=brix,
                weight=weight,
            )
        )

        return FruitParseResult(
            original_text=product_name,
            normalized_text=normalize_text(
                product_name
            ),
            confidence=confidence,
            origin=origin,
            variety=variety,
            grade=grade,
            brix=brix,
            weight_grams=weight_grams,
            detected_keywords=(
                detected_keywords
            ),
        )


_DEFAULT_FRUIT_PARSER = FruitParser()


def parse_fruit(
    product: Mapping[str, Any],
) -> FruitParseResult:
    """
    FruitParseResult를 반환하는 canonical 함수 API.
    """
    return _DEFAULT_FRUIT_PARSER.parse(
        product
    )


def parse_fruit_product(
    product: Mapping[str, Any],
) -> dict[str, Any]:
    """
    기존 Fruit 공개 API와의 하위 호환 adapter.

    기존 호출자가 기대하는 dict 구조를 그대로 반환한다.
    신규 코드는 parse_fruit() 또는 FruitParser.parse() 사용을 권장한다.
    """

    parsed = parse_fruit(product)

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
        "brix": parsed.brix,
        "weight": weight,
        "weight_grams": (
            parsed.weight_grams
        ),
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


def extract_brix(
    product: Mapping[str, Any],
) -> float | None:
    """
    brix 필드 또는 상품명에서 당도 값을 추출한다.

    지원 예:
    - 13
    - "13"
    - "13브릭스"
    - "13 Brix"
    - "당도 13.5"
    """

    direct_value = first_non_empty(
        product,
        _BRIX_KEYS,
    )

    parsed_direct_value = safe_float(
        direct_value,
        default=None,
    )

    if parsed_direct_value is not None:
        return parsed_direct_value

    product_name = extract_product_name(
        product
    )

    for pattern in BRIX_PATTERNS:
        matched = re.search(
            pattern,
            product_name,
            flags=re.IGNORECASE,
        )

        if not matched:
            continue

        return safe_float(
            matched.group("value"),
            default=None,
        )

    return None


def extract_weight_grams(
    value: Mapping[str, Any] | Any,
) -> float | None:
    """
    기존 Fruit API와의 호환성을 유지한다.

    Mapping 입력:
        상품의 무게 필드 또는 상품명에서 추출

    문자열 입력:
        문자열 자체에서 kg/g 단위를 추출
    """

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


def detect_fruit_keywords(
    product_name: str,
) -> list[str]:
    return detect_keywords(
        product_name,
        FRUIT_KEYWORDS,
        case_sensitive=False,
    )


def calculate_parse_confidence(
    *,
    product_name: str,
    origin: Any,
    grade: Any,
    brix: float | None,
    weight: Any,
) -> float:
    return calculate_field_confidence(
        {
            "product_name": product_name,
            "origin": origin,
            "grade": grade,
            "brix": brix,
            "weight": weight,
        },
        weights={
            "product_name": 0.30,
            "origin": 0.20,
            "grade": 0.15,
            "brix": 0.20,
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
    "FruitParser",
    "parse_fruit",
    "parse_fruit_product",
    "extract_product_name",
    "extract_brix",
    "extract_weight_grams",
    "detect_fruit_keywords",
    "calculate_parse_confidence",
]
