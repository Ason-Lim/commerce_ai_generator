from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from app.services.food.knowledge.common.base_model import RegistryMatch
from app.services.food.knowledge.common.base_registry import optional_string
from app.services.food.knowledge.wine._registry_support import (
    WineAliasRegistry,
    WineRegistryEntry,
)

REGISTRY_ID = "wine.acidity"


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
class WineAcidity(WineRegistryEntry):
    acidity_level: int | None = None


@dataclass(frozen=True, kw_only=True)
class WineAcidityMatch(RegistryMatch[WineAcidity]):
    @property
    def value(self) -> WineAcidity:
        return self.entry


class WineAcidityRegistry(WineAliasRegistry[WineAcidity]):
    registry_id = REGISTRY_ID
    entry_class = WineAcidity

    def build_entry(
        self,
        registry_key: str,
        raw_entry: Mapping[str, Any],
    ) -> WineAcidity:
        known_fields = {
            "canonical_name",
            "aliases",
            "score",
            "premium",
            "description",
            "acidity_level",
        }

        return WineAcidity(
            **self.common_fields(
                registry_key=registry_key,
                raw_entry=raw_entry,
                known_fields=known_fields,
            ),

            acidity_level=_optional_int(raw_entry.get("acidity_level")),
        )

    def match(
        self,
        text: str,
    ) -> WineAcidityMatch | None:
        raw_match = super().match(text)

        if raw_match is None:
            return None

        return self.convert_match(
            raw_match,
            WineAcidityMatch,
        )  # type: ignore[return-value]
