from app.services.food.category_registry import (
    get_food_category,
    resolve_food_category,
)
from app.services.food.knowledge.registry import (
    get_food_provider,
    list_food_providers,
    resolve_food_provider,
)
from app.services.food.knowledge.vegetable.provider import (
    VegetableKnowledgeProvider,
)


def test_vegetable_category_is_registered():
    config = get_food_category("vegetable")

    assert config is not None
    assert config.category_id == "vegetable"
    assert config.provider_id == "vegetable"
    assert config.display_name == "채소"


def test_vegetable_category_alias_resolves():
    config = resolve_food_category(
        category_id="채소"
    )

    assert config is not None
    assert config.category_id == "vegetable"


def test_vegetable_provider_is_registered():
    provider = get_food_provider(
        "vegetable"
    )

    assert isinstance(
        provider,
        VegetableKnowledgeProvider,
    )


def test_vegetable_provider_resolves_by_category():
    provider = resolve_food_provider(
        category_id="vegetable"
    )

    assert isinstance(
        provider,
        VegetableKnowledgeProvider,
    )


def test_vegetable_provider_resolves_by_product_name():
    provider = resolve_food_provider(
        product_name="유기농 상추 500g"
    )

    assert isinstance(
        provider,
        VegetableKnowledgeProvider,
    )


def test_vegetable_provider_is_after_fruit():
    category_ids = [
        provider.category_id
        for provider in list_food_providers()
    ]

    assert "fruit" in category_ids
    assert "vegetable" in category_ids

    assert (
        category_ids.index("vegetable")
        == category_ids.index("fruit") + 1
    )


def test_vegetable_registration_preserves_legacy_provider_order():
    category_ids = [
        provider.category_id
        for provider in list_food_providers()
    ]

    legacy_ids = [
        category_id
        for category_id in category_ids
        if category_id != "vegetable"
    ]

    expected_legacy_ids = [
        "fruit",
        "cheese",
        "coffee",
        "wine",
        "tea",
        "olive_oil",
        "herb_spice",
        "venison",
        "goat",
        "beef",
        "lamb",
        "chicken",
        "duck",
    ]

    actual_legacy_ids = [
        category_id
        for category_id in legacy_ids
        if category_id in expected_legacy_ids
    ]

    assert actual_legacy_ids == expected_legacy_ids
