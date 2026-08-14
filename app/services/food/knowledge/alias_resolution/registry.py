from __future__ import annotations

from collections.abc import Iterable

from app.services.food.knowledge.alias_resolution.normalizer import (
    AliasNormalizer,
)


class AliasCollisionError(ValueError):
    """
    Raised when one normalized alias is assigned to multiple
    canonical identities.
    """


class AliasRegistry:
    """
    Deterministic alias -> canonical identity registry.

    The registry owns terminology mappings only. It does not own
    category registration or Food Knowledge Provider registration.
    """

    def __init__(
        self,
        *,
        normalizer: AliasNormalizer | None = None,
    ) -> None:
        self._normalizer = normalizer or AliasNormalizer()
        self._aliases: dict[str, str] = {}

    def register(
        self,
        alias: str,
        canonical_id: str,
    ) -> None:
        normalized_alias = self._normalizer.normalize(alias)
        normalized_canonical_id = self._normalizer.normalize(
            canonical_id
        )

        if not normalized_alias:
            raise ValueError("alias가 비어 있습니다.")

        if not normalized_canonical_id:
            raise ValueError("canonical_id가 비어 있습니다.")

        existing = self._aliases.get(normalized_alias)

        if (
            existing is not None
            and existing != normalized_canonical_id
        ):
            raise AliasCollisionError(
                "alias collision: "
                f"{normalized_alias!r} -> "
                f"{existing!r} / {normalized_canonical_id!r}"
            )

        self._aliases[normalized_alias] = (
            normalized_canonical_id
        )

    def register_many(
        self,
        canonical_id: str,
        aliases: Iterable[str],
    ) -> None:
        for alias in aliases:
            self.register(
                alias,
                canonical_id,
            )

    def resolve(
        self,
        alias: str | None,
    ) -> str | None:
        normalized_alias = self._normalizer.normalize(alias)

        if not normalized_alias:
            return None

        return self._aliases.get(normalized_alias)

    def aliases_for(
        self,
        canonical_id: str,
    ) -> tuple[str, ...]:
        normalized_canonical_id = self._normalizer.normalize(
            canonical_id
        )

        return tuple(
            alias
            for alias, registered_id in self._aliases.items()
            if registered_id == normalized_canonical_id
        )

    def __contains__(
        self,
        alias: object,
    ) -> bool:
        if not isinstance(alias, str):
            return False

        normalized_alias = self._normalizer.normalize(alias)

        return normalized_alias in self._aliases

    def __len__(self) -> int:
        return len(self._aliases)
