from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from app.services.food.knowledge.common.base_model import RegistryMatch
from app.services.food.knowledge.common.base_registry import optional_string
from app.services.food.knowledge.wine._registry_support import (
    WineAliasRegistry,
    WineRegistryEntry,
)

REGISTRY_ID = "wine.grapes"


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
class WineGrape(WineRegistryEntry):
    color: str | None = None
    species: str | None = None
    aromatic: bool = False


@dataclass(frozen=True, kw_only=True)
class WineGrapeMatch(RegistryMatch[WineGrape]):
    @property
    def value(self) -> WineGrape:
        return self.entry


class WineGrapeRegistry(WineAliasRegistry[WineGrape]):
    registry_id = REGISTRY_ID
    entry_class = WineGrape

    def build_entry(
        self,
        registry_key: str,
        raw_entry: Mapping[str, Any],
    ) -> WineGrape:
        known_fields = {
            "canonical_name",
            "aliases",
            "score",
            "premium",
            "description",
            "color", "species", "aromatic",
        }

        return WineGrape(
            **self.common_fields(
                registry_key=registry_key,
                raw_entry=raw_entry,
                known_fields=known_fields,
            ),

            color=optional_string(raw_entry.get("color")),
            species=optional_string(raw_entry.get("species")),
            aromatic=bool(raw_entry.get("aromatic", False)),
        )

    def match(
        self,
        text: str,
    ) -> WineGrapeMatch | None:
        raw_match = super().match(text)

        if raw_match is None:
            return None

        return self.convert_match(
            raw_match,
            WineGrapeMatch,
        )  # type: ignore[return-value]
