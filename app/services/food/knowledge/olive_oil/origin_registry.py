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


OLIVE_OIL_ORIGIN_REGISTRY_ID = "olive_oil.origins"


@dataclass(
    frozen=True,
    kw_only=True,
)
class OliveOilOrigin(OliveOilRegistryEntry):
    """Canonical Olive Oil origin entry."""

    country_code: str | None = None
    region: str | None = None


@dataclass(
    frozen=True,
    kw_only=True,
)
class OliveOilOriginMatch(
    RegistryMatch[OliveOilOrigin]
):
    @property
    def olive_oil_origin(self) -> OliveOilOrigin:
        return self.entry


class OliveOilOriginRegistry(
    OliveOilAliasRegistry[OliveOilOrigin]
):
    registry_id = OLIVE_OIL_ORIGIN_REGISTRY_ID
    entry_class = OliveOilOrigin

    def build_entry(
        self,
        registry_key: str,
        raw_entry: Mapping[str, Any],
    ) -> OliveOilOrigin:
        known_fields = {
            "canonical_name",
            "aliases",
            "score",
            "premium",
            "description",
            "country_code",
            "region",
        }

        return OliveOilOrigin(
            **self.common_fields(
                registry_key=registry_key,
                raw_entry=raw_entry,
                known_fields=known_fields,
            ),
            country_code=optional_string(
                raw_entry.get("country_code")
            ),
            region=optional_string(
                raw_entry.get("region")
            ),
        )

    def match(
        self,
        text: str,
    ) -> OliveOilOriginMatch | None:
        raw_match = super().match(text)

        if raw_match is None:
            return None

        return self.convert_match(
            raw_match,
            OliveOilOriginMatch,
        )  # type: ignore[return-value]


__all__ = [
    "OLIVE_OIL_ORIGIN_REGISTRY_ID",
    "OliveOilOrigin",
    "OliveOilOriginMatch",
    "OliveOilOriginRegistry",
]
