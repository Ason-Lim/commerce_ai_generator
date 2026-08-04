from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from app.services.food.knowledge.common.base_model import RegistryMatch
from app.services.food.knowledge.common.base_registry import optional_string
from app.services.food.knowledge.wine._registry_support import (
    WineAliasRegistry,
    WineRegistryEntry,
)

REGISTRY_ID = "wine.bodies"


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
class WineBody(WineRegistryEntry):
    body_level: int | None = None


@dataclass(frozen=True, kw_only=True)
class WineBodyMatch(RegistryMatch[WineBody]):
    @property
    def value(self) -> WineBody:
        return self.entry


class WineBodyRegistry(WineAliasRegistry[WineBody]):
    registry_id = REGISTRY_ID
    entry_class = WineBody

    def build_entry(
        self,
        registry_key: str,
        raw_entry: Mapping[str, Any],
    ) -> WineBody:
        known_fields = {
            "canonical_name",
            "aliases",
            "score",
            "premium",
            "description",
            "body_level",
        }

        return WineBody(
            **self.common_fields(
                registry_key=registry_key,
                raw_entry=raw_entry,
                known_fields=known_fields,
            ),

            body_level=_optional_int(raw_entry.get("body_level")),
        )

    def match(
        self,
        text: str,
    ) -> WineBodyMatch | None:
        raw_match = super().match(text)

        if raw_match is None:
            return None

        return self.convert_match(
            raw_match,
            WineBodyMatch,
        )  # type: ignore[return-value]
