from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from app.services.food.knowledge.common.base_model import (
    RegistryMatch,
)
from app.services.food.knowledge.tea._registry_support import (
    TeaAliasRegistry,
    TeaRegistryEntry,
)


TEA_TYPE_REGISTRY_ID = "tea.types"


@dataclass(
    frozen=True,
    kw_only=True,
)
class TeaType(TeaRegistryEntry):
    """Canonical Tea type entry."""


@dataclass(
    frozen=True,
    kw_only=True,
)
class TeaTypeMatch(
    RegistryMatch[TeaType]
):
    """Typed alias match for a Tea type."""

    @property
    def tea_type(self) -> TeaType:
        return self.entry


class TeaTypeRegistry(
    TeaAliasRegistry[TeaType]
):
    """Declarative Registry for canonical Tea types."""

    registry_id = TEA_TYPE_REGISTRY_ID
    entry_class = TeaType

    def build_entry(
        self,
        registry_key: str,
        raw_entry: Mapping[str, Any],
    ) -> TeaType:
        known_fields = {
            "canonical_name",
            "aliases",
            "score",
            "premium",
            "description",
        }

        return TeaType(
            **self.common_fields(
                registry_key=registry_key,
                raw_entry=raw_entry,
                known_fields=known_fields,
            )
        )

    def match(
        self,
        text: str,
    ) -> TeaTypeMatch | None:
        raw_match = super().match(text)

        if raw_match is None:
            return None

        return self.convert_match(
            raw_match,
            TeaTypeMatch,
        )  # type: ignore[return-value]


__all__ = [
    "TEA_TYPE_REGISTRY_ID",
    "TeaType",
    "TeaTypeMatch",
    "TeaTypeRegistry",
]
