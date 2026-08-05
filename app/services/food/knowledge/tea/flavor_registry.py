from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from app.services.food.knowledge.common.base_model import (
    RegistryMatch,
)
from app.services.food.knowledge.common.base_registry import (
    optional_string,
)
from app.services.food.knowledge.tea._registry_support import (
    TeaAliasRegistry,
    TeaRegistryEntry,
)


TEA_FLAVOR_REGISTRY_ID = "tea.flavors"


@dataclass(
    frozen=True,
    kw_only=True,
)
class TeaFlavor(TeaRegistryEntry):
    """Canonical Tea flavor or aroma family."""

    flavor_family: str | None = None
    sensory_dimension: str | None = None
    aroma_dominant: bool = False
    taste_dominant: bool = False


@dataclass(
    frozen=True,
    kw_only=True,
)
class TeaFlavorMatch(
    RegistryMatch[TeaFlavor]
):
    """Typed alias match for a Tea flavor."""

    @property
    def tea_flavor(self) -> TeaFlavor:
        return self.entry


class TeaFlavorRegistry(
    TeaAliasRegistry[TeaFlavor]
):
    """Declarative Registry for Tea flavor and aroma vocabulary."""

    registry_id = TEA_FLAVOR_REGISTRY_ID
    entry_class = TeaFlavor

    def build_entry(
        self,
        registry_key: str,
        raw_entry: Mapping[str, Any],
    ) -> TeaFlavor:
        known_fields = {
            "canonical_name",
            "aliases",
            "score",
            "premium",
            "description",
            "flavor_family",
            "sensory_dimension",
            "aroma_dominant",
            "taste_dominant",
        }

        return TeaFlavor(
            **self.common_fields(
                registry_key=registry_key,
                raw_entry=raw_entry,
                known_fields=known_fields,
            ),
            flavor_family=optional_string(
                raw_entry.get("flavor_family")
            ),
            sensory_dimension=optional_string(
                raw_entry.get("sensory_dimension")
            ),
            aroma_dominant=bool(
                raw_entry.get(
                    "aroma_dominant",
                    False,
                )
            ),
            taste_dominant=bool(
                raw_entry.get(
                    "taste_dominant",
                    False,
                )
            ),
        )

    def match(
        self,
        text: str,
    ) -> TeaFlavorMatch | None:
        raw_match = super().match(text)

        if raw_match is None:
            return None

        return self.convert_match(
            raw_match,
            TeaFlavorMatch,
        )  # type: ignore[return-value]


__all__ = [
    "TEA_FLAVOR_REGISTRY_ID",
    "TeaFlavor",
    "TeaFlavorMatch",
    "TeaFlavorRegistry",
]
