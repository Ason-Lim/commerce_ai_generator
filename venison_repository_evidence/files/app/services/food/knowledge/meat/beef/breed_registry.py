from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Mapping

from app.services.food.knowledge.common.base_registry import (
    AliasCandidate,
    AliasMatch,
    BaseAliasRegistry,
    DomainRegistryEntryNotFoundError,
    normalize_string_list,
    optional_float,
    optional_string,
    safe_float,
)
from app.services.food.knowledge.registry_loader import (
    KnowledgeRegistryLoader,
    get_knowledge_registry_loader,
)


BEEF_BREED_REGISTRY_ID = "beef.breeds"


@dataclass(frozen=True)
class BeefBreed:
    """표준화된 쇠고기 품종 정보."""

    registry_key: str
    canonical_name: str
    aliases: tuple[str, ...]
    score: float
    premium: bool

    english_name: str | None = None
    origin_country: str | None = None
    breed_type: str | None = None
    description: str | None = None

    marbling_score: float | None = None
    flavor_score: float | None = None
    tenderness_score: float | None = None
    rarity_score: float | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "registry_key": self.registry_key,
            "canonical_name": self.canonical_name,
            "aliases": list(self.aliases),
            "score": self.score,
            "premium": self.premium,
            "english_name": self.english_name,
            "origin_country": self.origin_country,
            "breed_type": self.breed_type,
            "description": self.description,
            "marbling_score": self.marbling_score,
            "flavor_score": self.flavor_score,
            "tenderness_score": (
                self.tenderness_score
            ),
            "rarity_score": self.rarity_score,
            "metadata": copy.deepcopy(
                self.metadata
            ),
        }


@dataclass(frozen=True)
class BeefBreedMatch:
    """상품명에서 탐지된 쇠고기 품종 결과."""

    breed: BeefBreed
    matched_alias: str
    normalized_alias: str
    match_start: int
    match_end: int
    confidence: float
    exact_match: bool

    @property
    def registry_key(self) -> str:
        return self.breed.registry_key

    @property
    def canonical_name(self) -> str:
        return self.breed.canonical_name

    def to_dict(self) -> dict[str, Any]:
        payload = self.breed.to_dict()

        payload.update(
            {
                "matched_alias": self.matched_alias,
                "normalized_alias": (
                    self.normalized_alias
                ),
                "match_start": self.match_start,
                "match_end": self.match_end,
                "confidence": self.confidence,
                "exact_match": self.exact_match,
            }
        )

        return payload


class BeefBreedRegistry(
    BaseAliasRegistry[BeefBreed]
):
    """YAML 기반 쇠고기 품종 Registry."""

    registry_id = BEEF_BREED_REGISTRY_ID
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
    ) -> BeefBreed:
        known_fields = {
            "canonical_name",
            "aliases",
            "score",
            "premium",
            "english_name",
            "origin_country",
            "breed_type",
            "description",
            "marbling",
            "marbling_score",
            "flavor",
            "flavor_score",
            "tenderness",
            "tenderness_score",
            "rarity",
            "rarity_score",
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

        return BeefBreed(
            registry_key=registry_key,
            canonical_name=(
                canonical_name or registry_key
            ),
            aliases=self._build_entry_aliases(
                canonical_name=canonical_name,
                raw_aliases=raw_entry.get(
                    "aliases"
                ),
            ),
            score=safe_float(
                raw_entry.get("score"),
                default=0.0,
            ),
            premium=bool(
                raw_entry.get(
                    "premium",
                    False,
                )
            ),
            english_name=optional_string(
                raw_entry.get("english_name")
            ),
            origin_country=optional_string(
                raw_entry.get("origin_country")
            ),
            breed_type=optional_string(
                raw_entry.get("breed_type")
            ),
            description=optional_string(
                raw_entry.get("description")
            ),
            marbling_score=self._first_float(
                raw_entry,
                "marbling_score",
                "marbling",
            ),
            flavor_score=self._first_float(
                raw_entry,
                "flavor_score",
                "flavor",
            ),
            tenderness_score=self._first_float(
                raw_entry,
                "tenderness_score",
                "tenderness",
            ),
            rarity_score=self._first_float(
                raw_entry,
                "rarity_score",
                "rarity",
            ),
            metadata=metadata,
        )

    def match(
        self,
        text: str,
    ) -> BeefBreedMatch | None:
        base_match = super().match(text)

        if base_match is None:
            return None

        return self._convert_match(base_match)

    def find_all(
        self,
        text: str,
    ) -> list[BeefBreedMatch]:
        return [
            self._convert_match(match)
            for match in super().find_all(text)
        ]

    def lookup(
        self,
        query: str,
        *,
        required: bool = False,
    ) -> BeefBreed | None:
        match = self.match(query)

        if match is not None:
            return match.breed

        if required:
            raise DomainRegistryEntryNotFoundError(
                f"{self.registry_id}: no breed "
                f"match for {query!r}"
            )

        return None

    def list(
        self,
        *,
        premium_only: bool = False,
    ) -> list[BeefBreed]:
        breeds = super().list()

        if premium_only:
            breeds = [
                breed
                for breed in breeds
                if breed.premium
            ]

        return sorted(
            breeds,
            key=lambda breed: (
                -breed.score,
                breed.canonical_name,
            ),
        )

    def premium_breeds(
        self,
    ) -> list[BeefBreed]:
        return self.list(
            premium_only=True
        )

    @staticmethod
    def _convert_match(
        match: AliasMatch[BeefBreed],
    ) -> BeefBreedMatch:
        return BeefBreedMatch(
            breed=match.entry,
            matched_alias=match.matched_alias,
            normalized_alias=(
                match.normalized_alias
            ),
            match_start=match.match_start,
            match_end=match.match_end,
            confidence=match.confidence,
            exact_match=match.exact_match,
        )

    def _build_entry_aliases(
        self,
        *,
        canonical_name: str,
        raw_aliases: Any,
    ) -> tuple[str, ...]:
        values: list[Any] = [
            canonical_name,
        ]

        values.extend(
            normalize_string_list(
                raw_aliases
            )
        )

        result: list[str] = []
        seen: set[str] = set()

        for value in values:
            alias = str(value).strip()

            if not alias:
                continue

            normalized = self.normalize_text(
                alias
            )

            if (
                not normalized
                or normalized in seen
            ):
                continue

            seen.add(normalized)
            result.append(alias)

        return tuple(result)

    @staticmethod
    def _first_float(
        raw_entry: Mapping[str, Any],
        *keys: str,
    ) -> float | None:
        for key in keys:
            value = optional_float(
                raw_entry.get(key)
            )

            if value is not None:
                return value

        return None


_default_beef_breed_registry = (
    BeefBreedRegistry()
)


def get_beef_breed_registry(
) -> BeefBreedRegistry:
    return _default_beef_breed_registry


def get_beef_breed(
    registry_key: str,
    *,
    required: bool = False,
) -> BeefBreed | None:
    return get_beef_breed_registry().get(
        registry_key,
        required=required,
    )


def lookup_beef_breed(
    query: str,
    *,
    required: bool = False,
) -> BeefBreed | None:
    return get_beef_breed_registry().lookup(
        query,
        required=required,
    )


def match_beef_breed(
    text: str,
) -> BeefBreedMatch | None:
    return get_beef_breed_registry().match(
        text
    )


def list_beef_breeds(
    *,
    premium_only: bool = False,
) -> list[BeefBreed]:
    return get_beef_breed_registry().list(
        premium_only=premium_only
    )


__all__ = [
    "BEEF_BREED_REGISTRY_ID",
    "BeefBreed",
    "BeefBreedMatch",
    "BeefBreedRegistry",
    "get_beef_breed_registry",
    "get_beef_breed",
    "lookup_beef_breed",
    "match_beef_breed",
    "list_beef_breeds",
]
