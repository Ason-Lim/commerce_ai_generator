from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from app.services.recommendation.compare_identity_engine import (
    get_compare_identity,
)
from app.services.recommendation.compare_snapshot_engine import (
    build_compare_snapshot,
)


MAX_COMPARISON_ITEMS = 3

_COMPARE_IDENTITY_KEY = "_compare_identity"


def _comparison_identity(
    item: Mapping[str, Any],
) -> str:
    stored = item.get(_COMPARE_IDENTITY_KEY)

    if stored:
        return str(stored)

    return get_compare_identity(item)


@dataclass(frozen=True)
class ComparisonTransitionResult:
    items: tuple[dict[str, Any], ...]
    accepted: bool
    limit_reached: bool
    compare_identity: str


def _normalize_current_items(
    current_items: Iterable[Mapping[str, Any]] | None,
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()

    for item in current_items or ():
        copied = dict(item)
        identity = _comparison_identity(copied)

        if identity in seen:
            continue

        seen.add(identity)
        normalized.append(copied)

    return normalized


def transition_comparison_selection(
    *,
    current_items: Iterable[Mapping[str, Any]] | None,
    selected: bool,
    item: Mapping[str, Any],
    display: Mapping[str, Any] | None = None,
    max_items: int = MAX_COMPARISON_ITEMS,
) -> ComparisonTransitionResult:
    if max_items < 1:
        raise ValueError("max_items must be at least 1")

    normalized = _normalize_current_items(
        current_items
    )

    item_copy = dict(item)
    compare_identity = get_compare_identity(
        item_copy
    )

    existing_index = next(
        (
            index
            for index, existing in enumerate(
                normalized
            )
            if _comparison_identity(existing)
            == compare_identity
        ),
        None,
    )

    if not selected:
        if existing_index is not None:
            normalized.pop(existing_index)

        return ComparisonTransitionResult(
            items=tuple(
                dict(existing)
                for existing in normalized
            ),
            accepted=True,
            limit_reached=False,
            compare_identity=compare_identity,
        )

    if existing_index is not None:
        return ComparisonTransitionResult(
            items=tuple(
                dict(existing)
                for existing in normalized
            ),
            accepted=True,
            limit_reached=False,
            compare_identity=compare_identity,
        )

    if len(normalized) >= max_items:
        return ComparisonTransitionResult(
            items=tuple(
                dict(existing)
                for existing in normalized
            ),
            accepted=False,
            limit_reached=True,
            compare_identity=compare_identity,
        )

    snapshot_source = dict(item_copy)

    if display:
        snapshot_source.update(
            dict(display)
        )

    snapshot = dict(
        build_compare_snapshot(
            snapshot_source
        )
    )
    snapshot[_COMPARE_IDENTITY_KEY] = (
        compare_identity
    )

    normalized.append(snapshot)

    return ComparisonTransitionResult(
        items=tuple(
            dict(existing)
            for existing in normalized
        ),
        accepted=True,
        limit_reached=False,
        compare_identity=compare_identity,
    )
