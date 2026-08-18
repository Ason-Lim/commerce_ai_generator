from copy import deepcopy

from app.services.recommendation.context import (
    build_recommendation_context,
)
from app.services.recommendation.models import (
    RecommendationCandidate,
    RecommendationPriority,
    RecommendationResult,
    RecommendationScoreComponents,
)
from app.services.recommendation.parser import (
    parse_recommendation_query,
)
from app.services.recommendation.policy import (
    resolve_recommendation_policy,
)
from app.services.recommendation.provider import (
    RecommendationProvider,
    build_score_components,
)


def _context(
    priority: str = "ranking",
):
    return build_recommendation_context(
        parse_recommendation_query(
            "사과"
        ),
        resolve_recommendation_policy(
            priority
        ),
        limit=10,
    )


def _raw_items():
    return [
        {
            "product_id": "A",
            "product_name": "사과 A",
            "price": 10000,
            "platform": "naver",
            "food_intelligence_score": 80,
            "fruit_quality_score": 85,
            "platform_boost_score": 70,
            "v8_price_score": 90,
            "_canonical_identity_score": 90,
        },
        {
            "product_id": "B",
            "product_name": "사과 B",
            "price": 20000,
            "platform": "coupang",
            "food_intelligence_score": 70,
            "fruit_quality_score": 75,
            "platform_boost_score": 90,
            "v8_price_score": 60,
            "_canonical_identity_score": 90,
        },
    ]


def _passthrough(items):
    return [
        dict(item)
        for item in items
    ]


def test_component_builder_adapts_existing_signals() -> None:
    components = build_score_components(
        {
            "fruit_quality_score": 85,
            "v8_price_score": 90,
            "_canonical_trust_score": 75,
            "_canonical_popularity_score": 50,
            "_canonical_market_score": 65,
            "_canonical_identity_score": 88,
        }
    )

    assert components == RecommendationScoreComponents(
        quality=85,
        price=90,
        trust=75,
        popularity=50,
        market=65,
        identity=88,
    )


def test_component_builder_does_not_calculate_missing_market_signal() -> None:
    components = build_score_components(
        {
            "food_intelligence_score": 80,
        }
    )

    assert components.market == 0.0


def test_component_builder_keeps_missing_identity_unavailable() -> None:
    components = build_score_components(
        {}
    )

    assert components.identity == 0.0
    assert components.is_available(
        "identity"
    ) is False


def test_provider_returns_canonical_result() -> None:
    provider = RecommendationProvider(
        collector=lambda query, limit: (
            deepcopy(
                _raw_items()
            )
        ),
        deduplicator=_passthrough,
        normalizer=_passthrough,
        food_enricher=_passthrough,
    )

    result = provider.recommend(
        _context()
    )

    assert isinstance(
        result,
        RecommendationResult,
    )

    assert len(
        result.candidates
    ) == 2


def test_provider_builds_canonical_candidates() -> None:
    provider = RecommendationProvider(
        collector=lambda query, limit: (
            deepcopy(
                _raw_items()
            )
        ),
        deduplicator=_passthrough,
        normalizer=_passthrough,
        food_enricher=_passthrough,
    )

    result = provider.recommend(
        _context()
    )

    assert all(
        isinstance(
            candidate,
            RecommendationCandidate,
        )
        for candidate in result.candidates
    )


def test_provider_assigns_rank_after_canonical_ranking() -> None:
    provider = RecommendationProvider(
        collector=lambda query, limit: (
            deepcopy(
                _raw_items()
            )
        ),
        deduplicator=_passthrough,
        normalizer=_passthrough,
        food_enricher=_passthrough,
    )

    result = provider.recommend(
        _context(
            "price"
        )
    )

    assert [
        candidate.rank
        for candidate in result.candidates
    ] == [
        1,
        2,
    ]

    assert [
        candidate.item[
            "product_id"
        ]
        for candidate in result.candidates
    ] == [
        "A",
        "B",
    ]


def test_provider_uses_context_priority_for_scoring() -> None:
    provider = RecommendationProvider(
        collector=lambda query, limit: (
            deepcopy(
                _raw_items()
            )
        ),
        deduplicator=_passthrough,
        normalizer=_passthrough,
        food_enricher=_passthrough,
    )

    result = provider.recommend(
        _context(
            "trust"
        )
    )

    assert all(
        candidate.score.priority
        is RecommendationPriority.TRUST
        for candidate in result.candidates
    )


def test_provider_calls_dependencies_in_orchestration_order() -> None:
    calls = []

    def collect(query, limit):
        calls.append(
            "collect"
        )
        return deepcopy(
            _raw_items()
        )

    def dedup(items):
        calls.append(
            "dedup"
        )
        return _passthrough(
            items
        )

    def normalize(items):
        calls.append(
            "normalize"
        )
        return _passthrough(
            items
        )

    def enrich(items):
        calls.append(
            "food_enrich"
        )
        return _passthrough(
            items
        )

    provider = RecommendationProvider(
        collector=collect,
        deduplicator=dedup,
        normalizer=normalize,
        food_enricher=enrich,
    )

    provider.recommend(
        _context()
    )

    assert calls == [
        "collect",
        "dedup",
        "normalize",
        "food_enrich",
    ]


def test_provider_passes_context_query_and_limit_to_collector() -> None:
    received = {}

    def collect(query, limit):
        received[
            "query"
        ] = query
        received[
            "limit"
        ] = limit
        return []

    provider = RecommendationProvider(
        collector=collect,
        deduplicator=_passthrough,
        normalizer=_passthrough,
        food_enricher=_passthrough,
    )

    context = build_recommendation_context(
        parse_recommendation_query(
            "사과"
        ),
        resolve_recommendation_policy(
            "ranking"
        ),
        limit=4,
    )

    provider.recommend(
        context
    )

    assert received == {
        "query": "사과",
        "limit": 4,
    }


def test_provider_does_not_parse_query() -> None:
    observed = {}

    def collect(query, limit):
        observed[
            "query"
        ] = query
        return []

    provider = RecommendationProvider(
        collector=collect,
        deduplicator=_passthrough,
        normalizer=_passthrough,
        food_enricher=_passthrough,
    )

    context = build_recommendation_context(
        parse_recommendation_query(
            "가성비 좋은 사과 추천"
        ),
        resolve_recommendation_policy(
            "price"
        ),
    )

    provider.recommend(
        context
    )

    assert observed[
        "query"
    ] == "사과"


def test_provider_empty_query_does_not_call_collector() -> None:
    called = False

    def collect(query, limit):
        nonlocal called
        called = True
        return []

    provider = RecommendationProvider(
        collector=collect,
        deduplicator=_passthrough,
        normalizer=_passthrough,
        food_enricher=_passthrough,
    )

    context = build_recommendation_context(
        parse_recommendation_query(
            ""
        ),
        resolve_recommendation_policy(
            "ranking"
        ),
    )

    result = provider.recommend(
        context
    )

    assert called is False
    assert result.candidates == ()


def test_provider_stops_when_collection_is_empty() -> None:
    calls = []

    def collect(query, limit):
        calls.append(
            "collect"
        )
        return []

    def unexpected(items):
        calls.append(
            "unexpected"
        )
        return items

    provider = RecommendationProvider(
        collector=collect,
        deduplicator=unexpected,
        normalizer=unexpected,
        food_enricher=unexpected,
    )

    result = provider.recommend(
        _context()
    )

    assert calls == [
        "collect",
    ]

    assert result.candidates == ()


def test_provider_stops_when_enrichment_is_empty() -> None:
    provider = RecommendationProvider(
        collector=lambda query, limit: (
            deepcopy(
                _raw_items()
            )
        ),
        deduplicator=_passthrough,
        normalizer=_passthrough,
        food_enricher=lambda items: [],
    )

    result = provider.recommend(
        _context()
    )

    assert result.candidates == ()


def test_provider_does_not_add_legacy_compatibility_fields() -> None:
    provider = RecommendationProvider(
        collector=lambda query, limit: (
            deepcopy(
                _raw_items()
            )
        ),
        deduplicator=_passthrough,
        normalizer=_passthrough,
        food_enricher=_passthrough,
    )

    result = provider.recommend(
        _context()
    )

    forbidden = {
        "recommendation_mode",
        "selected_priority",
        "sort_mode",
        "v7_rank",
        "adaptive_score",
        "final_recommendation_label",
    }

    for candidate in result.candidates:
        assert not (
            forbidden
            & set(
                candidate.item
            )
        )


def test_provider_does_not_mutate_collected_items() -> None:
    source = _raw_items()
    before = deepcopy(
        source
    )

    provider = RecommendationProvider(
        collector=lambda query, limit: (
            source
        ),
        deduplicator=_passthrough,
        normalizer=_passthrough,
        food_enricher=_passthrough,
    )

    provider.recommend(
        _context()
    )

    assert source == before


def test_result_and_candidate_mappings_are_read_only() -> None:
    provider = RecommendationProvider(
        collector=lambda query, limit: (
            deepcopy(
                _raw_items()
            )
        ),
        deduplicator=_passthrough,
        normalizer=_passthrough,
        food_enricher=_passthrough,
    )

    result = provider.recommend(
        _context()
    )

    candidate = result.candidates[0]

    try:
        candidate.item[
            "product_id"
        ] = "changed"
        mutated = True
    except TypeError:
        mutated = False

    assert mutated is False


def test_provider_is_deterministic_for_deterministic_dependencies() -> None:
    provider = RecommendationProvider(
        collector=lambda query, limit: (
            deepcopy(
                _raw_items()
            )
        ),
        deduplicator=_passthrough,
        normalizer=_passthrough,
        food_enricher=_passthrough,
    )

    first = provider.recommend(
        _context(
            "quality"
        )
    )

    second = provider.recommend(
        _context(
            "quality"
        )
    )

    assert first == second
