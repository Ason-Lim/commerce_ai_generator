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
    prepare_trust_evidence,
)


def _context(
    priority: str = "trust",
):
    return build_recommendation_context(
        parse_recommendation_query(
            "사과"
        ),
        resolve_recommendation_policy(
            priority
        ),
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
            "trust_score": 90,
        },
        {
            "product_id": "B",
            "product_name": "사과 B",
            "price": 12000,
            "food_intelligence_score": 80,
            "platform_trust_score": 70,
        },
        {
            "product_id": "C",
            "product_name": "사과 C",
            "price": 18000,
            "food_intelligence_score": 80,
            "platform_boost_score": 99,
        },
    ]


def test_trust_preparation_attaches_explicit_trust():
    prepared = prepare_trust_evidence(
        [
            {
                "trust_score": 88,
            }
        ]
    )

    assert prepared[
        0
    ][
        "_canonical_trust_score"
    ] == 88.0

    assert prepared[
        0
    ][
        "_canonical_trust_source"
    ] == "trust_score"


def test_trust_preparation_accepts_platform_trust_specific_evidence():
    prepared = prepare_trust_evidence(
        [
            {
                "platform_trust_score": 72,
            }
        ]
    )

    assert prepared[
        0
    ][
        "_canonical_trust_score"
    ] == 72.0

    assert prepared[
        0
    ][
        "_canonical_trust_source"
    ] == "platform_trust_score"


def test_platform_boost_does_not_create_canonical_trust():
    prepared = prepare_trust_evidence(
        [
            {
                "platform_boost_score": 99,
            }
        ]
    )

    assert (
        "_canonical_trust_score"
        not in prepared[0]
    )

    assert (
        "_canonical_trust_source"
        not in prepared[0]
    )


def test_v7_v8_platform_scores_do_not_create_canonical_trust():
    prepared = prepare_trust_evidence(
        [
            {
                "v7_platform_score": 90,
                "v8_platform_score": 95,
            }
        ]
    )

    assert (
        "_canonical_trust_score"
        not in prepared[0]
    )


def test_identity_does_not_create_canonical_trust():
    prepared = prepare_trust_evidence(
        [
            {
                "identity_score": 95,
            }
        ]
    )

    assert (
        "_canonical_trust_score"
        not in prepared[0]
    )


def test_trust_preparation_does_not_mutate_source():
    source = _source()

    before = deepcopy(
        source
    )

    prepare_trust_evidence(
        source
    )

    assert source == before


def test_provider_marks_explicit_trust_available():
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
        "trust"
    )

    assert by_id[
        "A"
    ].score.components.trust == 90.0


def test_provider_marks_platform_trust_available():
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
        "trust"
    )

    assert by_id[
        "B"
    ].score.components.trust == 70.0


def test_provider_keeps_composite_platform_only_trust_unavailable():
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
        "C"
    ].score.components.is_available(
        "trust"
    ) is False


def test_provider_trust_priority_prefers_higher_canonical_trust():
    provider = RecommendationProvider(
        collector=lambda query, limit: deepcopy(
            _source()
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

    ids = [
        candidate.item[
            "product_id"
        ]
        for candidate in result.candidates
    ]

    assert ids.index(
        "A"
    ) < ids.index(
        "B"
    )


def test_provider_calls_trust_preparer_after_price_preparer():
    calls = []

    def collect(query, limit):
        calls.append(
            "collect"
        )
        return _source()

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

    def food(items):
        calls.append(
            "food"
        )
        return _passthrough(
            items
        )

    def price(items):
        calls.append(
            "price"
        )
        return _passthrough(
            items
        )

    def trust(items):
        calls.append(
            "trust"
        )
        return prepare_trust_evidence(
            items
        )

    provider = RecommendationProvider(
        collector=collect,
        deduplicator=dedup,
        normalizer=normalize,
        food_enricher=food,
        price_preparer=price,
        trust_preparer=trust,
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
    ]


def test_provider_can_inject_trust_preparer():
    calls = []

    def custom_trust(items):
        calls.append(
            "custom"
        )

        result = []

        for item in items:
            row = dict(
                item
            )
            row[
                "_canonical_trust_score"
            ] = 77.0
            row[
                "_canonical_trust_source"
            ] = "test"
            result.append(
                row
            )

        return result

    provider = RecommendationProvider(
        collector=lambda query, limit: deepcopy(
            _source()
        ),
        deduplicator=_passthrough,
        normalizer=_passthrough,
        food_enricher=_passthrough,
        trust_preparer=custom_trust,
    )

    result = provider.recommend(
        _context()
    )

    assert calls == [
        "custom"
    ]

    assert all(
        candidate.score.components.trust
        == 77.0
        for candidate in result.candidates
    )


def test_provider_no_longer_reads_platform_composite_as_trust():
    provider = RecommendationProvider(
        collector=lambda query, limit: [
            {
                "product_id": "A",
                "product_name": "사과 A",
                "price": 10000,
                "food_intelligence_score": 80,
                "platform_boost_score": 100,
                "v7_platform_score": 100,
                "v8_platform_score": 100,
            }
        ],
        deduplicator=_passthrough,
        normalizer=_passthrough,
        food_enricher=_passthrough,
    )

    result = provider.recommend(
        _context()
    )

    candidate = result.candidates[
        0
    ]

    assert candidate.score.components.trust == 0.0

    assert candidate.score.components.is_available(
        "trust"
    ) is False
