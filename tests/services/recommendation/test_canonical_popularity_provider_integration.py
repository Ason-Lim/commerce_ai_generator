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
    prepare_popularity_evidence,
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
            "popularity_score": 90,
        },
        {
            "product_id": "B",
            "product_name": "사과 B",
            "price": 12000,
            "food_intelligence_score": 80,
            "reaction_score": 70,
        },
        {
            "product_id": "C",
            "product_name": "사과 C",
            "price": 18000,
            "food_intelligence_score": 80,
            "click_count": 100,
            "ctr_pct": 20,
            "review_count": 10000,
            "purchase_count": 5000,
        },
    ]


def test_popularity_preparation_attaches_popularity_score():
    prepared = prepare_popularity_evidence(
        [
            {
                "popularity_score": 88,
            }
        ]
    )

    assert prepared[
        0
    ][
        "_canonical_popularity_score"
    ] == 88.0


def test_popularity_preparation_accepts_reaction_fallback():
    prepared = prepare_popularity_evidence(
        [
            {
                "reaction_score": 72,
            }
        ]
    )

    assert prepared[
        0
    ][
        "_canonical_popularity_score"
    ] == 72.0


def test_popularity_score_has_precedence():
    prepared = prepare_popularity_evidence(
        [
            {
                "popularity_score": 80,
                "reaction_score": 95,
            }
        ]
    )

    assert prepared[
        0
    ][
        "_canonical_popularity_score"
    ] == 80.0


def test_observed_zero_popularity_is_preserved():
    prepared = prepare_popularity_evidence(
        [
            {
                "popularity_score": 0,
                "reaction_score": 90,
            }
        ]
    )

    assert (
        prepared[0][
            "_canonical_popularity_score"
        ]
        == 0.0
    )


def test_raw_engagement_does_not_create_popularity_inline():
    prepared = prepare_popularity_evidence(
        [
            {
                "click_count": 100,
                "ctr_pct": 20,
                "impression_count": 500,
            }
        ]
    )

    assert (
        "_canonical_popularity_score"
        not in prepared[0]
    )


def test_review_and_rating_do_not_create_popularity_inline():
    prepared = prepare_popularity_evidence(
        [
            {
                "review_count": 10000,
                "rating": 4.9,
            }
        ]
    )

    assert (
        "_canonical_popularity_score"
        not in prepared[0]
    )


def test_purchase_and_market_signal_do_not_create_popularity_inline():
    prepared = prepare_popularity_evidence(
        [
            {
                "purchase_count": 5000,
                "market_signal_score": 90,
            }
        ]
    )

    assert (
        "_canonical_popularity_score"
        not in prepared[0]
    )


def test_popularity_preparation_does_not_mutate_source():
    source = _source()

    before = deepcopy(
        source
    )

    prepare_popularity_evidence(
        source
    )

    assert source == before


def test_provider_marks_popularity_score_available():
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
        "popularity"
    )

    assert by_id[
        "A"
    ].score.components.popularity == 90.0


def test_provider_marks_reaction_fallback_available():
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
        "popularity"
    )

    assert by_id[
        "B"
    ].score.components.popularity == 70.0


def test_provider_keeps_raw_behavior_only_popularity_unavailable():
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
        "popularity"
    ) is False


def test_provider_calls_popularity_after_trust():
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
        return _passthrough(
            items
        )

    def popularity(items):
        calls.append(
            "popularity"
        )
        return prepare_popularity_evidence(
            items
        )

    provider = RecommendationProvider(
        collector=collect,
        deduplicator=dedup,
        normalizer=normalize,
        food_enricher=food,
        price_preparer=price,
        trust_preparer=trust,
        popularity_preparer=popularity,
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
    ]


def test_provider_can_inject_popularity_preparer():
    calls = []

    def custom_popularity(items):
        calls.append(
            "custom"
        )

        result = []

        for item in items:
            row = dict(
                item
            )
            row[
                "_canonical_popularity_score"
            ] = 77.0

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
        popularity_preparer=custom_popularity,
    )

    result = provider.recommend(
        _context()
    )

    assert calls == [
        "custom"
    ]

    assert all(
        candidate.score.components.popularity
        == 77.0
        for candidate in result.candidates
    )


def test_build_score_components_no_longer_reads_raw_popularity_fields():
    provider = RecommendationProvider(
        collector=lambda query, limit: [
            {
                "product_id": "A",
                "product_name": "사과 A",
                "price": 10000,
                "food_intelligence_score": 80,
                "popularity_score": 100,
                "reaction_score": 100,
            }
        ],
        deduplicator=_passthrough,
        normalizer=_passthrough,
        food_enricher=_passthrough,
        popularity_preparer=_passthrough,
    )

    result = provider.recommend(
        _context()
    )

    candidate = result.candidates[
        0
    ]

    assert candidate.score.components.popularity == 0.0

    assert candidate.score.components.is_available(
        "popularity"
    ) is False
