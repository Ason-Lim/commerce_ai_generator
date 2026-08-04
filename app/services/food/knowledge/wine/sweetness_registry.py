from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from app.services.food.knowledge.common.base_model import RegistryMatch
from app.services.food.knowledge.common.base_registry import optional_string
from app.services.food.knowledge.wine._registry_support import (
    WineAliasRegistry,
    WineRegistryEntry,
)

REGISTRY_ID = "wine.sweetness"


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
class WineSweetness(WineRegistryEntry):
    sweetness_level: int | None = None
    residual_sugar_min: float | None = None
    residual_sugar_max: float | None = None


@dataclass(frozen=True, kw_only=True)
class WineSweetnessMatch(RegistryMatch[WineSweetness]):
    @property
    def value(self) -> WineSweetness:
        return self.entry


class WineSweetnessRegistry(WineAliasRegistry[WineSweetness]):
    registry_id = REGISTRY_ID
    entry_class = WineSweetness

    def build_entry(
        self,
        registry_key: str,
        raw_entry: Mapping[str, Any],
    ) -> WineSweetness:
        known_fields = {
            "canonical_name",
            "aliases",
            "score",
            "premium",
            "description",
            "sweetness_level", "residual_sugar_min", "residual_sugar_max",
        }

        return WineSweetness(
            **self.common_fields(
                registry_key=registry_key,
                raw_entry=raw_entry,
                known_fields=known_fields,
            ),

            sweetness_level=_optional_int(raw_entry.get("sweetness_level")),
            residual_sugar_min=_optional_float(raw_entry.get("residual_sugar_min")),
            residual_sugar_max=_optional_float(raw_entry.get("residual_sugar_max")),
        )

    def match(
        self,
        text: str,
    ) -> WineSweetnessMatch | None:
        raw_match = super().match(text)

        if raw_match is None:
            return None

        return self.convert_match(
            raw_match,
            WineSweetnessMatch,
        )  # type: ignore[return-value]
