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


HERB_SPICE_ORIGIN_REGISTRY_ID = "herb_spice.origins"


@dataclass(
    frozen=True,
    kw_only=True,
)
class HerbSpiceOrigin(HerbSpiceRegistryEntry):
    """Canonical Herb & Spice producing origin."""

    country_code: str | None = None
    country_name: str | None = None
    region_name: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()

        country_code = optional_string(
            self.country_code
        )

        if country_code is not None:
            country_code = country_code.upper()

        object.__setattr__(
            self,
            "country_code",
            country_code,
        )
        object.__setattr__(
            self,
            "country_name",
            optional_string(
                self.country_name
            ),
        )
        object.__setattr__(
            self,
            "region_name",
            optional_string(
                self.region_name
            ),
        )


@dataclass(
    frozen=True,
    kw_only=True,
)
class HerbSpiceOriginMatch(
    RegistryMatch[HerbSpiceOrigin]
):
    """Typed alias match for a Herb & Spice origin."""

    @property
    def origin(self) -> HerbSpiceOrigin:
        return self.entry


class HerbSpiceOriginRegistry(
    HerbSpiceAliasRegistry[HerbSpiceOrigin]
):
    """Declarative Registry for Herb & Spice origins."""

    registry_id = HERB_SPICE_ORIGIN_REGISTRY_ID
    entry_class = HerbSpiceOrigin

    def build_entry(
        self,
        registry_key: str,
        raw_entry: Mapping[str, Any],
    ) -> HerbSpiceOrigin:
        known_fields = {
            "canonical_name",
            "aliases",
            "score",
            "premium",
            "description",
            "country_code",
            "country_name",
            "region_name",
        }

        return HerbSpiceOrigin(
            **self.common_fields(
                registry_key=registry_key,
                raw_entry=raw_entry,
                known_fields=known_fields,
            ),
            country_code=optional_string(
                raw_entry.get("country_code")
            ),
            country_name=optional_string(
                raw_entry.get("country_name")
            ),
            region_name=optional_string(
                raw_entry.get("region_name")
            ),
        )

    def match(
        self,
        text: str,
    ) -> HerbSpiceOriginMatch | None:
        raw_match = super().match(text)

        if raw_match is None:
            return None

        return self.convert_match(
            raw_match,
            HerbSpiceOriginMatch,
        )  # type: ignore[return-value]


__all__ = [
    "HERB_SPICE_ORIGIN_REGISTRY_ID",
    "HerbSpiceOrigin",
    "HerbSpiceOriginMatch",
    "HerbSpiceOriginRegistry",
]
