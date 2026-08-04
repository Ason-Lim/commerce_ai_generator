from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from app.services.food.knowledge.common.base_model import (
    RegistryMatch,
)
from app.services.food.knowledge.common.base_registry import (
    optional_string,
)
from app.services.food.knowledge.wine._registry_support import (
    WineAliasRegistry,
    WineRegistryEntry,
)


WINE_TYPE_REGISTRY_ID = "wine.types"


@dataclass(
    frozen=True,
    kw_only=True,
)
class WineType(WineRegistryEntry):
    type_category: str | None = None
    color_family: str | None = None
    sparkling: bool = False
    fortified: bool = False


@dataclass(
    frozen=True,
    kw_only=True,
)
class WineTypeMatch(
    RegistryMatch[WineType]
):
    @property
    def wine_type(self) -> WineType:
        return self.entry


class WineTypeRegistry(
    WineAliasRegistry[WineType]
):
    registry_id = WINE_TYPE_REGISTRY_ID
    entry_class = WineType

    def build_entry(
        self,
        registry_key: str,
        raw_entry: Mapping[str, Any],
    ) -> WineType:
        known_fields = {
            "canonical_name",
            "aliases",
            "score",
            "premium",
            "description",
            "type_category",
            "color_family",
            "sparkling",
            "fortified",
        }

        return WineType(
            **self.common_fields(
                registry_key=registry_key,
                raw_entry=raw_entry,
                known_fields=known_fields,
            ),
            type_category=optional_string(
                raw_entry.get("type_category")
            ),
            color_family=optional_string(
                raw_entry.get("color_family")
            ),
            sparkling=bool(
                raw_entry.get("sparkling", False)
            ),
            fortified=bool(
                raw_entry.get("fortified", False)
            ),
        )

    def match(
        self,
        text: str,
    ) -> WineTypeMatch | None:
        raw_match = super().match(text)

        if raw_match is None:
            return None

        return self.convert_match(
            raw_match,
            WineTypeMatch,
        )  # type: ignore[return-value]