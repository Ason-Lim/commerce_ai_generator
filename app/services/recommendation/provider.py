from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from app.services.recommendation.deduplication import (
    deduplicate_market_items,
)
from app.services.food_intelligence.food_intelligence_engine import (
    enrich_items_with_food_intelligence,
)
from app.services.market.collector import (
    collect_market_products,
)
from app.services.recommendation.platform_normalization import (
    normalize_platform_items,
)

from .models import (
    RecommendationCandidate,
    RecommendationContext,
    RecommendationResult,
    RecommendationScoreComponents,
    RecommendationScoreResult,
)
from .price_utility import (
    calculate_price_utilities,
)
from .trust_adapter import (
    adapt_trust_evidence,
)
from .popularity_adapter import (
    adapt_canonical_popularity,
)
from .market_adapter import (
    adapt_canonical_market,
)
from .identity_adapter import (
    adapt_canonical_identity,
)
from .ranking import rank_candidates
from .scoring import calculate_recommendation_score


Candidate = dict[str, Any]

CandidateCollector = Callable[
    [str, int],
    list[Candidate],
]

CandidateTransform = Callable[
    [list[Candidate]],
    list[Candidate],
]

ComponentBuilder = Callable[
    [Mapping[str, Any]],
    RecommendationScoreComponents,
]

PricePreparer = Callable[
    [Sequence[Mapping[str, Any]]],
    Sequence[Any],
]

TrustPreparer = Callable[
    [Sequence[Mapping[str, Any]]],
    Sequence[Any],
]

PopularityPreparer = Callable[
    [Sequence[Mapping[str, Any]]],
    Sequence[Any],
]

MarketPreparer = Callable[
    [Sequence[Mapping[str, Any]]],
    Sequence[Any],
]

IdentityPreparer = Callable[
    [Sequence[Mapping[str, Any]]],
    Sequence[Any],
]

Scorer = Callable[
    [
        RecommendationScoreComponents,
        Any,
    ],
    RecommendationScoreResult,
]


def _safe_number(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        if value is None or value == "":
            return float(default)

        return float(value)

    except (TypeError, ValueError):
        return float(default)


def _first_available_number(
    item: Mapping[str, Any],
    *keys: str,
) -> tuple[float, bool]:
    """
    Return the first usable numeric evidence value.

    Observed zero remains available evidence.
    Missing/invalid values remain unavailable.
    """

    for key in keys:
        if key not in item:
            continue

        value = item.get(
            key
        )

        if value is None or value == "":
            continue

        try:
            return (
                float(value),
                True,
            )

        except (TypeError, ValueError):
            continue

    return (
        0.0,
        False,
    )


def prepare_price_utility(
    items: Sequence[Mapping[str, Any]],
) -> list[Candidate]:
    """
    Prepare canonical candidate-relative price evidence.

    The calculation itself is owned by ``price_utility.py``.
    This adapter only attaches the resulting evidence to copied
    candidate observations for downstream component adaptation.
    """

    observations = calculate_price_utilities(
        items
    )

    prepared: list[Candidate] = []

    for item, observation in zip(
        items,
        observations,
    ):
        row = dict(
            item
        )

        if observation.available:
            row[
                "price_score"
            ] = observation.utility

            row[
                "_canonical_raw_price"
            ] = observation.raw_price

        prepared.append(
            row
        )

    return prepared


def prepare_trust_evidence(
    items: Sequence[Mapping[str, Any]],
) -> list[Candidate]:
    """
    Attach canonical trust evidence to copied candidate observations.

    Trust interpretation is delegated to ``trust_adapter.py``.
    This function performs orchestration preparation only.
    """

    prepared: list[Candidate] = []

    for item in items:
        row = dict(
            item
        )

        observation = adapt_trust_evidence(
            row
        )

        if observation.available:
            row[
                "_canonical_trust_score"
            ] = observation.score

            row[
                "_canonical_trust_source"
            ] = observation.source

        prepared.append(
            row
        )

    return prepared


def prepare_popularity_evidence(
    items: Sequence[Mapping[str, Any]],
) -> list[Candidate]:
    """
    Attach canonical popularity evidence to copied candidates.

    Popularity interpretation is delegated to
    ``popularity_adapter.py``.

    Raw click, CTR, review, rating, purchase, and market evidence
    is not calculated here.
    """

    prepared: list[Candidate] = []

    for item in items:
        row = dict(
            item
        )

        popularity = adapt_canonical_popularity(
            row
        )

        if popularity is not None:
            row[
                "_canonical_popularity_score"
            ] = popularity

        prepared.append(
            row
        )

    return prepared


def prepare_market_evidence(
    items: Sequence[Mapping[str, Any]],
) -> list[Candidate]:
    """
    Attach canonical Market Intelligence evidence to copied candidates.

    Market interpretation remains owned by 31_Market Intelligence.
    This layer consumes canonical market_score only.
    """

    prepared: list[Candidate] = []

    for item in items:
        row = dict(item)

        market = adapt_canonical_market(
            row
        )

        if market is not None:
            row[
                "_canonical_market_score"
            ] = market

        prepared.append(
            row
        )

    return prepared


def prepare_identity_evidence(
    items: Sequence[Mapping[str, Any]],
) -> list[Candidate]:
    """
    Attach canonical identity evidence to copied candidates.

    Identity interpretation is delegated to ``identity_adapter.py``.
    This layer does not calculate product identity.
    """

    prepared: list[Candidate] = []

    for item in items:
        row = dict(item)

        identity = adapt_canonical_identity(
            row
        )

        if identity is not None:
            row[
                "_canonical_identity_score"
            ] = identity

        prepared.append(
            row
        )

    return prepared


def build_score_components(
    item: Mapping[str, Any],
) -> RecommendationScoreComponents:
    """
    Adapt available upstream evidence into canonical scoring axes.

    This adapter does not calculate source-domain signals and does not
    manufacture numeric evidence for unavailable components.
    """

    quality, quality_available = (
        _first_available_number(
            item,
            "fruit_quality_score",
            "food_intelligence_score",
            "v7_quality_score",
        )
    )

    price, price_available = (
        _first_available_number(
            item,
            "v8_price_score",
            "price_score",
            "v7_price_score",
        )
    )

    trust, trust_available = (
        _first_available_number(
            item,
            "_canonical_trust_score",
        )
    )

    popularity, popularity_available = (
        _first_available_number(
            item,
            "_canonical_popularity_score",
        )
    )

    market, market_available = (
        _first_available_number(
            item,
            "_canonical_market_score",
        )
    )

    identity, identity_available = (
        _first_available_number(
            item,
            "_canonical_identity_score",
        )
    )

    available: set[str] = set()

    for name, is_available in (
        (
            "quality",
            quality_available,
        ),
        (
            "price",
            price_available,
        ),
        (
            "trust",
            trust_available,
        ),
        (
            "popularity",
            popularity_available,
        ),
        (
            "market",
            market_available,
        ),
        (
            "identity",
            identity_available,
        ),
    ):
        if is_available:
            available.add(
                name
            )

    return RecommendationScoreComponents(
        quality=quality,
        price=price,
        trust=trust,
        popularity=popularity,
        market=market,
        identity=identity,
        available=frozenset(
            available
        ),
    )


class RecommendationProvider:
    """
    Canonical Recommendation orchestration boundary.

    Responsibilities:
    - consume RecommendationContext;
    - invoke candidate acquisition;
    - invoke deduplication;
    - invoke platform normalization;
    - invoke food intelligence enrichment;
    - adapt enriched observations to canonical score components;
    - invoke canonical scoring;
    - invoke canonical ranking;
    - build RecommendationResult.

    Non-responsibilities:
    - query parsing;
    - priority resolution;
    - marketplace implementation;
    - deduplication implementation;
    - platform-normalization implementation;
    - Food Intelligence implementation;
    - scoring formula implementation;
    - ranking formula implementation;
    - persistence;
    - API/UI compatibility response construction.
    """

    def __init__(
        self,
        *,
        collector: CandidateCollector = collect_market_products,
        deduplicator: CandidateTransform = deduplicate_market_items,
        normalizer: CandidateTransform = normalize_platform_items,
        food_enricher: CandidateTransform = (
            enrich_items_with_food_intelligence
        ),
        price_preparer: PricePreparer = prepare_price_utility,
        trust_preparer: TrustPreparer = prepare_trust_evidence,
        popularity_preparer: PopularityPreparer = prepare_popularity_evidence,
        market_preparer: MarketPreparer = prepare_market_evidence,
        identity_preparer: IdentityPreparer = prepare_identity_evidence,
        component_builder: ComponentBuilder = build_score_components,
    ) -> None:
        self.collector = collector
        self.deduplicator = deduplicator
        self.normalizer = normalizer
        self.food_enricher = food_enricher
        self.price_preparer = price_preparer
        self.trust_preparer = trust_preparer
        self.popularity_preparer = popularity_preparer
        self.market_preparer = market_preparer
        self.identity_preparer = identity_preparer
        self.component_builder = component_builder

    def recommend(
        self,
        context: RecommendationContext,
    ) -> RecommendationResult:
        if not context.query:
            return RecommendationResult(
                context=context,
                summary="검색어를 입력해 주세요.",
                metadata={
                    "provider": self.__class__.__name__,
                },
            )

        collected = self.collector(
            context.query,
            context.limit,
        )

        if not collected:
            return RecommendationResult(
                context=context,
                summary="추천 가능한 상품을 찾지 못했습니다.",
                metadata={
                    "provider": self.__class__.__name__,
                },
            )

        deduplicated = self.deduplicator(
            list(collected)
        )

        normalized = self.normalizer(
            list(deduplicated)
        )

        enriched = self.food_enricher(
            list(normalized)
        )

        if not enriched:
            return RecommendationResult(
                context=context,
                summary="추천 가능한 상품을 찾지 못했습니다.",
                metadata={
                    "provider": self.__class__.__name__,
                },
            )

        price_prepared = self.price_preparer(
            list(enriched)
        )

        if not price_prepared:
            return RecommendationResult(
                context=context,
                summary="추천 가능한 상품을 찾지 못했습니다.",
                metadata={
                    "provider": self.__class__.__name__,
                },
            )

        trust_prepared = self.trust_preparer(
            list(price_prepared)
        )

        if not trust_prepared:
            return RecommendationResult(
                context=context,
                summary="추천 가능한 상품을 찾지 못했습니다.",
                metadata={
                    "provider": self.__class__.__name__,
                },
            )

        popularity_prepared = self.popularity_preparer(
            list(trust_prepared)
        )

        if not popularity_prepared:
            return RecommendationResult(
                context=context,
                summary="추천 가능한 상품을 찾지 못했습니다.",
                metadata={
                    "provider": self.__class__.__name__,
                },
            )

        market_prepared = self.market_preparer(
            list(popularity_prepared)
        )

        if not market_prepared:
            return RecommendationResult(
                context=context,
                summary="추천 가능한 상품을 찾지 못했습니다.",
                metadata={
                    "provider": self.__class__.__name__,
                },
            )

        identity_prepared = self.identity_preparer(
            list(market_prepared)
        )

        if not identity_prepared:
            return RecommendationResult(
                context=context,
                summary="추천 가능한 상품을 찾지 못했습니다.",
                metadata={
                    "provider": self.__class__.__name__,
                },
            )

        scored: list[
            tuple[
                Candidate,
                RecommendationScoreResult,
            ]
        ] = []

        for item in identity_prepared:
            components = self.component_builder(
                item
            )

            score_result = (
                calculate_recommendation_score(
                    components,
                    context.priority,
                )
            )

            scored.append(
                (
                    dict(item),
                    score_result,
                )
            )

        ranked = rank_candidates(
            scored,
            context.priority,
            final_score=lambda pair: (
                pair[1].final_score
            ),
            price=lambda pair: (
                pair[0].get("price")
            ),
            quality_score=lambda pair: (
                pair[1].components.quality
            ),
            trust_signal=lambda pair: (
                pair[1].components.trust
            ),
        )

        candidates = tuple(
            RecommendationCandidate(
                item=item,
                score=score,
                rank=index,
                metadata={
                    "provider": (
                        self.__class__.__name__
                    ),
                },
            )
            for index, (
                item,
                score,
            ) in enumerate(
                ranked,
                start=1,
            )
        )

        return RecommendationResult(
            context=context,
            candidates=candidates,
            summary=(
                f"'{context.query}' 기준으로 "
                f"추천 상품 {len(candidates)}개를 구성했습니다."
            ),
            metadata={
                "provider": self.__class__.__name__,
                "candidate_count": len(
                    candidates
                ),
            },
        )
