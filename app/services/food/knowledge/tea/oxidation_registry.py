from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from app.services.food.knowledge.common.base_model import (
    RegistryMatch,
)
from app.services.food.knowledge.common.base_registry import (
    safe_float,
)
from app.services.food.knowledge.tea._registry_support import (
    TeaAliasRegistry,
    TeaRegistryEntry,
)


TEA_OXIDATION_REGISTRY_ID = "tea.oxidations"


@dataclass(
    frozen=True,
    kw_only=True,
)
class TeaOxidation(TeaRegistryEntry):
    """Canonical Tea oxidation classification."""

    oxidation_level: int = 0
    oxidation_min_percent: float = 0.0
    oxidation_max_percent: float = 0.0
    fully_oxidized: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()

        level = max(
            0,
            min(
                4,
                int(self.oxidation_level),
            ),
        )
        minimum = max(
            0.0,
            min(
                100.0,
                float(self.oxidation_min_percent),
            ),
        )
        maximum = max(
            minimum,
            min(
                100.0,
                float(self.oxidation_max_percent),
            ),
        )

        object.__setattr__(
            self,
            "oxidation_level",
            level,
        )
        object.__setattr__(
            self,
            "oxidation_min_percent",
            minimum,
        )
        object.__setattr__(
            self,
            "oxidation_max_percent",
            maximum,
        )
        object.__setattr__(
            self,
            "fully_oxidized",
            bool(self.fully_oxidized),
        )


@dataclass(
    frozen=True,
    kw_only=True,
)
class TeaOxidationMatch(
    RegistryMatch[TeaOxidation]
):
    """Typed alias match for a Tea oxidation class."""

    @property
    def tea_oxidation(self) -> TeaOxidation:
        return self.entry


class TeaOxidationRegistry(
    TeaAliasRegistry[TeaOxidation]
):
    """Declarative Registry for Tea oxidation levels."""

    registry_id = TEA_OXIDATION_REGISTRY_ID
    entry_class = TeaOxidation

    def build_entry(
        self,
        registry_key: str,
        raw_entry: Mapping[str, Any],
    ) -> TeaOxidation:
        known_fields = {
            "canonical_name",
            "aliases",
            "score",
            "premium",
            "description",
            "oxidation_level",
            "oxidation_min_percent",
            "oxidation_max_percent",
            "fully_oxidized",
        }

        return TeaOxidation(
            **self.common_fields(
                registry_key=registry_key,
                raw_entry=raw_entry,
                known_fields=known_fields,
            ),
            oxidation_level=int(
                safe_float(
                    raw_entry.get("oxidation_level"),
                    default=0.0,
                )
            ),
            oxidation_min_percent=safe_float(
                raw_entry.get(
                    "oxidation_min_percent"
                ),
                default=0.0,
            ),
            oxidation_max_percent=safe_float(
                raw_entry.get(
                    "oxidation_max_percent"
                ),
                default=0.0,
            ),
            fully_oxidized=bool(
                raw_entry.get(
                    "fully_oxidized",
                    False,
                )
            ),
        )

    def match(
        self,
        text: str,
    ) -> TeaOxidationMatch | None:
        raw_match = super().match(text)

        if raw_match is None:
            return None

        return self.convert_match(
            raw_match,
            TeaOxidationMatch,
        )  # type: ignore[return-value]


__all__ = [
    "TEA_OXIDATION_REGISTRY_ID",
    "TeaOxidation",
    "TeaOxidationMatch",
    "TeaOxidationRegistry",
]
