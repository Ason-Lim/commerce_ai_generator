from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from app.services.food.knowledge.common.base_model import (
    RegistryMatch,
)
from app.services.food.knowledge.common.base_registry import (
    optional_string,
)
from app.services.food.knowledge.olive_oil._registry_support import (
    OliveOilAliasRegistry,
    OliveOilRegistryEntry,
)


OLIVE_OIL_VARIETY_REGISTRY_ID = "olive_oil.varieties"


@dataclass(
    frozen=True,
    kw_only=True,
)
class OliveOilVariety(OliveOilRegistryEntry):
    """Canonical olive cultivar entry."""

    cultivar_origin: str | None = None
    flavor_profile: str | None = None


@dataclass(
    frozen=True,
    kw_only=True,
)
class OliveOilVarietyMatch(
    RegistryMatch[OliveOilVariety]
):
    @property
    def olive_oil_variety(self) -> OliveOilVariety:
        return self.entry


class OliveOilVarietyRegistry(
    OliveOilAliasRegistry[OliveOilVariety]
):
    registry_id = OLIVE_OIL_VARIETY_REGISTRY_ID
    entry_class = OliveOilVariety

    def build_entry(
        self,
        registry_key: str,
        raw_entry: Mapping[str, Any],
    ) -> OliveOilVariety:
        known_fields = {
            "canonical_name",
            "aliases",
            "score",
            "premium",
            "description",
            "cultivar_origin",
            "flavor_profile",
        }

        return OliveOilVariety(
            **self.common_fields(
                registry_key=registry_key,
                raw_entry=raw_entry,
                known_fields=known_fields,
            ),
            cultivar_origin=optional_string(
                raw_entry.get("cultivar_origin")
            ),
            flavor_profile=optional_string(
                raw_entry.get("flavor_profile")
            ),
        )

    def match(
        self,
        text: str,
    ) -> OliveOilVarietyMatch | None:
        raw_match = super().match(text)

        if raw_match is None:
            return None

        return self.convert_match(
            raw_match,
            OliveOilVarietyMatch,
        )  # type: ignore[return-value]


__all__ = [
    "OLIVE_OIL_VARIETY_REGISTRY_ID",
    "OliveOilVariety",
    "OliveOilVarietyMatch",
    "OliveOilVarietyRegistry",
]
