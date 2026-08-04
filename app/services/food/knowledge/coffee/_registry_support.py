from __future__ import annotations

import copy
from typing import Any, Mapping, TypeVar

from app.services.food.knowledge.common.base_model import (
    RegistryEntry,
    RegistryMatch,
)
from app.services.food.knowledge.common.base_registry import (
    AliasMatch,
    BaseAliasRegistry,
    normalize_string_list,
)


EntryT = TypeVar(
    "EntryT",
    bound=RegistryEntry,
)


def build_aliases(
    canonical_name: str,
    raw_aliases: Any,
) -> tuple[str, ...]:
    values = (
        canonical_name,
        *normalize_string_list(raw_aliases),
    )

    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        text = str(value).strip()
        key = text.casefold()

        if text and key not in seen:
            seen.add(key)
            result.append(text)

    return tuple(result)


def optional_text(
    value: Any,
) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    return text or None


def optional_score(
    value: Any,
) -> float | None:
    if value is None:
        return None

    try:
        score = float(value)
    except (TypeError, ValueError):
        return None

    return max(0.0, min(100.0, score))


def required_score(
    value: Any,
) -> float:
    score = optional_score(value)

    if score is None:
        return 0.0

    return score


def extra_metadata(
    raw_entry: Mapping[str, Any],
    known_fields: set[str],
) -> dict[str, Any]:
    return {
        key: copy.deepcopy(value)
        for key, value in raw_entry.items()
        if key not in known_fields
    }


def convert_match(
    raw_match: AliasMatch[EntryT],
    match_type: type[RegistryMatch[EntryT]],
) -> RegistryMatch[EntryT]:
    return match_type(
        entry=raw_match.entry,
        matched_alias=raw_match.matched_alias,
        normalized_alias=(
            raw_match.normalized_alias
        ),
        match_start=raw_match.match_start,
        match_end=raw_match.match_end,
        confidence=raw_match.confidence,
        exact_match=raw_match.exact_match,
    )


class CoffeeAliasRegistry(
    BaseAliasRegistry[EntryT]
):
    def typed_entries(
        self,
        entry_type: type[EntryT],
        *,
        premium_only: bool = False,
    ) -> list[EntryT]:
        entries = [
            entry
            for entry in super().list()
            if isinstance(entry, entry_type)
        ]

        if premium_only:
            entries = [
                entry
                for entry in entries
                if bool(
                    getattr(
                        entry,
                        "premium",
                        False,
                    )
                )
            ]

        return sorted(
            entries,
            key=lambda entry: (
                -float(
                    getattr(
                        entry,
                        "score",
                        0.0,
                    )
                ),
                str(
                    getattr(
                        entry,
                        "canonical_name",
                        "",
                    )
                ),
            ),
        )


__all__ = [
    "CoffeeAliasRegistry",
    "build_aliases",
    "convert_match",
    "extra_metadata",
    "optional_score",
    "optional_text",
    "required_score",
]
