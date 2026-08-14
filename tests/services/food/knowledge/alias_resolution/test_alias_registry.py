import pytest

from app.services.food.knowledge.alias_resolution import (
    AliasCollisionError,
    AliasRegistry,
)


def test_registry_resolves_registered_alias() -> None:
    registry = AliasRegistry()

    registry.register("커피", "coffee")

    assert registry.resolve("커피") == "coffee"
    assert registry.resolve("  커피  ") == "coffee"


def test_registry_normalizes_alias_and_identity() -> None:
    registry = AliasRegistry()

    registry.register(" COFFEE ", " Coffee ")

    assert registry.resolve("coffee") == "coffee"


def test_same_mapping_can_be_registered_repeatedly() -> None:
    registry = AliasRegistry()

    registry.register("coffee", "coffee")
    registry.register(" COFFEE ", "COFFEE")

    assert len(registry) == 1


def test_collision_is_explicit() -> None:
    registry = AliasRegistry()

    registry.register("apple", "fruit")

    with pytest.raises(AliasCollisionError):
        registry.register("apple", "vegetable")


def test_empty_alias_is_rejected() -> None:
    registry = AliasRegistry()

    with pytest.raises(ValueError):
        registry.register(" ", "fruit")


def test_empty_canonical_identity_is_rejected() -> None:
    registry = AliasRegistry()

    with pytest.raises(ValueError):
        registry.register("apple", " ")


def test_register_many() -> None:
    registry = AliasRegistry()

    registry.register_many(
        "coffee",
        (
            "커피",
            "coffee",
            "원두",
        ),
    )

    assert registry.resolve("커피") == "coffee"
    assert registry.resolve("coffee") == "coffee"
    assert registry.resolve("원두") == "coffee"


def test_aliases_for_canonical_identity() -> None:
    registry = AliasRegistry()

    registry.register_many(
        "coffee",
        (
            "커피",
            "원두",
        ),
    )

    assert registry.aliases_for("coffee") == (
        "커피",
        "원두",
    )
