from __future__ import annotations

from collections.abc import Iterable

from app.services.food.knowledge.alias_resolution.registry import (
    AliasRegistry,
)
from app.services.food.knowledge.alias_resolution.resolver import (
    AliasResolver,
)
from app.services.food.knowledge.base import (
    FoodKnowledgeProvider,
)


def build_provider_alias_registry(
    providers: Iterable[FoodKnowledgeProvider],
) -> AliasRegistry:
    """
    Build a deterministic alias registry from provider-owned aliases.

    Provider category IDs remain the canonical identities.
    This function does not mutate provider registration state.
    """
    registry = AliasRegistry()

    for provider in providers:
        canonical_id = provider.category_id

        registry.register(
            canonical_id,
            canonical_id,
        )

        registry.register_many(
            canonical_id,
            getattr(provider, "aliases", ()),
        )

    return registry


def build_provider_alias_resolver(
    providers: Iterable[FoodKnowledgeProvider],
) -> AliasResolver:
    providers = tuple(providers)

    registry = build_provider_alias_registry(
        providers
    )

    return AliasResolver(
        registry
    )
