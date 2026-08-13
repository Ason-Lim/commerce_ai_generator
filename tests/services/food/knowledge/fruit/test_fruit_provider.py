from __future__ import annotations

from app.services.food.knowledge.fruit.provider import (
    FruitKnowledgeProvider,
)
from app.services.food.knowledge.models import (
    FoodKnowledgeResult,
)


def test_fruit_provider_supports_category() -> None:
    provider = FruitKnowledgeProvider()

    assert provider.supports(
        category_id="fruit"
    )
    assert provider.supports(
        product_name="고당도 사과"
    )


def test_fruit_provider_analyze_returns_result() -> None:
    provider = FruitKnowledgeProvider()

    result = provider.analyze(
        {
            "product_name": (
                "고당도 제주 감귤 12브릭스 2kg"
            ),
            "origin": "제주",
            "variety": "감귤",
            "grade": "특품",
            "weight": "2kg",
        }
    )

    assert isinstance(
        result,
        FoodKnowledgeResult,
    )

    assert result.category_id == "fruit"
    assert result.category_name == "과일"

    assert result.product_name == (
        "고당도 제주 감귤 12브릭스 2kg"
    )

    assert result.attributes[
        "origin"
    ] == "제주"

    assert result.attributes[
        "variety"
    ] == "감귤"

    assert result.attributes[
        "brix"
    ] == 12.0

    assert result.attributes[
        "weight_grams"
    ] == 2000.0

    assert result.confidence > 0.0


def test_fruit_provider_uses_attribute_layer() -> None:
    provider = FruitKnowledgeProvider()

    result = provider.analyze(
        {
            "product_name": "사과 1kg",
            "weight": "1kg",
        }
    )

    assert (
        result.attributes[
            "product_name"
        ]
        == "사과 1kg"
    )

    assert result.attributes[
        "weight"
    ] == "1kg"

    assert result.attributes[
        "weight_grams"
    ] == 1000.0


def test_fruit_provider_preserves_raw_product() -> None:
    provider = FruitKnowledgeProvider()

    product = {
        "product_name": "사과",
        "origin": "대한민국",
    }

    result = provider.analyze(product)

    assert result.raw_product == product


def test_fruit_provider_metadata_version() -> None:
    provider = FruitKnowledgeProvider()

    result = provider.analyze(
        {
            "product_name": "사과",
        }
    )

    assert result.metadata[
        "provider"
    ] == "FruitKnowledgeProvider"

    assert result.metadata[
        "provider_version"
    ] == "2.2"
