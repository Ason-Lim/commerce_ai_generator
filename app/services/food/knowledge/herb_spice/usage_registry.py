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


HERB_SPICE_USAGE_REGISTRY_ID = "herb_spice.usages"


@dataclass(
    frozen=True,
    kw_only=True,
)
class HerbSpiceUsage(HerbSpiceRegistryEntry):
    """Canonical culinary usage for herbs and spices."""

    usage_category: str | None = None
    dry_heat: bool = False
    wet_cooking: bool = False
    finishing: bool = False
    beverage: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()

        object.__setattr__(
            self,
            "usage_category",
            optional_string(
                self.usage_category
            ),
        )
        object.__setattr__(
            self,
            "dry_heat",
            bool(self.dry_heat),
        )
        object.__setattr__(
            self,
            "wet_cooking",
            bool(self.wet_cooking),
        )
        object.__setattr__(
            self,
            "finishing",
            bool(self.finishing),
        )
        object.__setattr__(
            self,
            "beverage",
            bool(self.beverage),
        )


@dataclass(
    frozen=True,
    kw_only=True,
)
class HerbSpiceUsageMatch(
    RegistryMatch[HerbSpiceUsage]
):
    """Typed alias match for a Herb & Spice usage."""

    @property
    def usage(self) -> HerbSpiceUsage:
        return self.entry


class HerbSpiceUsageRegistry(
    HerbSpiceAliasRegistry[HerbSpiceUsage]
):
    """Declarative Registry for Herb & Spice culinary usages."""

    registry_id = HERB_SPICE_USAGE_REGISTRY_ID
    entry_class = HerbSpiceUsage

    def build_entry(
        self,
        registry_key: str,
        raw_entry: Mapping[str, Any],
    ) -> HerbSpiceUsage:
        known_fields = {
            "canonical_name",
            "aliases",
            "score",
            "premium",
            "description",
            "usage_category",
            "dry_heat",
            "wet_cooking",
            "finishing",
            "beverage",
        }

        return HerbSpiceUsage(
            **self.common_fields(
                registry_key=registry_key,
                raw_entry=raw_entry,
                known_fields=known_fields,
            ),
            usage_category=optional_string(
                raw_entry.get("usage_category")
            ),
            dry_heat=bool(
                raw_entry.get("dry_heat", False)
            ),
            wet_cooking=bool(
                raw_entry.get(
                    "wet_cooking",
                    False,
                )
            ),
            finishing=bool(
                raw_entry.get("finishing", False)
            ),
            beverage=bool(
                raw_entry.get("beverage", False)
            ),
        )

    def match(
        self,
        text: str,
    ) -> HerbSpiceUsageMatch | None:
        raw_match = super().match(text)

        if raw_match is None:
            return None

        return self.convert_match(
            raw_match,
            HerbSpiceUsageMatch,
        )  # type: ignore[return-value]


__all__ = [
    "HERB_SPICE_USAGE_REGISTRY_ID",
    "HerbSpiceUsage",
    "HerbSpiceUsageMatch",
    "HerbSpiceUsageRegistry",
]
