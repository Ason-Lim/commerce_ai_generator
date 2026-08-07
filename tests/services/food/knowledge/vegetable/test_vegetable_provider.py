from app.services.food.knowledge.models import (
    FoodKnowledgeResult,
)
from app.services.food.knowledge.vegetable.provider import (
    VegetableKnowledgeProvider,
)


def test_vegetable_provider_supports_category():
    provider = VegetableKnowledgeProvider()

    assert provider.supports(
        category_id="vegetable"
    )
    assert provider.supports(
        product_name="유기농 상추"
    )
    assert not provider.supports(
        product_name="에티오피아 커피"
    )


def test_vegetable_provider_analyze_returns_result():
    provider = VegetableKnowledgeProvider()

    result = provider.analyze(
        {
            "product_name": (
                "국산 유기농 상추 500g"
            ),
            "origin": "국산",
            "variety": "상추",
            "grade": "특",
            "weight": "500g",
            "quality_score": 85,
            "price_score": 70,
            "trust_score": 90,
        }
    )

    assert isinstance(
        result,
        FoodKnowledgeResult,
    )

    assert result.category_id == (
        "vegetable"
    )
    assert result.category_name == "채소"

    assert result.attributes[
        "origin"
    ] == "국산"

    assert result.attributes[
        "variety"
    ] == "상추"

    assert result.attributes[
        "weight_grams"
    ] == 500.0

    assert 0.0 <= result.confidence <= 1.0
    assert result.final_score is not None


def test_vegetable_provider_preserves_raw_product():
    provider = VegetableKnowledgeProvider()

    product = {
        "product_name": "국산 당근",
        "origin": "국산",
        "variety": "당근",
    }

    result = provider.analyze(
        product
    )

    assert result.raw_product == product


def test_vegetable_provider_metadata():
    provider = VegetableKnowledgeProvider()

    result = provider.analyze(
        {
            "product_name": "상추",
            "variety": "상추",
        }
    )

    assert result.metadata[
        "provider"
    ] == "VegetableKnowledgeProvider"

    assert result.metadata[
        "provider_version"
    ] == "1.0"
