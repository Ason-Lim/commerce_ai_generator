from __future__ import annotations

import copy
from dataclasses import dataclass
from functools import lru_cache
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


LAMB_BREED_REGISTRY_ID = "lamb.breeds"


@dataclass(
    frozen=True,
    kw_only=True,
)
class LambBreed(
    RegistryEntry
):
    """
    양 품종 Registry 항목.

    score:
        품종의 일반적인 상품성 및 선호도 기준 점수.

    origin_country:
        품종의 대표 기원 국가 또는 지역.

    breed_type:
        육용, 모용, 겸용 등 품종 분류.

    flavor_score:
        풍미 특성 참고 점수.

    tenderness_score:
        연도 특성 참고 점수.

    rarity_score:
        희소성 참고 점수.
    """

    canonical_name: str
    aliases: tuple[str, ...]
    score: float
    premium: bool

    english_name: str | None
    origin_country: str | None
    breed_type: str | None

    flavor_score: float | None
    tenderness_score: float | None
    marbling_score: float | None
    rarity_score: float | None

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

        aliases = tuple(
            str(alias).strip()
            for alias in self.aliases
            if str(alias).strip()
        )

        object.__setattr__(
            self,
            "canonical_name",
            canonical_name,
        )
        object.__setattr__(
            self,
            "aliases",
            aliases,
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

        for field_name in (
            "english_name",
            "origin_country",
            "breed_type",
            "description",
        ):
            value = getattr(
                self,
                field_name,
            )

            if value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    str(value).strip() or None,
                )

        for field_name in (
            "flavor_score",
            "tenderness_score",
            "marbling_score",
            "rarity_score",
        ):
            value = getattr(
                self,
                field_name,
            )

            if value is None:
                continue

            object.__setattr__(
                self,
                field_name,
                max(
                    0.0,
                    min(
                        100.0,
                        float(value),
                    ),
                ),
            )


@dataclass(
    frozen=True,
    kw_only=True,
)
class LambBreedMatch(
    RegistryMatch[LambBreed]
):
    """
    상품명에서 탐지된 양 품종 결과.
    """

    @property
    def breed(self) -> LambBreed:
        return self.entry


class LambBreedRegistry(
    BaseAliasRegistry[LambBreed]
):
    """
    YAML 기반 양 품종 Registry.

    Registry data:
        app/services/food/registry_data/lamb/breeds.yaml
    """

    registry_id = LAMB_BREED_REGISTRY_ID
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
    ) -> LambBreed:
        known_fields = {
            "canonical_name",
            "aliases",
            "score",
            "premium",
            "english_name",
            "origin_country",
            "breed_type",
            "flavor",
            "flavor_score",
            "tenderness",
            "tenderness_score",
            "marbling",
            "marbling_score",
            "rarity",
            "rarity_score",
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

        return LambBreed(
            registry_key=registry_key,
            canonical_name=(
                canonical_name
                or registry_key
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
                raw_entry.get(
                    "english_name"
                )
            ),
            origin_country=optional_string(
                raw_entry.get(
                    "origin_country"
                )
            ),
            breed_type=optional_string(
                raw_entry.get(
                    "breed_type"
                )
            ),
            flavor_score=self._first_score(
                raw_entry,
                "flavor_score",
                "flavor",
            ),
            tenderness_score=self._first_score(
                raw_entry,
                "tenderness_score",
                "tenderness",
            ),
            marbling_score=self._first_score(
                raw_entry,
                "marbling_score",
                "marbling",
            ),
            rarity_score=self._first_score(
                raw_entry,
                "rarity_score",
                "rarity",
            ),
            description=optional_string(
                raw_entry.get(
                    "description"
                )
            ),
            metadata=metadata,
        )

    def match(
        self,
        text: str,
    ) -> LambBreedMatch | None:
        raw_match = super().match(text)

        if raw_match is None:
            return None

        return self._convert_match(
            raw_match
        )

    def find_all(
        self,
        text: str,
    ) -> list[LambBreedMatch]:
        return [
            self._convert_match(match)
            for match in super().find_all(text)
        ]

    def lookup(
        self,
        text: str,
    ) -> LambBreed | None:
        match = self.match(text)

        if match is None:
            return None

        return match.entry

    def list(
        self,
        *,
        premium_only: bool = False,
    ) -> list[LambBreed]:
        breeds = [
            entry
            for entry in super().list()
            if isinstance(
                entry,
                LambBreed,
            )
        ]

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
    ) -> list[LambBreed]:
        return self.list(
            premium_only=True
        )

    def _convert_match(
        self,
        match: AliasMatch[LambBreed],
    ) -> LambBreedMatch:
        if not isinstance(
            match.entry,
            LambBreed,
        ):
            raise TypeError(
                "matched entry must be LambBreed"
            )

        return LambBreedMatch(
            entry=match.entry,
            matched_alias=(
                match.matched_alias
            ),
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
        aliases = normalize_string_list(
            raw_aliases
        )

        ordered: list[str] = []
        seen: set[str] = set()

        for alias in (
            canonical_name,
            *aliases,
        ):
            normalized_alias = str(
                alias
            ).strip()

            if not normalized_alias:
                continue

            dedupe_key = self.normalize_text(
                normalized_alias
            )

            if (
                not dedupe_key
                or dedupe_key in seen
            ):
                continue

            seen.add(dedupe_key)
            ordered.append(
                normalized_alias
            )

        return tuple(ordered)

    @staticmethod
    def _first_score(
        raw_entry: Mapping[str, Any],
        *keys: str,
    ) -> float | None:
        for key in keys:
            value = raw_entry.get(key)

            if value is None or value == "":
                continue

            return safe_float(
                value,
                default=0.0,
            )

        return None


@lru_cache(maxsize=1)
def get_lamb_breed_registry(
) -> LambBreedRegistry:
    return LambBreedRegistry()


def get_lamb_breed(
    registry_key: str,
) -> LambBreed | None:
    return get_lamb_breed_registry().get(
        registry_key
    )


def lookup_lamb_breed(
    text: str,
) -> LambBreed | None:
    return get_lamb_breed_registry().lookup(
        text
    )


def match_lamb_breed(
    text: str,
) -> LambBreedMatch | None:
    return get_lamb_breed_registry().match(
        text
    )


def list_lamb_breeds(
    *,
    premium_only: bool = False,
) -> list[LambBreed]:
    return get_lamb_breed_registry().list(
        premium_only=premium_only
    )


__all__ = [
    "LAMB_BREED_REGISTRY_ID",
    "LambBreed",
    "LambBreedMatch",
    "LambBreedRegistry",
    "get_lamb_breed_registry",
    "get_lamb_breed",
    "lookup_lamb_breed",
    "match_lamb_breed",
    "list_lamb_breeds",
]
