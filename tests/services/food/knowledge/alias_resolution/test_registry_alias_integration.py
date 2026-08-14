from app.services.food.knowledge.registry import (
    FoodKnowledgeRegistry,
    resolve_food_provider,
)
from app.services.food.knowledge.coffee.provider import (
    CoffeeKnowledgeProvider,
)
from app.services.food.knowledge.tea.provider import (
    TeaKnowledgeProvider,
)


def test_global_registry_resolves_provider_alias_category_id() -> None:
    cases = [
        ("커피", "coffee"),
        ("올리브오일", "olive_oil"),
        ("허브 향신료", "herb_spice"),
        ("야채", "vegetable"),
        ("연어", "seafood"),
    ]

    for alias, expected in cases:
        provider = resolve_food_provider(
            category_id=alias,
        )

        assert provider is not None
        assert provider.category_id == expected


def test_direct_canonical_identity_still_resolves() -> None:
    provider = resolve_food_provider(
        category_id="coffee",
    )

    assert provider is not None
    assert provider.category_id == "coffee"


def test_product_name_fallback_remains_operational() -> None:
    provider = resolve_food_provider(
        product_name="에티오피아 예가체프 커피",
    )

    assert provider is not None
    assert provider.category_id == "coffee"


def test_alias_registry_rebuilds_after_registration() -> None:
    registry = FoodKnowledgeRegistry()

    coffee = CoffeeKnowledgeProvider()

    registry.register(coffee)

    provider = registry.resolve(
        category_id="커피",
    )

    assert provider is coffee


def test_alias_registry_rebuilds_after_unregister() -> None:
    registry = FoodKnowledgeRegistry()

    coffee = CoffeeKnowledgeProvider()
    tea = TeaKnowledgeProvider()

    registry.register(coffee)
    registry.register(tea)

    assert (
        registry.resolve(
            category_id="커피",
        )
        is coffee
    )

    removed = registry.unregister("coffee")

    assert removed is coffee

    assert (
        registry.resolve(
            category_id="커피",
        )
        is None
    )


def test_provider_order_is_not_changed_by_alias_resolution() -> None:
    registry = FoodKnowledgeRegistry()

    coffee = CoffeeKnowledgeProvider()
    tea = TeaKnowledgeProvider()

    registry.register(coffee)
    registry.register(tea)

    assert registry.list_category_ids() == [
        "coffee",
        "tea",
    ]
