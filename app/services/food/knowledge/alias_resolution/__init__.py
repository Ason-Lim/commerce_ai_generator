from app.services.food.knowledge.alias_resolution.bootstrap import (
    build_provider_alias_registry,
    build_provider_alias_resolver,
)
from app.services.food.knowledge.alias_resolution.normalizer import (
    AliasNormalizer,
)
from app.services.food.knowledge.alias_resolution.registry import (
    AliasCollisionError,
    AliasRegistry,
)
from app.services.food.knowledge.alias_resolution.resolver import (
    AliasResolver,
)

__all__ = [
    "AliasCollisionError",
    "AliasNormalizer",
    "AliasRegistry",
    "AliasResolver",
    "build_provider_alias_registry",
    "build_provider_alias_resolver",
]
