from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Mapping

from app.services.food.knowledge.common.base_model import (
    RegistryEntry,
    RegistryMatch,
)
from app.services.food.knowledge.common.base_registry import (
    AliasMatch,
    BaseAliasRegistry,
    normalize_string_list,
    optional_string,
    safe_float,
)
from app.services.food.knowledge.registry_loader import (
    KnowledgeRegistryLoader,
    get_knowledge_registry_loader,
)


CHEESE_MILK_SOURCE_REGISTRY_ID = "cheese.milk_sources"


def _aliases(
    canonical_name: str,
    raw_aliases: Any,
) -> tuple[str, ...]:
    values = [
        canonical_name,
        *normalize_string_list(raw_aliases),
    ]

    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        text = str(value).strip()
        key = text.casefold()

        if text and key not in seen:
            seen.add(key)
            result.append(text)

    return tuple(result)


def _optional_score(
    value: Any,
) -> float | None:
    if value is None:
        return None

    return max(
        0.0,
        min(
            100.0,
            safe_float(value, default=0.0),
        ),
    )


def _optional_int(
    value: Any,
) -> int | None:
    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@dataclass(
    frozen=True,
    kw_only=True,
)
class CheeseMilkSource(RegistryEntry):
    canonical_name: str
    aliases: tuple[str, ...]
    source_category: str | None
    score: float
    premium: bool
    richness_score: float | None
    availability_score: float | None
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
            tuple(
                str(value).strip()
                for value in self.aliases
                if str(value).strip()
            ),
        )

        object.__setattr__(
            self,
            "score",
            max(
                0.0,
                min(
                    100.0,
                    float(self.score),
                ),
            ),
        )

        object.__setattr__(
            self,
            "premium",
            bool(self.premium),
        )


@dataclass(
    frozen=True,
    kw_only=True,
)
class CheeseMilkSourceMatch(
    RegistryMatch[CheeseMilkSource]
):
    @property
    def milk_source(
        self,
    ) -> CheeseMilkSource:
        return self.entry


class CheeseMilkSourceRegistry(
    BaseAliasRegistry[CheeseMilkSource]
):
    registry_id = CHEESE_MILK_SOURCE_REGISTRY_ID
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
    ) -> CheeseMilkSource:
        known_fields = {
            "canonical_name",
            "aliases",
            "source_category",
            "score",
            "premium",
            "richness_score",
            "availability_score",
            "description",
        }

        metadata = {
            key: copy.deepcopy(value)
            for key, value in raw_entry.items()
            if key not in known_fields
        }

        canonical_name = str(
            raw_entry.get(
                "canonical_name",
                registry_key,
            )
        ).strip()

        return CheeseMilkSource(
            registry_key=registry_key,
            canonical_name=(
                canonical_name
                or registry_key
            ),
            aliases=_aliases(
                canonical_name,
                raw_entry.get("aliases"),
            ),
            source_category=optional_string(raw_entry.get("source_category")),
            score=safe_float(raw_entry.get("score"), default=0.0),
            premium=bool(raw_entry.get("premium", False)),
            richness_score=_optional_score(raw_entry.get("richness_score")),
            availability_score=_optional_score(raw_entry.get("availability_score")),
            description=optional_string(raw_entry.get("description")),
            metadata=metadata,
        )

    def match(
        self,
        text: str,
    ) -> CheeseMilkSourceMatch | None:
        raw_match = super().match(text)

        if raw_match is None:
            return None

        return self._convert_match(
            raw_match
        )

    def find_all(
        self,
        text: str,
    ) -> list[CheeseMilkSourceMatch]:
        return [
            self._convert_match(match)
            for match in super().find_all(text)
        ]

    def lookup(
        self,
        text: str,
    ) -> CheeseMilkSource | None:
        match = self.match(text)

        if match is None:
            return None

        return match.entry

    def list(
        self,
        *,
        premium_only: bool = False,
    ) -> list[CheeseMilkSource]:
        entries = [
            entry
            for entry in super().list()
            if isinstance(
                entry,
                CheeseMilkSource,
            )
        ]

        if premium_only:
            entries = [
                entry
                for entry in entries
                if entry.premium
            ]

        return sorted(
            entries,
            key=lambda entry: (
                -entry.score,
                entry.canonical_name,
            ),
        )

    @staticmethod
    def _convert_match(
        raw_match: AliasMatch[CheeseMilkSource],
    ) -> CheeseMilkSourceMatch:
        return CheeseMilkSourceMatch(
            entry=raw_match.entry,
            matched_alias=(
                raw_match.matched_alias
            ),
            normalized_alias=(
                raw_match.normalized_alias
            ),
            match_start=raw_match.match_start,
            match_end=raw_match.match_end,
            confidence=raw_match.confidence,
            exact_match=raw_match.exact_match,
        )


__all__ = [
    "CHEESE_MILK_SOURCE_REGISTRY_ID",
    "CheeseMilkSource",
    "CheeseMilkSourceMatch",
    "CheeseMilkSourceRegistry",
]
