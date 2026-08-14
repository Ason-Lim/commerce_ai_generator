from __future__ import annotations

from collections.abc import Iterable

from app.services.food.knowledge.alias_resolution.normalizer import (
    AliasNormalizer,
)
from app.services.food.knowledge.alias_resolution.registry import (
    AliasRegistry,
)


class AliasResolver:
    """
    Resolves terminology to an existing canonical identity.

    Resolution precedence:

    1. Direct canonical identity
    2. Registered alias
    3. No resolution

    Provider supports() fallback remains outside this component.
    """

    def __init__(
        self,
        registry: AliasRegistry,
        *,
        normalizer: AliasNormalizer | None = None,
    ) -> None:
        self._registry = registry
        self._normalizer = normalizer or AliasNormalizer()

    def resolve(
        self,
        value: str | None,
        *,
        canonical_ids: Iterable[str] = (),
    ) -> str | None:
        normalized_value = self._normalizer.normalize(value)

        if not normalized_value:
            return None

        normalized_canonical_ids = {
            self._normalizer.normalize(canonical_id)
            for canonical_id in canonical_ids
            if self._normalizer.normalize(canonical_id)
        }

        if normalized_value in normalized_canonical_ids:
            return normalized_value

        return self._registry.resolve(normalized_value)
