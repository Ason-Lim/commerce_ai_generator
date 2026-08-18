from copy import deepcopy

from app.services.recommendation.context import (
    build_recommendation_context,
)
from app.services.recommendation.parser import (
    parse_recommendation_query,
)
from app.services.recommendation.policy import (
    resolve_recommendation_policy,
)
from app.services.recommendation.provider import (
    RecommendationProvider,
    prepare_market_evidence,
)


def _context():
    return build_recommendation_context(
        parse_recommendation_query("사과"),
        resolve_recommendation_policy("ranking"),
    )


def _passthrough(items):
    return [
        dict(item)
        for item in items
    ]


def _source():
    return [
        {
            "product_id": "A",
            "product_name": "사과 A",
            "price": 10000,
            "food_intelligence_score": 80,
            "market_score": 90,
        },
        {
            "product_id": "B",
            "product_name": "사과 B",
            "price": 12000,
            "food_intelligence_score": 80,
            "trend_score": 95,
            "trend_direction": "up",
        },
        {
            "product_id": "C",
            "product_name": "사과 C",
            "price": 15000,
            "food_intelligence_score": 80,
            "market_signal_score": 100,
            "market_signal_score_final": 100,
        },
    ]


def test_market_preparation_attaches_canonical_market_score():
    prepared = prepare_market_evidence(
        [
            {
                "market_score": 88,
            }
        ]
    )

    assert (
        prepared[0][
            "_canonical_market_score"
        ]
        == 88.0
    )


def test_observed_zero_market_is_preserved():
    prepared = prepare_market_evidence(
        [
            {
                "market_score": 0,
                "trend_score": 100,
            }
        ]
    )

    assert (
        prepared[0][
            "_canonical_market_score"
        ]
        == 0.0
    )


def test_trend_evidence_does_not_create_market_inline():
    prepared = prepare_market_evidence(
        [
            {
                "trend_score": 95,
                "trend_direction": "up",
            }
        ]
    )

    assert (
        "_canonical_market_score"
        not in prepared[0]
    )


def test_legacy_market_signal_does_not_create_market_inline():
    prepared = prepare_market_evidence(
        [
            {
                "market_signal_score": 90,
                "market_signal_score_final": 95,
                "propagated_market_signal_score": 98,
            }
        ]
    )

    assert (
        "_canonical_market_score"
        not in prepared[0]
    )


def test_market_preparation_does_not_mutate_source():
    source = _source()
    before = deepcopy(source)

    prepare_market_evidence(
        source
    )

    assert source == before


def test_provider_marks_market_score_available():
    provider = RecommendationProvider(
        collector=lambda query, limit: deepcopy(
            _source()
        ),
        deduplicator=_passthrough,
        normalizer=_passthrough,
        food_enricher=_passthrough,
    )

    result = provider.recommend(
        _context()
    )

    by_id = {
        candidate.item[
            "product_id"
        ]: candidate
        for candidate in result.candidates
    }

    assert by_id[
        "A"
    ].score.components.is_available(
        "market"
    )

    assert (
        by_id["A"].score.components.market
        == 90.0
    )


def test_provider_keeps_trend_only_market_unavailable():
    provider = RecommendationProvider(
        collector=lambda query, limit: deepcopy(
            _source()
        ),
        deduplicator=_passthrough,
        normalizer=_passthrough,
        food_enricher=_passthrough,
    )

    result = provider.recommend(
        _context()
    )

    by_id = {
        candidate.item[
            "product_id"
        ]: candidate
        for candidate in result.candidates
    }

    assert (
        by_id["B"].score.components.is_available(
            "market"
        )
        is False
    )


def test_provider_keeps_legacy_market_signal_unavailable():
    provider = RecommendationProvider(
        collector=lambda query, limit: deepcopy(
            _source()
        ),
        deduplicator=_passthrough,
        normalizer=_passthrough,
        food_enricher=_passthrough,
    )

    result = provider.recommend(
        _context()
    )

    by_id = {
        candidate.item[
            "product_id"
        ]: candidate
        for candidate in result.candidates
    }

    assert (
        by_id["C"].score.components.is_available(
            "market"
        )
        is False
    )


def test_provider_calls_market_after_popularity():
    calls = []

    def collect(query, limit):
        calls.append("collect")
        return _source()

    def stage(name):
        def run(items):
            calls.append(name)
            return _passthrough(items)
        return run

    provider = RecommendationProvider(
        collector=collect,
        deduplicator=stage("dedup"),
        normalizer=stage("normalize"),
        food_enricher=stage("food"),
        price_preparer=stage("price"),
        trust_preparer=stage("trust"),
        popularity_preparer=stage("popularity"),
        market_preparer=stage("market"),
    )

    provider.recommend(
        _context()
    )

    assert calls == [
        "collect",
        "dedup",
        "normalize",
        "food",
        "price",
        "trust",
        "popularity",
        "market",
    ]


def test_provider_can_inject_market_preparer():
    calls = []

    def custom_market(items):
        calls.append("custom")

        prepared = []

        for item in items:
            row = dict(item)
            row[
                "_canonical_market_score"
            ] = 77.0
            prepared.append(row)

        return prepared

    provider = RecommendationProvider(
        collector=lambda query, limit: deepcopy(
            _source()
        ),
        deduplicator=_passthrough,
        normalizer=_passthrough,
        food_enricher=_passthrough,
        market_preparer=custom_market,
    )

    result = provider.recommend(
        _context()
    )

    assert calls == ["custom"]

    assert all(
        candidate.score.components.market
        == 77.0
        for candidate in result.candidates
    )


def test_component_builder_no_longer_reads_raw_market_fields():
    provider = RecommendationProvider(
        collector=lambda query, limit: [
            {
                "product_id": "A",
                "product_name": "사과 A",
                "price": 10000,
                "food_intelligence_score": 80,
                "market_score": 100,
                "trend_score": 100,
            }
        ],
        deduplicator=_passthrough,
        normalizer=_passthrough,
        food_enricher=_passthrough,
        market_preparer=_passthrough,
    )

    result = provider.recommend(
        _context()
    )

    candidate = result.candidates[0]

    assert candidate.score.components.market == 0.0

    assert (
        candidate.score.components.is_available(
            "market"
        )
        is False
    )
