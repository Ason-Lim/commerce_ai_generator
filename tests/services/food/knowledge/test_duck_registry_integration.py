from __future__ import annotations

from app.services.food.knowledge.meat.duck.breed_registry import (
    DuckBreedRegistry,
)
from app.services.food.knowledge.meat.duck.cut_registry import (
    DuckCutRegistry,
)
from app.services.food.knowledge.meat.duck.provider import (
    DuckKnowledgeProvider,
)
from app.services.food.knowledge.meat.duck.type_registry import (
    DuckTypeRegistry,
)
from app.services.food.knowledge.registry import (
    get_food_provider,
    list_food_providers,
    require_food_provider,
    resolve_food_provider,
)


def test_duck_provider_is_registered() -> None:
    provider = get_food_provider("duck")

    assert isinstance(
        provider,
        DuckKnowledgeProvider,
    )
    assert (
        require_food_provider("duck")
        is provider
    )


def test_default_provider_order_includes_duck() -> None:
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


def test_resolve_duck_by_category_id() -> None:
    provider = resolve_food_provider(
        category_id="duck"
    )

    assert isinstance(
        provider,
        DuckKnowledgeProvider,
    )


def test_resolve_duck_by_product_name() -> None:
    provider = resolve_food_provider(
        product_name=(
            "국내산 훈제오리 체리밸리 "
            "오리가슴살 500g"
        )
    )

    assert isinstance(
        provider,
        DuckKnowledgeProvider,
    )


def test_duck_registry_data_loads() -> None:
    type_registry = DuckTypeRegistry()
    breed_registry = DuckBreedRegistry()
    cut_registry = DuckCutRegistry()

    assert type_registry.registry_id == (
        "duck.types"
    )
    assert breed_registry.registry_id == (
        "duck.breeds"
    )
    assert cut_registry.registry_id == (
        "duck.cuts"
    )

    assert type_registry.list()
    assert breed_registry.list()
    assert cut_registry.list()


def test_registered_provider_analyzes_product() -> None:
    provider = require_food_provider(
        "duck"
    )

    result = provider.analyze(
        {
            "product_name": (
                "국내산 훈제오리 체리밸리 "
                "오리가슴살 500g"
            ),
            "country": "대한민국",
            "quality_score": 80,
            "price_score": 70,
            "trust_score": 90,
        }
    )

    assert result.category_id == "duck"
    assert (
        result.metadata["provider_id"]
        == "duck"
    )
    assert (
        result.metadata[
            "parent_category_id"
        ]
        == "meat"
    )
    assert result.scores["knowledge"] == 86.6
    assert result.final_score == 83.3
