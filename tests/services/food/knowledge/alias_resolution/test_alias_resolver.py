from app.services.food.knowledge.alias_resolution import (
    AliasRegistry,
    AliasResolver,
)


def test_direct_canonical_identity_has_precedence() -> None:
    registry = AliasRegistry()
    registry.register("커피", "coffee")

    resolver = AliasResolver(registry)

    assert (
        resolver.resolve(
            "coffee",
            canonical_ids=("coffee", "tea"),
        )
        == "coffee"
    )


def test_registered_alias_resolves_to_canonical_identity() -> None:
    registry = AliasRegistry()
    registry.register("커피", "coffee")

    resolver = AliasResolver(registry)

    assert (
        resolver.resolve(
            "커피",
            canonical_ids=("coffee", "tea"),
        )
        == "coffee"
    )


def test_unknown_alias_does_not_fabricate_identity() -> None:
    registry = AliasRegistry()
    resolver = AliasResolver(registry)

    assert (
        resolver.resolve(
            "unknown-food",
            canonical_ids=("coffee", "tea"),
        )
        is None
    )


def test_empty_value_does_not_resolve() -> None:
    registry = AliasRegistry()
    resolver = AliasResolver(registry)

    assert resolver.resolve(None) is None
    assert resolver.resolve("") is None
