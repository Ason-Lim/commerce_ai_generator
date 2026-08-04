from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from app.services.food.knowledge.coffee._registry_support import (
    CoffeeAliasRegistry,
    build_aliases,
    convert_match,
    extra_metadata,
    optional_score,
    optional_text,
    required_score,
)
from app.services.food.knowledge.common.base_model import (
    RegistryEntry,
    RegistryMatch,
)
from app.services.food.knowledge.common.base_registry import (
    AliasMatch,
)
from app.services.food.knowledge.registry_loader import (
    KnowledgeRegistryLoader,
    get_knowledge_registry_loader,
)


COFFEE_ORIGIN_REGISTRY_ID = "coffee.origins"


@dataclass(frozen=True, kw_only=True)
class CoffeeOrigin(RegistryEntry):
    canonical_name: str
    aliases: tuple[str, ...]
    country_code: str | None
    score: float
    premium: bool
    acidity_score: float | None
    body_score: float | None
    aroma_score: float | None
    description: str | None

    def __post_init__(self) -> None:
        super().__post_init__()

        canonical_name = str(
            self.canonical_name
        ).strip()

        if not canonical_name:
            raise ValueError(
                "canonical_name must not be empty"
            )

        object.__setattr__(
            self,
            "canonical_name",
            canonical_name,
        )
        object.__setattr__(
            self,
            "aliases",
            tuple(self.aliases),
        )
        object.__setattr__(
            self,
            "score",
            required_score(self.score),
        )
        object.__setattr__(
            self,
            "premium",
            bool(self.premium),
        )

        country_code = optional_text(
            self.country_code
        )

        object.__setattr__(
            self,
            "country_code",
            (
                country_code.upper()
                if country_code
                else None
            ),
        )


@dataclass(frozen=True, kw_only=True)
class CoffeeOriginMatch(
    RegistryMatch[CoffeeOrigin]
):
    @property
    def origin(self) -> CoffeeOrigin:
        return self.entry


class CoffeeOriginRegistry(
    CoffeeAliasRegistry[CoffeeOrigin]
):
    registry_id = COFFEE_ORIGIN_REGISTRY_ID
    canonical_name_field = "canonical_name"
    aliases_field = "aliases"

    def __init__(
        self,
        loader: KnowledgeRegistryLoader | None = None,
    ) -> None:
        super().__init__(
            loader=(
                loader
                or get_knowledge_registry_loader()
            )
        )

    def build_entry(
        self,
        registry_key: str,
        raw_entry: Mapping[str, Any],
    ) -> CoffeeOrigin:
        known_fields = {
            "canonical_name",
            "aliases",
            "country_code",
            "score",
            "premium",
            "acidity_score",
            "body_score",
            "aroma_score",
            "description",
        }

        canonical_name = str(
            raw_entry.get(
                "canonical_name",
                registry_key,
            )
        ).strip()

        return CoffeeOrigin(
            registry_key=registry_key,
            canonical_name=(
                canonical_name or registry_key
            ),
            aliases=build_aliases(
                canonical_name,
                raw_entry.get("aliases"),
            ),
            country_code=optional_text(
                raw_entry.get("country_code")
            ),
            score=required_score(
                raw_entry.get("score")
            ),
            premium=bool(
                raw_entry.get(
                    "premium",
                    False,
                )
            ),
            acidity_score=optional_score(
                raw_entry.get(
                    "acidity_score"
                )
            ),
            body_score=optional_score(
                raw_entry.get("body_score")
            ),
            aroma_score=optional_score(
                raw_entry.get("aroma_score")
            ),
            description=optional_text(
                raw_entry.get("description")
            ),
            metadata=extra_metadata(
                raw_entry,
                known_fields,
            ),
        )

    def match(
        self,
        text: str,
    ) -> CoffeeOriginMatch | None:
        raw_match = super().match(text)

        if raw_match is None:
            return None

        return self._convert(raw_match)

    def find_all(
        self,
        text: str,
    ) -> list[CoffeeOriginMatch]:
        return [
            self._convert(match)
            for match in super().find_all(text)
        ]

    def list(
        self,
        *,
        premium_only: bool = False,
    ) -> list[CoffeeOrigin]:
        return self.typed_entries(
            CoffeeOrigin,
            premium_only=premium_only,
        )

    @staticmethod
    def _convert(
        raw_match: AliasMatch[CoffeeOrigin],
    ) -> CoffeeOriginMatch:
        return convert_match(
            raw_match,
            CoffeeOriginMatch,
        )  # type: ignore[return-value]


__all__ = [
    "COFFEE_ORIGIN_REGISTRY_ID",
    "CoffeeOrigin",
    "CoffeeOriginMatch",
    "CoffeeOriginRegistry",
]
