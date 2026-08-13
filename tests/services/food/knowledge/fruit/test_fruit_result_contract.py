from __future__ import annotations

import json

from app.services.food.knowledge.fruit.parser import (
    parse_fruit_product,
)
from app.services.food.knowledge.fruit.provider import (
    FruitKnowledgeProvider,
)
from app.services.food.knowledge.models import (
    FoodKnowledgeResult,
)


PRODUCT = {
    "product_name": (
        "고당도 제주 감귤 12브릭스 2kg"
    ),
    "origin": "제주",
    "variety": "감귤",
    "grade": "특품",
    "weight": "2kg",
}


def test_food_knowledge_result_serializes() -> None:
    result = FruitKnowledgeProvider().analyze(
        PRODUCT
    )

    assert isinstance(
        result,
        FoodKnowledgeResult,
    )

    payload = result.to_dict()

    assert payload["category_id"] == "fruit"
    assert payload["category_name"] == "과일"
    assert payload["attributes"]["brix"] == 12.0
    assert isinstance(payload["scores"], dict)
    assert isinstance(payload["reasons"], list)
    assert isinstance(payload["warnings"], list)


def test_food_knowledge_result_is_json_serializable() -> None:
    result = FruitKnowledgeProvider().analyze(
        PRODUCT
    )

    encoded = json.dumps(
        result.to_dict(),
        ensure_ascii=False,
    )

    assert '"category_id": "fruit"' in encoded


def test_provider_is_deterministic() -> None:
    provider = FruitKnowledgeProvider()

    first = provider.analyze(PRODUCT)
    second = provider.analyze(PRODUCT)

    assert first.to_dict() == second.to_dict()


def test_legacy_parser_is_deterministic() -> None:
    first = parse_fruit_product(PRODUCT)
    second = parse_fruit_product(PRODUCT)

    assert first == second


def test_result_nested_objects_are_independent() -> None:
    provider = FruitKnowledgeProvider()

    first = provider.analyze(PRODUCT)
    second = provider.analyze(PRODUCT)

    first.attributes["origin"] = "changed"
    first.reasons.append("changed")

    assert second.attributes["origin"] == "제주"
    assert "changed" not in second.reasons
