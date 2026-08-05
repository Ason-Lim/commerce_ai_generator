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


OLIVE_OIL_PROCESSING_REGISTRY_ID = "olive_oil.processes"


@dataclass(
    frozen=True,
    kw_only=True,
)
class OliveOilProcessing(OliveOilRegistryEntry):
    """Canonical Olive Oil processing method."""

    process_category: str | None = None
    mechanical_only: bool = False
    cold_extracted: bool = False
    refined: bool = False


@dataclass(
    frozen=True,
    kw_only=True,
)
class OliveOilProcessingMatch(
    RegistryMatch[OliveOilProcessing]
):
    @property
    def olive_oil_processing(self) -> OliveOilProcessing:
        return self.entry


class OliveOilProcessingRegistry(
    OliveOilAliasRegistry[OliveOilProcessing]
):
    registry_id = OLIVE_OIL_PROCESSING_REGISTRY_ID
    entry_class = OliveOilProcessing

    def build_entry(
        self,
        registry_key: str,
        raw_entry: Mapping[str, Any],
    ) -> OliveOilProcessing:
        known_fields = {
            "canonical_name",
            "aliases",
            "score",
            "premium",
            "description",
            "process_category",
            "mechanical_only",
            "cold_extracted",
            "refined",
        }

        return OliveOilProcessing(
            **self.common_fields(
                registry_key=registry_key,
                raw_entry=raw_entry,
                known_fields=known_fields,
            ),
            process_category=optional_string(
                raw_entry.get("process_category")
            ),
            mechanical_only=bool(
                raw_entry.get("mechanical_only", False)
            ),
            cold_extracted=bool(
                raw_entry.get("cold_extracted", False)
            ),
            refined=bool(
                raw_entry.get("refined", False)
            ),
        )

    def match(
        self,
        text: str,
    ) -> OliveOilProcessingMatch | None:
        raw_match = super().match(text)

        if raw_match is None:
            return None

        return self.convert_match(
            raw_match,
            OliveOilProcessingMatch,
        )  # type: ignore[return-value]


__all__ = [
    "OLIVE_OIL_PROCESSING_REGISTRY_ID",
    "OliveOilProcessing",
    "OliveOilProcessingMatch",
    "OliveOilProcessingRegistry",
]
