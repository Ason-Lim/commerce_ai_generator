from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from app.services.food.knowledge.common.base_model import RegistryMatch
from app.services.food.knowledge.common.base_registry import optional_string
from app.services.food.knowledge.wine._registry_support import (
    WineAliasRegistry,
    WineRegistryEntry,
)

REGISTRY_ID = "wine.regions"


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True, kw_only=True)
class WineRegion(WineRegistryEntry):
    country_code: str | None = None
    country_name: str | None = None
    appellation: str | None = None


@dataclass(frozen=True, kw_only=True)
class WineRegionMatch(RegistryMatch[WineRegion]):
    @property
    def value(self) -> WineRegion:
        return self.entry


class WineRegionRegistry(WineAliasRegistry[WineRegion]):
    registry_id = REGISTRY_ID
    entry_class = WineRegion

    def build_entry(
        self,
        registry_key: str,
        raw_entry: Mapping[str, Any],
    ) -> WineRegion:
        known_fields = {
            "canonical_name",
            "aliases",
            "score",
            "premium",
            "description",
            "country_code", "country_name", "appellation",
        }

        return WineRegion(
            **self.common_fields(
                registry_key=registry_key,
                raw_entry=raw_entry,
                known_fields=known_fields,
            ),

            country_code=optional_string(raw_entry.get("country_code")),
            country_name=optional_string(raw_entry.get("country_name")),
            appellation=optional_string(raw_entry.get("appellation")),
        )

    def match(
        self,
        text: str,
    ) -> WineRegionMatch | None:
        raw_match = super().match(text)

        if raw_match is None:
            return None

        return self.convert_match(
            raw_match,
            WineRegionMatch,
        )  # type: ignore[return-value]
