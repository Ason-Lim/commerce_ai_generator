from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from app.services.food.knowledge.common.base_model import (
    RegistryMatch,
)
from app.services.food.knowledge.common.base_registry import (
    optional_string,
)
from app.services.food.knowledge.herb_spice._registry_support import (
    HerbSpiceAliasRegistry,
    HerbSpiceRegistryEntry,
)


HERB_SPICE_FORM_REGISTRY_ID = "herb_spice.forms"


@dataclass(
    frozen=True,
    kw_only=True,
)
class HerbSpiceForm(HerbSpiceRegistryEntry):
    """Canonical commercial form for herbs and spices."""

    form_category: str | None = None
    dried: bool = False
    ground: bool = False
    whole: bool = False
    fresh: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()

        object.__setattr__(
            self,
            "form_category",
            optional_string(
                self.form_category
            ),
        )
        object.__setattr__(
            self,
            "dried",
            bool(self.dried),
        )
        object.__setattr__(
            self,
            "ground",
            bool(self.ground),
        )
        object.__setattr__(
            self,
            "whole",
            bool(self.whole),
        )
        object.__setattr__(
            self,
            "fresh",
            bool(self.fresh),
        )


@dataclass(
    frozen=True,
    kw_only=True,
)
class HerbSpiceFormMatch(
    RegistryMatch[HerbSpiceForm]
):
    """Typed alias match for a Herb & Spice form."""

    @property
    def form(self) -> HerbSpiceForm:
        return self.entry


class HerbSpiceFormRegistry(
    HerbSpiceAliasRegistry[HerbSpiceForm]
):
    """Declarative Registry for Herb & Spice product forms."""

    registry_id = HERB_SPICE_FORM_REGISTRY_ID
    entry_class = HerbSpiceForm

    def build_entry(
        self,
        registry_key: str,
        raw_entry: Mapping[str, Any],
    ) -> HerbSpiceForm:
        known_fields = {
            "canonical_name",
            "aliases",
            "score",
            "premium",
            "description",
            "form_category",
            "dried",
            "ground",
            "whole",
            "fresh",
        }

        return HerbSpiceForm(
            **self.common_fields(
                registry_key=registry_key,
                raw_entry=raw_entry,
                known_fields=known_fields,
            ),
            form_category=optional_string(
                raw_entry.get("form_category")
            ),
            dried=bool(
                raw_entry.get("dried", False)
            ),
            ground=bool(
                raw_entry.get("ground", False)
            ),
            whole=bool(
                raw_entry.get("whole", False)
            ),
            fresh=bool(
                raw_entry.get("fresh", False)
            ),
        )

    def match(
        self,
        text: str,
    ) -> HerbSpiceFormMatch | None:
        raw_match = super().match(text)

        if raw_match is None:
            return None

        return self.convert_match(
            raw_match,
            HerbSpiceFormMatch,
        )  # type: ignore[return-value]


__all__ = [
    "HERB_SPICE_FORM_REGISTRY_ID",
    "HerbSpiceForm",
    "HerbSpiceFormMatch",
    "HerbSpiceFormRegistry",
]
