import pytest

from app.services.food.knowledge.alias_resolution import (
    AliasCollisionError,
)
from app.services.food.knowledge.base import (
    FoodKnowledgeProvider,
)
from app.services.food.knowledge.models import (
    FoodKnowledgeContext,
    FoodKnowledgeResult,
)
from app.services.food.knowledge.registry import (
    FoodKnowledgeRegistry,
)


class _Provider(
    FoodKnowledgeProvider,
):
    def __init__(
        self,
        *,
        category_id: str,
        aliases: tuple[str, ...],
    ) -> None:
        self.category_id = category_id
        self.category_name = category_id
        self.aliases = aliases

    def supports(
        self,
        category_id: str | None = None,
        product_name: str | None = None,
    ) -> bool:
        return category_id == self.category_id

    def analyze(
        self,
        product,
        context: FoodKnowledgeContext | None = None,
    ) -> FoodKnowledgeResult:
        raise NotImplementedError


def test_failed_registration_does_not_mutate_registry() -> None:
    registry = FoodKnowledgeRegistry()

    fruit = _Provider(
        category_id="fruit",
        aliases=("apple",),
    )
    vegetable = _Provider(
        category_id="vegetable",
        aliases=("apple",),
    )

    registry.register(fruit)

    before = registry.list_category_ids()

    with pytest.raises(AliasCollisionError):
        registry.register(vegetable)

    assert registry.list_category_ids() == before
    assert registry.get("fruit") is fruit
    assert registry.get("vegetable") is None

    assert (
        registry.resolve(category_id="apple")
        is fruit
    )


def test_failed_replace_restores_previous_provider() -> None:
    registry = FoodKnowledgeRegistry()

    coffee = _Provider(
        category_id="coffee",
        aliases=("coffee-alias",),
    )
    tea = _Provider(
        category_id="tea",
        aliases=("tea-alias",),
    )

    registry.register(coffee)
    registry.register(tea)

    conflicting_replacement = _Provider(
        category_id="coffee",
        aliases=("tea-alias",),
    )

    with pytest.raises(AliasCollisionError):
        registry.register(
            conflicting_replacement,
            replace=True,
        )

    assert registry.get("coffee") is coffee
    assert registry.get("tea") is tea

    assert (
        registry.resolve(
            category_id="coffee-alias",
        )
        is coffee
    )

    assert (
        registry.resolve(
            category_id="tea-alias",
        )
        is tea
    )


def test_successful_replace_updates_aliases_atomically() -> None:
    registry = FoodKnowledgeRegistry()

    original = _Provider(
        category_id="coffee",
        aliases=("old-coffee",),
    )

    replacement = _Provider(
        category_id="coffee",
        aliases=("new-coffee",),
    )

    registry.register(original)

    registry.register(
        replacement,
        replace=True,
    )

    assert registry.get("coffee") is replacement

    assert (
        registry.resolve(
            category_id="new-coffee",
        )
        is replacement
    )

    assert (
        registry.resolve(
            category_id="old-coffee",
        )
        is None
    )


def test_resolution_is_deterministic_after_repeated_rebuilds() -> None:
    registry = FoodKnowledgeRegistry()

    coffee = _Provider(
        category_id="coffee",
        aliases=("커피",),
    )
    tea = _Provider(
        category_id="tea",
        aliases=("차",),
    )

    registry.register(coffee)
    registry.register(tea)

    results = []

    for _ in range(20):
        results.append(
            registry.resolve(
                category_id="커피",
            )
        )

    assert results == [coffee] * 20
