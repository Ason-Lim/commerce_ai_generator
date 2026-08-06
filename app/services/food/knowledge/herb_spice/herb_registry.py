from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from app.services.food.knowledge.common.base_model import (
    RegistryMatch,
)
from app.services.food.knowledge.common.base_registry import (
    optional_string,
)
from app.services.food.knowledge.herb_spice._registry_support import (
    HerbSpiceAliasRegistry,
    HerbSpiceRegistryEntry,
)


HERB_REGISTRY_ID = "herb_spice.herbs"


@dataclass(
    frozen=True,
    kw_only=True,
)
class Herb(HerbSpiceRegistryEntry):
    """Canonical culinary herb entry."""

    botanical_name: str | None = None
    plant_part: str | None = None
    flavor_profile: str | None = None
    fresh_available: bool = False
    dried_available: bool = False


@dataclass(
    frozen=True,
    kw_only=True,
)
class HerbMatch(
    RegistryMatch[Herb]
):
    """Typed alias match for a culinary herb."""

    @property
    def herb(self) -> Herb:
        return self.entry


class HerbRegistry(
    HerbSpiceAliasRegistry[Herb]
):
    """Declarative Registry for culinary herbs."""

    registry_id = HERB_REGISTRY_ID
    entry_class = Herb

    def build_entry(
        self,
        registry_key: str,
        raw_entry: Mapping[str, Any],
    ) -> Herb:
        known_fields = {
            "canonical_name",
            "aliases",
            "score",
            "premium",
            "description",
            "botanical_name",
            "plant_part",
            "flavor_profile",
            "fresh_available",
            "dried_available",
        }

        return Herb(
            **self.common_fields(
                registry_key=registry_key,
                raw_entry=raw_entry,
                known_fields=known_fields,
            ),
            botanical_name=optional_string(
                raw_entry.get("botanical_name")
            ),
            plant_part=optional_string(
                raw_entry.get("plant_part")
            ),
            flavor_profile=optional_string(
                raw_entry.get("flavor_profile")
            ),
            fresh_available=bool(
                raw_entry.get(
                    "fresh_available",
                    False,
                )
            ),
            dried_available=bool(
                raw_entry.get(
                    "dried_available",
                    False,
                )
            ),
        )

    def match(
        self,
        text: str,
    ) -> HerbMatch | None:
        raw_match = super().match(text)

        if raw_match is None:
            return None

        return self.convert_match(
            raw_match,
            HerbMatch,
        )  # type: ignore[return-value]


__all__ = [
    "HERB_REGISTRY_ID",
    "Herb",
    "HerbMatch",
    "HerbRegistry",
]
