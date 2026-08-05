from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from app.services.food.knowledge.common.base_model import (
    RegistryMatch,
)
from app.services.food.knowledge.olive_oil._registry_support import (
    OliveOilAliasRegistry,
    OliveOilRegistryEntry,
)


OLIVE_OIL_TYPE_REGISTRY_ID = "olive_oil.types"


@dataclass(
    frozen=True,
    kw_only=True,
)
class OliveOilType(OliveOilRegistryEntry):
    """Canonical Olive Oil product type."""


@dataclass(
    frozen=True,
    kw_only=True,
)
class OliveOilTypeMatch(
    RegistryMatch[OliveOilType]
):
    """Typed match for an Olive Oil product type."""

    @property
    def olive_oil_type(self) -> OliveOilType:
        return self.entry


class OliveOilTypeRegistry(
    OliveOilAliasRegistry[OliveOilType]
):
    """Declarative Registry for Olive Oil product types."""

    registry_id = OLIVE_OIL_TYPE_REGISTRY_ID
    entry_class = OliveOilType

    def build_entry(
        self,
        registry_key: str,
        raw_entry: Mapping[str, Any],
    ) -> OliveOilType:
        known_fields = {
            "canonical_name",
            "aliases",
            "score",
            "premium",
            "description",
        }

        return OliveOilType(
            **self.common_fields(
                registry_key=registry_key,
                raw_entry=raw_entry,
                known_fields=known_fields,
            )
        )

    def match(
        self,
        text: str,
    ) -> OliveOilTypeMatch | None:
        """
        구체적인 Olive Oil Type을 일반 olive_oil보다 우선한다.

        olive_oil은 다른 구체 Type이 감지되지 않을 때만
        fallback으로 사용한다.
        """
        matches = self.find_all(text)

        if not matches:
            return None

        for match in matches:
            if match.registry_key != "olive_oil":
                return self.convert_match(
                    match,
                    OliveOilTypeMatch,
                )  # type: ignore[return-value]

        return self.convert_match(
            matches[0],
            OliveOilTypeMatch,
        )  # type: ignore[return-value]


__all__ = [
    "OLIVE_OIL_TYPE_REGISTRY_ID",
    "OliveOilType",
    "OliveOilTypeMatch",
    "OliveOilTypeRegistry",
]
