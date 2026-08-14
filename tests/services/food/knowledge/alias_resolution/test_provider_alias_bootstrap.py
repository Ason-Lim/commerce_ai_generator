from app.services.food.knowledge.alias_resolution.bootstrap import (
    build_provider_alias_registry,
    build_provider_alias_resolver,
)
from app.services.food.knowledge.registry import (
    FOOD_KNOWLEDGE_REGISTRY,
)


def test_all_provider_aliases_bootstrap_without_collision() -> None:
    providers = FOOD_KNOWLEDGE_REGISTRY.list_providers()

    registry = build_provider_alias_registry(
        providers
    )

    assert len(providers) == 15
    assert len(registry) > 15


def test_all_canonical_provider_ids_resolve() -> None:
    providers = FOOD_KNOWLEDGE_REGISTRY.list_providers()

    resolver = build_provider_alias_resolver(
        providers
    )

    canonical_ids = [
        provider.category_id
        for provider in providers
    ]

    for category_id in canonical_ids:
        assert (
            resolver.resolve(
                category_id,
                canonical_ids=canonical_ids,
            )
            == category_id
        )


def test_provider_aliases_resolve_to_owner() -> None:
    providers = FOOD_KNOWLEDGE_REGISTRY.list_providers()

    resolver = build_provider_alias_resolver(
        providers
    )

    canonical_ids = [
        provider.category_id
        for provider in providers
    ]

    for provider in providers:
        for alias in provider.aliases:
            assert (
                resolver.resolve(
                    alias,
                    canonical_ids=canonical_ids,
                )
                == provider.category_id
            )


def test_representative_aliases_resolve() -> None:
    providers = FOOD_KNOWLEDGE_REGISTRY.list_providers()

    resolver = build_provider_alias_resolver(
        providers
    )

    canonical_ids = [
        provider.category_id
        for provider in providers
    ]

    cases = [
        ("커피", "coffee"),
        ("올리브오일", "olive_oil"),
        ("허브 향신료", "herb_spice"),
        ("연어", "seafood"),
        ("야채", "vegetable"),
    ]

    for alias, expected in cases:
        assert (
            resolver.resolve(
                alias,
                canonical_ids=canonical_ids,
            )
            == expected
        )
