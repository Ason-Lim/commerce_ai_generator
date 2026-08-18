from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


class RecommendationPriority(str, Enum):
    """
    Canonical recommendation priority vocabulary.

    Legacy aliases such as ``ranking`` and ``*_adaptive`` are intentionally
    not resolved here. Alias normalization remains a compatibility concern
    until the canonical policy layer is introduced.
    """

    MIX = "mix"
    PRICE = "price"
    QUALITY = "quality"
    TRUST = "trust"
    EXPLORATION = "exploration"
    DISCOVERY = "discovery"
    REVISIT = "revisit"


_RECOMMENDATION_COMPONENT_NAMES = frozenset(
    {
        "quality",
        "price",
        "trust",
        "popularity",
        "market",
        "identity",
    }
)


@dataclass(frozen=True)
class RecommendationScoreComponents:
    """
    Canonical recommendation score component contract.

    A numeric value and evidence availability are separate concerns.

    ``available=None`` preserves the pre-5H-3A direct-construction contract:
    all six axes are treated as available. Canonical signal adapters should
    explicitly provide the set of axes for which evidence actually exists.
    """

    quality: float = 0.0
    price: float = 0.0
    trust: float = 0.0
    popularity: float = 0.0
    market: float = 0.0
    identity: float = 0.0
    available: frozenset[str] | None = None

    def __post_init__(self) -> None:
        available = (
            _RECOMMENDATION_COMPONENT_NAMES
            if self.available is None
            else frozenset(self.available)
        )

        unknown = (
            available
            - _RECOMMENDATION_COMPONENT_NAMES
        )

        if unknown:
            raise ValueError(
                "unknown recommendation components: "
                + ", ".join(
                    sorted(unknown)
                )
            )

        object.__setattr__(
            self,
            "available",
            available,
        )

    def as_mapping(self) -> Mapping[str, float]:
        return MappingProxyType(
            {
                "quality": self.quality,
                "price": self.price,
                "trust": self.trust,
                "popularity": self.popularity,
                "market": self.market,
                "identity": self.identity,
            }
        )

    def is_available(
        self,
        component: str,
    ) -> bool:
        return component in self.available

    def available_mapping(
        self,
    ) -> Mapping[str, float]:
        values = self.as_mapping()

        return MappingProxyType(
            {
                name: values[name]
                for name in self.available
            }
        )


@dataclass(frozen=True)
class RecommendationScoreResult:
    """
    Immutable canonical representation of a recommendation score result.

    This model does not replace the current V7/V8 dictionary runtime.
    It is the target contract for future canonical scoring.
    """

    final_score: float
    priority: RecommendationPriority
    components: RecommendationScoreComponents
    weights: Mapping[str, float] = field(default_factory=dict)
    reason_codes: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    version: str | None = None

    def __post_init__(self) -> None:
        if not 0.0 <= float(self.final_score) <= 100.0:
            raise ValueError(
                "final_score must be between 0.0 and 100.0"
            )

        object.__setattr__(
            self,
            "weights",
            MappingProxyType(
                dict(self.weights)
            ),
        )


@dataclass(frozen=True)
class RecommendationReason:
    """
    Structured recommendation explanation unit.

    Human-readable rendering remains outside this value contract.
    """

    code: str
    message: str
    weight: float = 0.0
    source: str | None = None


@dataclass(frozen=True)
class RecommendationContext:
    """
    Recommendation-facing request context.

    This object carries recommendation inputs only.
    It does not own Marketplace, Market Intelligence, Food Knowledge,
    user-preference persistence, or external API behavior.
    """

    query: str = ""
    priority: RecommendationPriority = RecommendationPriority.MIX
    session_id: str | None = None
    marketplace_id: str | None = None
    category_id: str | None = None
    limit: int = 10
    adaptive: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.limit <= 0:
            raise ValueError(
                "limit must be greater than zero"
            )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                dict(self.metadata)
            ),
        )


@dataclass(frozen=True)
class RecommendationCandidate:
    """
    Canonical recommendation candidate.

    The raw marketplace/product observation remains separate from
    canonical recommendation scoring evidence.
    """

    item: Mapping[str, Any]
    score: RecommendationScoreResult
    rank: int
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.rank <= 0:
            raise ValueError(
                "rank must be greater than zero"
            )

        object.__setattr__(
            self,
            "item",
            MappingProxyType(
                dict(self.item)
            ),
        )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                dict(self.metadata)
            ),
        )


@dataclass(frozen=True)
class RecommendationResult:
    """
    Canonical orchestration result.

    Compatibility/API/UI fields are intentionally not modeled here.
    """

    context: RecommendationContext
    candidates: tuple[RecommendationCandidate, ...] = ()
    summary: str = ""
    warnings: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "candidates",
            tuple(
                self.candidates
            ),
        )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                dict(self.metadata)
            ),
        )
