from __future__ import annotations

from app.services.food.knowledge.meat.chicken.provider import (
    ChickenKnowledgeProvider,
)
from app.services.food.knowledge.meat.chicken.breed_registry import (
    ChickenBreedRegistry,
)
from app.services.food.knowledge.meat.chicken.cut_registry import (
    ChickenCutRegistry,
)
from app.services.food.knowledge.meat.chicken.type_registry import (
    ChickenTypeRegistry,
)
from app.services.food.knowledge.registry import (
    get_food_provider,
    list_food_providers,
    require_food_provider,
    resolve_food_provider,
)


def test_chicken_provider_is_registered() -> None:
    provider = get_food_provider("chicken")

    assert isinstance(
        provider,
        ChickenKnowledgeProvider,
    )
    assert (
        require_food_provider("chicken")
        is provider
    )


def test_default_provider_order_includes_chicken() -> None:
    category_ids = [
        provider.category_id
        for provider in list_food_providers()
    ]

    required = {
        "fruit",
        "venison",
        "beef",
        "lamb",
        "chicken",
        "duck",
    }

    assert required.issubset(set(category_ids))

    assert len(category_ids) == len(set(category_ids))

    assert (
        category_ids.index("venison")
        < category_ids.index("beef")
    )


def test_resolve_chicken_by_category_id() -> None:
    provider = resolve_food_provider(
        category_id="chicken"
    )

    assert isinstance(
        provider,
        ChickenKnowledgeProvider,
    )


def test_resolve_chicken_by_product_name() -> None:
    provider = resolve_food_provider(
        product_name=(
            "국내산 토종닭 닭다리살 500g"
        )
    )

    assert isinstance(
        provider,
        ChickenKnowledgeProvider,
    )


def test_chicken_registry_data_loads() -> None:
    type_registry = ChickenTypeRegistry()
    breed_registry = ChickenBreedRegistry()
    cut_registry = ChickenCutRegistry()

    assert type_registry.registry_id == (
        "chicken.types"
    )
    assert breed_registry.registry_id == (
        "chicken.breeds"
    )
    assert cut_registry.registry_id == (
        "chicken.cuts"
    )

    assert type_registry.list()
    assert breed_registry.list()
    assert cut_registry.list()


def test_registered_provider_analyzes_product() -> None:
    provider = require_food_provider(
        "chicken"
    )

    result = provider.analyze(
        {
            "product_name": (
                "국내산 토종닭 Ross 308 "
                "닭다리살 500g"
            ),
            "country": "대한민국",
            "quality_score": 80,
            "price_score": 70,
            "trust_score": 90,
        }
    )

    assert result.category_id == "chicken"
    assert (
        result.metadata["provider_id"]
        == "chicken"
    )
    assert (
        result.metadata[
            "parent_category_id"
        ]
        == "meat"
    )
    assert result.scores["knowledge"] == 86.8
    assert result.final_score == 83.4
