from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from app.services.food.knowledge.common.base_model import (
    RegistryMatch,
)
from app.services.food.knowledge.common.base_registry import (
    optional_string,
)
from app.services.food.knowledge.tea._registry_support import (
    TeaAliasRegistry,
    TeaRegistryEntry,
)


TEA_VARIETY_REGISTRY_ID = "tea.varieties"


@dataclass(
    frozen=True,
    kw_only=True,
)
class TeaVariety(TeaRegistryEntry):
    """Canonical botanical variety or Tea cultivar."""

    botanical_name: str | None = None
    variety_kind: str | None = None
    country_code: str | None = None


@dataclass(
    frozen=True,
    kw_only=True,
)
class TeaVarietyMatch(
    RegistryMatch[TeaVariety]
):
    """Typed alias match for a Tea variety."""

    @property
    def tea_variety(self) -> TeaVariety:
        return self.entry


class TeaVarietyRegistry(
    TeaAliasRegistry[TeaVariety]
):
    """Declarative Registry for Tea varieties and cultivars."""

    registry_id = TEA_VARIETY_REGISTRY_ID
    entry_class = TeaVariety

    def build_entry(
        self,
        registry_key: str,
        raw_entry: Mapping[str, Any],
    ) -> TeaVariety:
        known_fields = {
            "canonical_name",
            "aliases",
            "score",
            "premium",
            "description",
            "botanical_name",
            "variety_kind",
            "country_code",
        }

        return TeaVariety(
            **self.common_fields(
                registry_key=registry_key,
                raw_entry=raw_entry,
                known_fields=known_fields,
            ),
            botanical_name=optional_string(
                raw_entry.get("botanical_name")
            ),
            variety_kind=optional_string(
                raw_entry.get("variety_kind")
            ),
            country_code=optional_string(
                raw_entry.get("country_code")
            ),
        )

    def match(
        self,
        text: str,
    ) -> TeaVarietyMatch | None:
        raw_match = super().match(text)

        if raw_match is None:
            return None

        return self.convert_match(
            raw_match,
            TeaVarietyMatch,
        )  # type: ignore[return-value]


__all__ = [
    "TEA_VARIETY_REGISTRY_ID",
    "TeaVariety",
    "TeaVarietyMatch",
    "TeaVarietyRegistry",
]
