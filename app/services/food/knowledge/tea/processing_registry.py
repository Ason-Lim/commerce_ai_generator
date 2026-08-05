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


TEA_PROCESSING_REGISTRY_ID = "tea.processes"


@dataclass(
    frozen=True,
    kw_only=True,
)
class TeaProcessing(TeaRegistryEntry):
    """Canonical Tea processing method."""

    process_category: str | None = None
    heat_fixation: bool = False
    microbial_fermentation: bool = False
    smoke_applied: bool = False


@dataclass(
    frozen=True,
    kw_only=True,
)
class TeaProcessingMatch(
    RegistryMatch[TeaProcessing]
):
    """Typed alias match for a Tea processing method."""

    @property
    def tea_processing(self) -> TeaProcessing:
        return self.entry


class TeaProcessingRegistry(
    TeaAliasRegistry[TeaProcessing]
):
    """Declarative Registry for Tea processing methods."""

    registry_id = TEA_PROCESSING_REGISTRY_ID
    entry_class = TeaProcessing

    def build_entry(
        self,
        registry_key: str,
        raw_entry: Mapping[str, Any],
    ) -> TeaProcessing:
        known_fields = {
            "canonical_name",
            "aliases",
            "score",
            "premium",
            "description",
            "process_category",
            "heat_fixation",
            "microbial_fermentation",
            "smoke_applied",
        }

        return TeaProcessing(
            **self.common_fields(
                registry_key=registry_key,
                raw_entry=raw_entry,
                known_fields=known_fields,
            ),
            process_category=optional_string(
                raw_entry.get("process_category")
            ),
            heat_fixation=bool(
                raw_entry.get("heat_fixation", False)
            ),
            microbial_fermentation=bool(
                raw_entry.get(
                    "microbial_fermentation",
                    False,
                )
            ),
            smoke_applied=bool(
                raw_entry.get("smoke_applied", False)
            ),
        )

    def match(
        self,
        text: str,
    ) -> TeaProcessingMatch | None:
        raw_match = super().match(text)

        if raw_match is None:
            return None

        return self.convert_match(
            raw_match,
            TeaProcessingMatch,
        )  # type: ignore[return-value]


__all__ = [
    "TEA_PROCESSING_REGISTRY_ID",
    "TeaProcessing",
    "TeaProcessingMatch",
    "TeaProcessingRegistry",
]
