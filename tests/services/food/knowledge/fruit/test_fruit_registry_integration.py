from __future__ import annotations

import pytest

from app.services.food.category_registry import (
    resolve_food_category,
)
from app.services.food.knowledge.fruit.provider import (
    FruitKnowledgeProvider,
)
from app.services.food.knowledge.models import (
    FoodKnowledgeResult,
)
from app.services.food.knowledge.registry import (
    FOOD_KNOWLEDGE_REGISTRY,
    get_food_provider,
    list_food_providers,
    require_food_provider,
    resolve_food_provider,
)
from app.services.food.resolver import (
    analyze_food_product,
    resolve_food_knowledge,
    resolve_knowledge_provider,
    resolve_product_category,
)


def test_fruit_provider_is_registered() -> None:
    provider = get_food_provider(
        "fruit"
    )

    assert isinstance(
        provider,
        FruitKnowledgeProvider,
    )

    assert provider.category_id == "fruit"


def test_fruit_provider_is_in_registry() -> None:
    assert (
        "fruit"
        in FOOD_KNOWLEDGE_REGISTRY
    )

    assert (
        "fruit"
        in FOOD_KNOWLEDGE_REGISTRY
        .list_category_ids()
    )


def test_fruit_provider_registered_once() -> None:
    providers = list_food_providers()

    fruit_providers = [
        provider
        for provider in providers
        if provider.category_id == "fruit"
    ]

    assert len(fruit_providers) == 1


def test_provider_ids_are_unique() -> None:
    provider_ids = [
        provider.category_id
        for provider in list_food_providers()
    ]

    assert len(provider_ids) == len(
        set(provider_ids)
    )


def test_require_fruit_provider() -> None:
    provider = require_food_provider(
        "fruit"
    )

    assert isinstance(
        provider,
        FruitKnowledgeProvider,
    )


@pytest.mark.parametrize(
    "category_id",
    [
        "fruit",
        "FRUIT",
        " fruit ",
    ],
)
def test_resolve_provider_by_category_id(
    category_id: str,
) -> None:
    provider = resolve_food_provider(
        category_id=category_id
    )

    assert isinstance(
        provider,
        FruitKnowledgeProvider,
    )


@pytest.mark.parametrize(
    "category_id",
    [
        "과일",
        "사과",
        "감귤",
        "복숭아",
    ],
)
def test_resolve_provider_by_category_alias(
    category_id: str,
) -> None:
    provider = resolve_food_provider(
        category_id=category_id
    )

    assert isinstance(
        provider,
        FruitKnowledgeProvider,
    )


@pytest.mark.parametrize(
    "product_name",
    [
        "고당도 사과",
        "제주 감귤",
        "프리미엄 복숭아",
        "국산 배 선물세트",
    ],
)
def test_resolve_provider_by_product_name(
    product_name: str,
) -> None:
    provider = resolve_food_provider(
        product_name=product_name
    )

    assert isinstance(
        provider,
        FruitKnowledgeProvider,
    )


@pytest.mark.parametrize(
    "product_name",
    [
        "고당도 사과",
        "제주 감귤",
        "국산 배",
    ],
)
def test_category_registry_routes_fruit(
    product_name: str,
) -> None:
    category = resolve_food_category(
        product_name=product_name
    )

    assert category is not None
    assert category.category_id == "fruit"
    assert category.provider_id == "fruit"


def test_resolve_product_category() -> None:
    category = resolve_product_category(
        {
            "product_name": (
                "고당도 사과"
            ),
        }
    )

    assert category is not None
    assert category.category_id == "fruit"


def test_resolve_product_category_explicit() -> None:
    category = resolve_product_category(
        {
            "product_name": (
                "상품명만으로는 불명확"
            ),
        },
        category_id="fruit",
    )

    assert category is not None
    assert category.category_id == "fruit"


def test_resolve_knowledge_provider_by_product() -> None:
    provider = resolve_knowledge_provider(
        {
            "product_name": (
                "고당도 사과"
            ),
        }
    )

    assert isinstance(
        provider,
        FruitKnowledgeProvider,
    )


def test_resolve_knowledge_provider_explicit() -> None:
    provider = resolve_knowledge_provider(
        {
            "product_name": (
                "일반 상품"
            ),
        },
        category_id="fruit",
    )

    assert isinstance(
        provider,
        FruitKnowledgeProvider,
    )


def test_analyze_food_product_routes_to_fruit() -> None:
    result = analyze_food_product(
        {
            "product_name": (
                "고당도 제주 감귤 "
                "12브릭스 2kg"
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
    assert result.attributes[
        "origin"
    ] == "제주"

    assert result.attributes[
        "brix"
    ] == 12.0


def test_analyze_food_product_explicit_category() -> None:
    result = analyze_food_product(
        {
            "product_name": "사과 1kg",
            "weight": "1kg",
        },
        category_id="fruit",
    )

    assert isinstance(
        result,
        FoodKnowledgeResult,
    )

    assert result.category_id == "fruit"
    assert result.attributes[
        "weight_grams"
    ] == 1000.0


def test_resolve_food_knowledge_routes_to_fruit() -> None:
    result = resolve_food_knowledge(
        {
            "product_name": (
                "제주 감귤 13브릭스"
            ),
            "origin": "제주",
        },
        category_id="fruit",
    )

    assert isinstance(
        result,
        FoodKnowledgeResult,
    )

    assert result.category_id == "fruit"
    assert result.attributes[
        "brix"
    ] == 13.0


def test_runtime_result_contract() -> None:
    result = analyze_food_product(
        {
            "product_name": (
                "고당도 사과 14브릭스 1kg"
            ),
            "weight": "1kg",
        },
        category_id="fruit",
    )

    assert result is not None

    payload = result.to_dict()

    required_keys = {
        "category_id",
        "category_name",
        "product_name",
        "attributes",
        "attribute_details",
        "scores",
        "score_details",
        "rules",
        "reasons",
        "warnings",
        "final_score",
        "confidence",
        "metadata",
        "raw_product",
    }

    assert required_keys.issubset(
        payload
    )

    assert payload[
        "category_id"
    ] == "fruit"


def test_runtime_routing_is_deterministic() -> None:
    product = {
        "product_name": (
            "고당도 제주 감귤 "
            "12브릭스 2kg"
        ),
        "origin": "제주",
        "weight": "2kg",
    }

    first_provider = (
        resolve_knowledge_provider(
            product
        )
    )

    second_provider = (
        resolve_knowledge_provider(
            product
        )
    )

    assert type(first_provider) is type(
        second_provider
    )

    assert isinstance(
        first_provider,
        FruitKnowledgeProvider,
    )
