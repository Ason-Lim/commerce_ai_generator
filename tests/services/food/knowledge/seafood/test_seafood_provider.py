from __future__ import annotations

import pytest

from app.services.food.knowledge.models import (
    FoodKnowledgeResult,
)
from app.services.food.knowledge.seafood.provider import (
    SeafoodKnowledgeProvider,
)


def test_seafood_provider_supports_category_id():
    provider = SeafoodKnowledgeProvider()

    assert provider.supports(
        category_id="seafood"
    )


@pytest.mark.parametrize(
    "product_name",
    [
        "노르웨이 연어 500g",
        "냉동 새우 800g",
        "자연산 대게 1kg",
        "생물 전복 1kg",
        "손질 오징어 500g",
    ],
)
def test_seafood_provider_supports_representative_products(
    product_name,
):
    provider = SeafoodKnowledgeProvider()

    assert provider.supports(
        product_name=product_name
    )


def test_seafood_provider_does_not_support_unrelated_product():
    provider = SeafoodKnowledgeProvider()

    assert not provider.supports(
        product_name="제주 사과 3kg"
    )


def test_seafood_provider_builds_result_contract():
    provider = SeafoodKnowledgeProvider()

    result = provider.analyze(
        {
            "product_name": "노르웨이산 냉장 생연어 500g",
            "origin": "노르웨이",
            "quality_score": 82,
            "price_score": 72,
            "trust_score": 88,
        }
    )

    assert isinstance(
        result,
        FoodKnowledgeResult,
    )

    assert result.category_id == "seafood"
    assert result.category_name == "수산물"
    assert result.attributes["species"] == "salmon"
    assert result.attributes["seafood_group"] == "fish"
    assert result.attributes["processing_state"] == "fresh"

    payload = result.to_dict()

    required = {
        "category_id",
        "category_name",
        "product_name",
        "attributes",
        "scores",
        "reasons",
        "warnings",
        "final_score",
    }

    assert required.issubset(payload)


def test_seafood_provider_is_deterministic():
    provider = SeafoodKnowledgeProvider()

    product = {
        "product_name": "냉동 새우 800g",
        "quality_score": 75,
        "price_score": 80,
        "trust_score": 70,
    }

    first = provider.analyze(product)
    second = provider.analyze(product)

    assert first.to_dict() == second.to_dict()


def test_seafood_provider_rejects_non_mapping():
    provider = SeafoodKnowledgeProvider()

    with pytest.raises(TypeError):
        provider.analyze("연어")
