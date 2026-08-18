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
    prepare_price_utility,
)


def _context(
    priority: str = "price",
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
        },
        {
            "product_id": "B",
            "product_name": "사과 B",
            "price": 12000,
            "food_intelligence_score": 80,
        },
        {
            "product_id": "C",
            "product_name": "사과 C",
            "price": 18000,
            "food_intelligence_score": 80,
        },
    ]


def test_price_preparation_attaches_canonical_price_utility():
    prepared = prepare_price_utility(
        _source()
    )

    assert [
        item["price_score"]
        for item in prepared
    ] == [
        100.0,
        50.0,
        0.0,
    ]


def test_price_preparation_preserves_raw_price_separately():
    prepared = prepare_price_utility(
        _source()
    )

    assert [
        item["_canonical_raw_price"]
        for item in prepared
    ] == [
        10000.0,
        12000.0,
        18000.0,
    ]


def test_price_preparation_does_not_mutate_source():
    source = _source()
    before = deepcopy(
        source
    )

    prepare_price_utility(
        source
    )

    assert source == before


def test_missing_price_does_not_create_price_score():
    prepared = prepare_price_utility(
        [
            {
                "product_id": "A",
            }
        ]
    )

    assert "price_score" not in (
        prepared[0]
    )

    assert "_canonical_raw_price" not in (
        prepared[0]
    )


def test_observed_zero_utility_remains_present():
    prepared = prepare_price_utility(
        [
            {
                "product_id": "A",
                "price": 10000,
            },
            {
                "product_id": "B",
                "price": 20000,
            },
        ]
    )

    assert prepared[
        1
    ]["price_score"] == 0.0


def test_provider_marks_price_available_after_preparation():
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

    assert all(
        candidate.score.components.is_available(
            "price"
        )
        for candidate in result.candidates
    )


def test_provider_price_component_matches_prepared_utility():
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
    ].score.components.price == 100.0

    assert by_id[
        "B"
    ].score.components.price == 50.0

    assert by_id[
        "C"
    ].score.components.price == 0.0


def test_provider_price_priority_orders_by_canonical_price_evidence():
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
            "price"
        )
    )

    assert [
        candidate.item[
            "product_id"
        ]
        for candidate in result.candidates
    ] == [
        "A",
        "B",
        "C",
    ]


def test_provider_calls_price_preparer_after_food_enrichment():
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
        return prepare_price_utility(
            items
        )

    provider = RecommendationProvider(
        collector=collect,
        deduplicator=dedup,
        normalizer=normalize,
        food_enricher=food,
        price_preparer=price,
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
    ]


def test_provider_can_inject_price_preparation_dependency():
    calls = []

    def custom_price_preparer(items):
        calls.append(
            "custom"
        )

        result = []

        for item in items:
            row = dict(
                item
            )
            row[
                "price_score"
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
        price_preparer=custom_price_preparer,
    )

    result = provider.recommend(
        _context()
    )

    assert calls == [
        "custom"
    ]

    assert all(
        candidate.score.components.price
        == 77.0
        for candidate in result.candidates
    )


def test_provider_does_not_calculate_price_utility_inline():
    calls = []

    def price_preparer(items):
        calls.append(
            len(items)
        )

        return prepare_price_utility(
            items
        )

    provider = RecommendationProvider(
        collector=lambda query, limit: deepcopy(
            _source()
        ),
        deduplicator=_passthrough,
        normalizer=_passthrough,
        food_enricher=_passthrough,
        price_preparer=price_preparer,
    )

    provider.recommend(
        _context()
    )

    assert calls == [
        3
    ]
