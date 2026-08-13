from __future__ import annotations

import pytest

from app.services.food.knowledge.fruit.attributes import (
    build_fruit_attributes,
    extract_fruit_product_name,
)
from app.services.food.knowledge.fruit.parser_models import (
    FruitParseResult,
)


def test_extract_fruit_product_name() -> None:
    assert extract_fruit_product_name(
        {
            "product_name": "제주 감귤",
        }
    ) == "제주 감귤"


def test_build_fruit_attributes() -> None:
    product = {
        "product_name": (
            "고당도 제주 감귤 12브릭스 2kg"
        ),
        "weight": "2kg",
    }

    parsed = FruitParseResult(
        original_text=product[
            "product_name"
        ],
        normalized_text=product[
            "product_name"
        ],
        confidence=0.9,
        origin="제주",
        variety="감귤",
        grade="특품",
        brix=12.0,
        weight_grams=2000.0,
        detected_keywords=[
            "고당도",
        ],
    )

    attributes = build_fruit_attributes(
        product=product,
        parse_result=parsed,
    )

    assert attributes[
        "product_name"
    ] == product["product_name"]
    assert attributes["origin"] == "제주"
    assert attributes["variety"] == "감귤"
    assert attributes["grade"] == "특품"
    assert attributes["brix"] == 12.0
    assert attributes[
        "weight_grams"
    ] == 2000.0
    assert attributes["weight"] == "2kg"
    assert attributes[
        "confidence"
    ] == 0.9
    assert attributes[
        "detected_keywords"
    ] == ["고당도"]
    assert attributes[
        "is_complete"
    ] is True


def test_attributes_reject_invalid_product() -> None:
    parsed = FruitParseResult(
        original_text="사과",
        normalized_text="사과",
    )

    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        build_fruit_attributes(
            product=[],  # type: ignore[arg-type]
            parse_result=parsed,
        )


def test_attributes_reject_invalid_parse_result() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "parse_result must be "
            "FruitParseResult"
        ),
    ):
        build_fruit_attributes(
            product={
                "product_name": "사과",
            },
            parse_result=object(),  # type: ignore[arg-type]
        )
