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


BEEF_CUT_REGISTRY_ID = "beef.cuts"


@dataclass(
    frozen=True,
    kw_only=True,
)
class BeefCut(
    RegistryEntry
):
    """
    쇠고기 부위 Registry 항목.

    score:
        부위의 전반적인 상품성 및 추천 기준 점수.

    tenderness_score:
        부드러움 점수. YAML의 tenderness 필드를 정규화해 저장한다.

    fat_level:
        지방 수준. 예: low, medium, high, very_high.

    cooking_methods:
        권장 조리 방식. 예: steak, grilling, braising.
    """

    canonical_name: str
    aliases: tuple[str, ...]
    score: float
    premium: bool
    tenderness_score: float | None
    fat_level: str | None
    cooking_methods: tuple[str, ...]
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

        cooking_methods = tuple(
            str(method).strip()
            for method in self.cooking_methods
            if str(method).strip()
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
        object.__setattr__(
            self,
            "cooking_methods",
            cooking_methods,
        )

        if self.tenderness_score is not None:
            object.__setattr__(
                self,
                "tenderness_score",
                max(
                    0.0,
                    min(
                        100.0,
                        float(
                            self.tenderness_score
                        ),
                    ),
                ),
            )

        if self.fat_level is not None:
            object.__setattr__(
                self,
                "fat_level",
                str(
                    self.fat_level
                ).strip() or None,
            )

        if self.description is not None:
            object.__setattr__(
                self,
                "description",
                str(
                    self.description
                ).strip() or None,
            )


@dataclass(
    frozen=True,
    kw_only=True,
)
class BeefCutMatch(
    RegistryMatch[BeefCut]
):
    """
    BeefCut 별칭 검색 결과.
    """

    @property
    def cut(self) -> BeefCut:
        return self.entry


class BeefCutRegistry(
    BaseAliasRegistry
):
    """
    쇠고기 부위 Registry.

    Registry data:
        app/services/food/registry_data/beef/cuts.yaml
    """

    registry_id = BEEF_CUT_REGISTRY_ID

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
    ) -> BeefCut:
        known_fields = {
            "canonical_name",
            "aliases",
            "score",
            "premium",
            "tenderness",
            "tenderness_score",
            "fat_level",
            "cooking_methods",
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

        aliases = self._build_entry_aliases(
            canonical_name=canonical_name,
            raw_aliases=raw_entry.get(
                "aliases"
            ),
        )

        raw_tenderness = raw_entry.get(
            "tenderness_score",
            raw_entry.get("tenderness"),
        )

        tenderness_score: float | None

        if raw_tenderness is None:
            tenderness_score = None
        else:
            tenderness_score = safe_float(
                raw_tenderness,
                default=0.0,
            )

        return BeefCut(
            registry_key=registry_key,
            canonical_name=(
                canonical_name
                or registry_key
            ),
            aliases=aliases,
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
            tenderness_score=(
                tenderness_score
            ),
            fat_level=optional_string(
                raw_entry.get("fat_level")
            ),
            cooking_methods=tuple(
                normalize_string_list(
                    raw_entry.get(
                        "cooking_methods"
                    )
                )
            ),
            description=optional_string(
                raw_entry.get("description")
            ),
            metadata=metadata,
        )

    def match(
        self,
        text: str,
    ) -> BeefCutMatch | None:
        raw_match = super().match(text)

        if raw_match is None:
            return None

        return self._convert_match(
            raw_match
        )

    def find_all(
        self,
        text: str,
    ) -> list[BeefCutMatch]:
        return [
            self._convert_match(match)
            for match in super().find_all(text)
        ]

    def lookup(
        self,
        text: str,
    ) -> BeefCut | None:
        match = self.match(text)

        if match is None:
            return None

        return match.entry

    def list(
        self,
    ) -> list[BeefCut]:
        return [
            entry
            for entry in super().list()
            if isinstance(entry, BeefCut)
        ]

    def premium_cuts(
        self,
    ) -> list[BeefCut]:
        """
        premium=true인 부위를 점수 내림차순으로 반환한다.
        """
        return sorted(
            (
                cut
                for cut in self.list()
                if cut.premium
            ),
            key=lambda cut: (
                cut.score,
                cut.tenderness_score or 0.0,
                cut.canonical_name,
            ),
            reverse=True,
        )

    def cooking_method_cuts(
        self,
        cooking_method: str,
    ) -> list[BeefCut]:
        """
        특정 조리 방식에 적합한 부위를 반환한다.

        예:
            cooking_method_cuts("steak")
            cooking_method_cuts("grilling")
        """
        normalized_method = str(
            cooking_method
        ).strip().casefold()

        if not normalized_method:
            return []

        return sorted(
            (
                cut
                for cut in self.list()
                if normalized_method
                in {
                    method.casefold()
                    for method
                    in cut.cooking_methods
                }
            ),
            key=lambda cut: (
                cut.score,
                cut.tenderness_score or 0.0,
            ),
            reverse=True,
        )

    def fat_level_cuts(
        self,
        fat_level: str,
    ) -> list[BeefCut]:
        normalized_level = str(
            fat_level
        ).strip().casefold()

        if not normalized_level:
            return []

        return sorted(
            (
                cut
                for cut in self.list()
                if (
                    cut.fat_level is not None
                    and cut.fat_level.casefold()
                    == normalized_level
                )
            ),
            key=lambda cut: cut.score,
            reverse=True,
        )

    def _convert_match(
        self,
        match: AliasMatch,
    ) -> BeefCutMatch:
        if not isinstance(
            match.entry,
            BeefCut,
        ):
            raise TypeError(
                "matched entry must be BeefCut"
            )

        return BeefCutMatch(
            entry=match.entry,
            matched_alias=(
                match.matched_alias
            ),
            normalized_alias=(
                match.normalized_alias
            ),
            match_start=(
                match.match_start
            ),
            match_end=(
                match.match_end
            ),
            confidence=(
                match.confidence
            ),
            exact_match=(
                match.exact_match
            ),
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

            dedupe_key = (
                normalized_alias.casefold()
            )

            if dedupe_key in seen:
                continue

            seen.add(dedupe_key)
            ordered.append(
                normalized_alias
            )

        return tuple(ordered)


@lru_cache(maxsize=1)
def get_beef_cut_registry() -> BeefCutRegistry:
    return BeefCutRegistry()


def get_beef_cut(
    registry_key: str,
) -> BeefCut | None:
    return get_beef_cut_registry().get(
        registry_key
    )


def lookup_beef_cut(
    text: str,
) -> BeefCut | None:
    return get_beef_cut_registry().lookup(
        text
    )


def match_beef_cut(
    text: str,
) -> BeefCutMatch | None:
    return get_beef_cut_registry().match(
        text
    )


def list_beef_cuts() -> list[BeefCut]:
    return get_beef_cut_registry().list()


def premium_beef_cuts() -> list[BeefCut]:
    return (
        get_beef_cut_registry()
        .premium_cuts()
    )


def beef_cuts_for_cooking(
    cooking_method: str,
) -> list[BeefCut]:
    return (
        get_beef_cut_registry()
        .cooking_method_cuts(
            cooking_method
        )
    )


__all__ = [
    "BEEF_CUT_REGISTRY_ID",
    "BeefCut",
    "BeefCutMatch",
    "BeefCutRegistry",
    "beef_cuts_for_cooking",
    "get_beef_cut",
    "get_beef_cut_registry",
    "list_beef_cuts",
    "lookup_beef_cut",
    "match_beef_cut",
    "premium_beef_cuts",
]
