from __future__ import annotations

import pytest

from app.services.food.knowledge.fruit.parser import (
    FruitParser,
    extract_brix,
    extract_weight_grams,
    parse_fruit,
    parse_fruit_product,
)
from app.services.food.knowledge.fruit.parser_models import (
    FruitParseResult,
)


def test_fruit_parser_returns_typed_result() -> None:
    product = {
        "product_name": (
            "고당도 제주 감귤 12브릭스 2kg"
        ),
        "origin": "제주",
        "variety": "감귤",
        "grade": "특품",
        "weight": "2kg",
    }

    result = FruitParser().parse(
        product
    )

    assert isinstance(
        result,
        FruitParseResult,
    )

    assert result.original_text == (
        product["product_name"]
    )
    assert result.origin == "제주"
    assert result.variety == "감귤"
    assert result.grade == "특품"
    assert result.brix == 12.0
    assert result.weight_grams == 2000.0
    assert "고당도" in (
        result.detected_keywords
    )
    assert 0.0 <= result.confidence <= 1.0


def test_parse_fruit_function_returns_typed_result() -> None:
    result = parse_fruit(
        {
            "product_name": "사과",
            "variety": "부사",
        }
    )

    assert isinstance(
        result,
        FruitParseResult,
    )
    assert result.variety == "부사"


def test_legacy_parse_fruit_product_returns_dict() -> None:
    product = {
        "product_name": (
            "고당도 제주 감귤 12브릭스 2kg"
        ),
        "origin": "제주",
        "variety": "감귤",
        "grade": "특품",
        "weight": "2kg",
    }

    result = parse_fruit_product(
        product
    )

    assert isinstance(result, dict)

    assert result == {
        "product_name": (
            "고당도 제주 감귤 12브릭스 2kg"
        ),
        "origin": "제주",
        "variety": "감귤",
        "grade": "특품",
        "brix": 12.0,
        "weight": "2kg",
        "weight_grams": 2000.0,
        "detected_keywords": [
            "고당도",
        ],
        "confidence": 1.0,
    }


def test_structured_brix_has_priority() -> None:
    result = extract_brix(
        {
            "product_name": (
                "사과 14브릭스"
            ),
            "brix": 12.5,
        }
    )

    assert result == 12.5


@pytest.mark.parametrize(
    ("product_name", "expected"),
    [
        ("감귤 13브릭스", 13.0),
        ("사과 13 Brix", 13.0),
        ("배 당도 13.5", 13.5),
        ("일반 사과", None),
    ],
)
def test_extract_brix_from_product_name(
    product_name: str,
    expected: float | None,
) -> None:
    result = extract_brix(
        {
            "product_name": (
                product_name
            ),
        }
    )

    assert result == expected


def test_extract_weight_grams_from_mapping() -> None:
    result = extract_weight_grams(
        {
            "product_name": "사과 2kg",
        }
    )

    assert result == 2000.0


def test_extract_weight_grams_legacy_string_api() -> None:
    assert extract_weight_grams(
        "1.5kg"
    ) == 1500.0


def test_parser_rejects_non_mapping() -> None:
    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        FruitParser().parse(
            []  # type: ignore[arg-type]
        )


def test_fruit_keyword_registry_is_used() -> None:
    result = parse_fruit(
        {
            "product_name": (
                "산지직송 유기농 사과"
            ),
        }
    )

    assert "산지직송" in (
        result.detected_keywords
    )
    assert "유기농" in (
        result.detected_keywords
    )


def test_brix_rule_patterns_preserve_parsing() -> None:
    result = parse_fruit(
        {
            "product_name": (
                "프리미엄 배 당도 13.5"
            ),
        }
    )

    assert result.brix == 13.5
