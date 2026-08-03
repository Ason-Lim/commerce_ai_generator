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


LAMB_CUT_REGISTRY_ID = "lamb.cuts"


@dataclass(
    frozen=True,
    kw_only=True,
)
class LambCut(
    RegistryEntry
):
    """
    양고기 부위 Registry 항목.

    score:
        부위의 일반적인 상품성과 선호도를 나타내는 점수.

    premium:
        프리미엄 부위 여부.

    cut_group:
        loin, rack, leg, shoulder 등 상위 부위 그룹.

    cooking_methods:
        권장 조리 방식.

    tenderness_score:
        연도 특성 참고 점수.

    flavor_score:
        풍미 특성 참고 점수.

    fat_score:
        지방감 특성 참고 점수.

    yield_score:
        가식부 수율 참고 점수.
    """

    canonical_name: str
    aliases: tuple[str, ...]
    score: float
    premium: bool

    english_name: str | None
    cut_group: str | None

    tenderness_score: float | None
    flavor_score: float | None
    fat_score: float | None
    yield_score: float | None

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
            "cooking_methods",
            cooking_methods,
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
            "cut_group",
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
            "tenderness_score",
            "flavor_score",
            "fat_score",
            "yield_score",
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
class LambCutMatch(
    RegistryMatch[LambCut]
):
    """
    상품명에서 탐지된 양고기 부위 결과.
    """

    @property
    def cut(self) -> LambCut:
        return self.entry


class LambCutRegistry(
    BaseAliasRegistry[LambCut]
):
    """
    YAML 기반 양고기 부위 Registry.

    Registry data:
        app/services/food/registry_data/lamb/cuts.yaml
    """

    registry_id = LAMB_CUT_REGISTRY_ID
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
    ) -> LambCut:
        known_fields = {
            "canonical_name",
            "aliases",
            "score",
            "premium",
            "english_name",
            "cut_group",
            "tenderness",
            "tenderness_score",
            "flavor",
            "flavor_score",
            "fat",
            "fat_score",
            "yield",
            "yield_score",
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

        return LambCut(
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
            cut_group=optional_string(
                raw_entry.get(
                    "cut_group"
                )
            ),
            tenderness_score=self._first_score(
                raw_entry,
                "tenderness_score",
                "tenderness",
            ),
            flavor_score=self._first_score(
                raw_entry,
                "flavor_score",
                "flavor",
            ),
            fat_score=self._first_score(
                raw_entry,
                "fat_score",
                "fat",
            ),
            yield_score=self._first_score(
                raw_entry,
                "yield_score",
                "yield",
            ),
            cooking_methods=normalize_string_list(
                raw_entry.get(
                    "cooking_methods"
                )
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
    ) -> LambCutMatch | None:
        raw_match = super().match(text)

        if raw_match is None:
            return None

        return self._convert_match(
            raw_match
        )

    def find_all(
        self,
        text: str,
    ) -> list[LambCutMatch]:
        return [
            self._convert_match(match)
            for match in super().find_all(text)
        ]

    def lookup(
        self,
        text: str,
    ) -> LambCut | None:
        match = self.match(text)

        if match is None:
            return None

        return match.entry

    def list(
        self,
        *,
        premium_only: bool = False,
        cut_group: str | None = None,
    ) -> list[LambCut]:
        cuts = [
            entry
            for entry in super().list()
            if isinstance(
                entry,
                LambCut,
            )
        ]

        if premium_only:
            cuts = [
                cut
                for cut in cuts
                if cut.premium
            ]

        normalized_cut_group = (
            str(cut_group).strip().lower()
            if cut_group is not None
            else None
        )

        if normalized_cut_group:
            cuts = [
                cut
                for cut in cuts
                if (
                    cut.cut_group is not None
                    and cut.cut_group.lower()
                    == normalized_cut_group
                )
            ]

        return sorted(
            cuts,
            key=lambda cut: (
                -cut.score,
                cut.canonical_name,
            ),
        )

    def premium_cuts(
        self,
    ) -> list[LambCut]:
        return self.list(
            premium_only=True
        )

    def cuts_by_group(
        self,
        cut_group: str,
    ) -> list[LambCut]:
        return self.list(
            cut_group=cut_group
        )

    def _convert_match(
        self,
        match: AliasMatch[LambCut],
    ) -> LambCutMatch:
        if not isinstance(
            match.entry,
            LambCut,
        ):
            raise TypeError(
                "matched entry must be LambCut"
            )

        return LambCutMatch(
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
def get_lamb_cut_registry(
) -> LambCutRegistry:
    return LambCutRegistry()


def get_lamb_cut(
    registry_key: str,
) -> LambCut | None:
    return get_lamb_cut_registry().get(
        registry_key
    )


def lookup_lamb_cut(
    text: str,
) -> LambCut | None:
    return get_lamb_cut_registry().lookup(
        text
    )


def match_lamb_cut(
    text: str,
) -> LambCutMatch | None:
    return get_lamb_cut_registry().match(
        text
    )


def list_lamb_cuts(
    *,
    premium_only: bool = False,
    cut_group: str | None = None,
) -> list[LambCut]:
    return get_lamb_cut_registry().list(
        premium_only=premium_only,
        cut_group=cut_group,
    )


__all__ = [
    "LAMB_CUT_REGISTRY_ID",
    "LambCut",
    "LambCutMatch",
    "LambCutRegistry",
    "get_lamb_cut_registry",
    "get_lamb_cut",
    "lookup_lamb_cut",
    "match_lamb_cut",
    "list_lamb_cuts",
]
