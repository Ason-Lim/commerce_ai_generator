from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from app.services.food.knowledge.common.base_model import (
    RegistryMatch,
)
from app.services.food.knowledge.common.base_registry import (
    optional_string,
    safe_float,
)
from app.services.food.knowledge.herb_spice._registry_support import (
    HerbSpiceAliasRegistry,
    HerbSpiceRegistryEntry,
)


SPICE_REGISTRY_ID = "herb_spice.spices"


@dataclass(
    frozen=True,
    kw_only=True,
)
class Spice(HerbSpiceRegistryEntry):
    """Canonical culinary spice entry."""

    botanical_name: str | None = None
    plant_part: str | None = None
    flavor_profile: str | None = None
    heat_level: float = 0.0
    pungent: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()

        object.__setattr__(
            self,
            "heat_level",
            max(
                0.0,
                min(
                    10.0,
                    float(self.heat_level),
                ),
            ),
        )
        object.__setattr__(
            self,
            "pungent",
            bool(self.pungent),
        )


@dataclass(
    frozen=True,
    kw_only=True,
)
class SpiceMatch(
    RegistryMatch[Spice]
):
    """Typed alias match for a culinary spice."""

    @property
    def spice(self) -> Spice:
        return self.entry


class SpiceRegistry(
    HerbSpiceAliasRegistry[Spice]
):
    """Declarative Registry for culinary spices."""

    registry_id = SPICE_REGISTRY_ID
    entry_class = Spice

    def build_entry(
        self,
        registry_key: str,
        raw_entry: Mapping[str, Any],
    ) -> Spice:
        known_fields = {
            "canonical_name",
            "aliases",
            "score",
            "premium",
            "description",
            "botanical_name",
            "plant_part",
            "flavor_profile",
            "heat_level",
            "pungent",
        }

        return Spice(
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
            heat_level=max(
                0.0,
                min(
                    10.0,
                    safe_float(
                        raw_entry.get("heat_level"),
                        default=0.0,
                    ),
                ),
            ),
            pungent=bool(
                raw_entry.get("pungent", False)
            ),
        )

    def match(
        self,
        text: str,
    ) -> SpiceMatch | None:
        raw_match = super().match(text)

        if raw_match is None:
            return None

        return self.convert_match(
            raw_match,
            SpiceMatch,
        )  # type: ignore[return-value]


__all__ = [
    "SPICE_REGISTRY_ID",
    "Spice",
    "SpiceMatch",
    "SpiceRegistry",
]
