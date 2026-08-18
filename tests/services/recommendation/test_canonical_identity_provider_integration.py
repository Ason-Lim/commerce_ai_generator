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
    prepare_identity_evidence,
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
            "identity_score": 90,
        },
        {
            "product_id": "B",
            "product_name": "사과 B",
            "price": 12000,
            "food_intelligence_score": 80,
            "_identity_score": 70,
        },
        {
            "product_id": "C",
            "product_name": "사과 C",
            "price": 15000,
            "food_intelligence_score": 80,
            "_identity_validation": {
                "identity_score": 60,
            },
        },
        {
            "product_id": "D",
            "product_name": "사과 D",
            "price": 18000,
            "food_intelligence_score": 80,
            "identity_cluster_confidence": 95,
        },
    ]


def test_identity_preparation_attaches_canonical_identity():
    prepared = prepare_identity_evidence(
        [
            {
                "identity_score": 88,
            }
        ]
    )

    assert (
        prepared[0][
            "_canonical_identity_score"
        ]
        == 88.0
    )


def test_identity_preparation_accepts_legacy_score_fallback():
    prepared = prepare_identity_evidence(
        [
            {
                "_identity_score": 72,
            }
        ]
    )

    assert (
        prepared[0][
            "_canonical_identity_score"
        ]
        == 72.0
    )


def test_identity_preparation_accepts_validation_fallback():
    prepared = prepare_identity_evidence(
        [
            {
                "_identity_validation": {
                    "identity_score": 66,
                },
            }
        ]
    )

    assert (
        prepared[0][
            "_canonical_identity_score"
        ]
        == 66.0
    )


def test_observed_zero_identity_is_preserved():
    prepared = prepare_identity_evidence(
        [
            {
                "identity_score": 0,
                "_identity_score": 90,
            }
        ]
    )

    assert (
        prepared[0][
            "_canonical_identity_score"
        ]
        == 0.0
    )


def test_out_of_range_identity_is_clamped():
    prepared = prepare_identity_evidence(
        [
            {
                "identity_score": 150,
            },
            {
                "identity_score": -10,
            },
        ]
    )

    assert prepared[0][
        "_canonical_identity_score"
    ] == 100.0

    assert prepared[1][
        "_canonical_identity_score"
    ] == 0.0


def test_noncanonical_identity_confidence_does_not_create_identity():
    prepared = prepare_identity_evidence(
        [
            {
                "identity_cluster_confidence": 95,
                "product_family_confidence": 95,
                "market_cluster_confidence": 95,
            }
        ]
    )

    assert (
        "_canonical_identity_score"
        not in prepared[0]
    )


def test_identity_preparation_does_not_mutate_source():
    source = _source()
    before = deepcopy(source)

    prepare_identity_evidence(
        source
    )

    assert source == before


def test_provider_marks_primary_identity_available():
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
        "identity"
    )

    assert (
        by_id["A"].score.components.identity
        == 90.0
    )


def test_provider_marks_legacy_identity_available():
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
        "B"
    ].score.components.is_available(
        "identity"
    )

    assert (
        by_id["B"].score.components.identity
        == 70.0
    )


def test_provider_marks_validation_identity_available():
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
        by_id["C"].score.components.identity
        == 60.0
    )

    assert by_id[
        "C"
    ].score.components.is_available(
        "identity"
    )


def test_provider_keeps_noncanonical_identity_confidence_unavailable():
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
        by_id["D"].score.components.is_available(
            "identity"
        )
        is False
    )


def test_provider_calls_identity_after_market():
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
        identity_preparer=stage("identity"),
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
        "identity",
    ]


def test_provider_can_inject_identity_preparer():
    calls = []

    def custom_identity(items):
        calls.append("custom")

        prepared = []

        for item in items:
            row = dict(item)
            row[
                "_canonical_identity_score"
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
        identity_preparer=custom_identity,
    )

    result = provider.recommend(
        _context()
    )

    assert calls == ["custom"]

    assert all(
        candidate.score.components.identity
        == 77.0
        for candidate in result.candidates
    )


def test_component_builder_no_longer_reads_raw_identity_fields():
    provider = RecommendationProvider(
        collector=lambda query, limit: [
            {
                "product_id": "A",
                "product_name": "사과 A",
                "price": 10000,
                "food_intelligence_score": 80,
                "identity_score": 100,
                "_identity_score": 100,
                "_identity_validation": {
                    "identity_score": 100,
                },
            }
        ],
        deduplicator=_passthrough,
        normalizer=_passthrough,
        food_enricher=_passthrough,
        identity_preparer=_passthrough,
    )

    result = provider.recommend(
        _context()
    )

    candidate = result.candidates[0]

    assert candidate.score.components.identity == 0.0

    assert (
        candidate.score.components.is_available(
            "identity"
        )
        is False
    )
