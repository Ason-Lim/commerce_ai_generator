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


TEA_ORIGIN_REGISTRY_ID = "tea.origins"


@dataclass(
    frozen=True,
    kw_only=True,
)
class TeaOrigin(TeaRegistryEntry):
    """Canonical Tea-producing origin."""

    country_code: str | None = None
    country_name: str | None = None
    region_name: str | None = None


@dataclass(
    frozen=True,
    kw_only=True,
)
class TeaOriginMatch(
    RegistryMatch[TeaOrigin]
):
    """Typed alias match for a Tea origin."""

    @property
    def tea_origin(self) -> TeaOrigin:
        return self.entry


class TeaOriginRegistry(
    TeaAliasRegistry[TeaOrigin]
):
    """Declarative Registry for Tea-producing origins."""

    registry_id = TEA_ORIGIN_REGISTRY_ID
    entry_class = TeaOrigin

    def build_entry(
        self,
        registry_key: str,
        raw_entry: Mapping[str, Any],
    ) -> TeaOrigin:
        known_fields = {
            "canonical_name",
            "aliases",
            "score",
            "premium",
            "description",
            "country_code",
            "country_name",
            "region_name",
        }

        return TeaOrigin(
            **self.common_fields(
                registry_key=registry_key,
                raw_entry=raw_entry,
                known_fields=known_fields,
            ),
            country_code=optional_string(
                raw_entry.get("country_code")
            ),
            country_name=optional_string(
                raw_entry.get("country_name")
            ),
            region_name=optional_string(
                raw_entry.get("region_name")
            ),
        )

    def match(
        self,
        text: str,
    ) -> TeaOriginMatch | None:
        raw_match = super().match(text)

        if raw_match is None:
            return None

        return self.convert_match(
            raw_match,
            TeaOriginMatch,
        )  # type: ignore[return-value]


__all__ = [
    "TEA_ORIGIN_REGISTRY_ID",
    "TeaOrigin",
    "TeaOriginMatch",
    "TeaOriginRegistry",
]
