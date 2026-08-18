from copy import deepcopy

import pytest

from app.services.recommendation.models import (
    RecommendationPriority,
)

from app.services.recommendation.ranking import (
    rank_candidates,
)

from app.services.recommendation_pipeline import (
    apply_priority_sort,
)


def _items() -> list[dict]:
    return [
        {
            "product_id": "A",
            "price": 20000,
            "v7_final_score": 80,
            "v7_quality_score": 60,
            "v7_platform_score": 70,
        },
        {
            "product_id": "B",
            "price": 30000,
            "v7_final_score": 80,
            "v7_quality_score": 90,
            "v7_platform_score": 80,
        },
        {
            "product_id": "C",
            "price": 10000,
            "v7_final_score": 70,
            "v7_quality_score": 95,
            "v7_platform_score": 95,
        },
    ]


def _canonical_rank(
    items: list[dict],
    priority: RecommendationPriority,
) -> list[dict]:
    return rank_candidates(
        items,
        priority,
        final_score=lambda item: item.get(
            "v7_final_score"
        ),
        price=lambda item: item.get(
            "price"
        ),
        quality_score=lambda item: item.get(
            "v7_quality_score"
        ),
        trust_signal=lambda item: item.get(
            "v7_platform_score"
        ),
    )


@pytest.mark.parametrize(
    (
        "legacy_priority",
        "canonical_priority",
    ),
    [
        (
            "ranking",
            RecommendationPriority.MIX,
        ),
        (
            "price",
            RecommendationPriority.PRICE,
        ),
        (
            "quality",
            RecommendationPriority.QUALITY,
        ),
        (
            "trust",
            RecommendationPriority.TRUST,
        ),
        (
            "exploration",
            RecommendationPriority.EXPLORATION,
        ),
        (
            "discovery",
            RecommendationPriority.DISCOVERY,
        ),
        (
            "revisit",
            RecommendationPriority.REVISIT,
        ),
    ],
)
def test_canonical_ranking_matches_pipeline_priority_order(
    legacy_priority: str,
    canonical_priority: RecommendationPriority,
) -> None:
    source = _items()

    legacy = apply_priority_sort(
        deepcopy(source),
        legacy_priority,
    )

    canonical = _canonical_rank(
        deepcopy(source),
        canonical_priority,
    )

    assert [
        item["product_id"]
        for item in canonical
    ] == [
        item["product_id"]
        for item in legacy
    ]


def test_mix_ranking_uses_final_score_descending() -> None:
    ranked = _canonical_rank(
        _items(),
        RecommendationPriority.MIX,
    )

    assert [
        item["product_id"]
        for item in ranked
    ] == [
        "A",
        "B",
        "C",
    ]


def test_price_ranking_uses_price_then_final_score() -> None:
    ranked = _canonical_rank(
        _items(),
        RecommendationPriority.PRICE,
    )

    assert [
        item["product_id"]
        for item in ranked
    ] == [
        "C",
        "A",
        "B",
    ]


def test_quality_ranking_uses_quality_then_final_score() -> None:
    ranked = _canonical_rank(
        _items(),
        RecommendationPriority.QUALITY,
    )

    assert [
        item["product_id"]
        for item in ranked
    ] == [
        "C",
        "B",
        "A",
    ]


def test_trust_ranking_uses_caller_supplied_trust_signal() -> None:
    ranked = _canonical_rank(
        _items(),
        RecommendationPriority.TRUST,
    )

    assert [
        item["product_id"]
        for item in ranked
    ] == [
        "C",
        "B",
        "A",
    ]


@pytest.mark.parametrize(
    "priority",
    [
        RecommendationPriority.MIX,
        RecommendationPriority.EXPLORATION,
        RecommendationPriority.DISCOVERY,
        RecommendationPriority.REVISIT,
    ],
)
def test_default_modes_share_final_score_order(
    priority: RecommendationPriority,
) -> None:
    ranked = _canonical_rank(
        _items(),
        priority,
    )

    assert [
        item["product_id"]
        for item in ranked
    ] == [
        "A",
        "B",
        "C",
    ]


def test_complete_tie_preserves_input_order() -> None:
    items = [
        {
            "id": "A",
            "score": 80,
        },
        {
            "id": "B",
            "score": 80,
        },
        {
            "id": "C",
            "score": 80,
        },
    ]

    ranked = rank_candidates(
        items,
        RecommendationPriority.MIX,
        final_score=lambda item: item[
            "score"
        ],
    )

    assert [
        item["id"]
        for item in ranked
    ] == [
        "A",
        "B",
        "C",
    ]


def test_ranking_does_not_mutate_input_list_or_items() -> None:
    items = _items()
    before = deepcopy(items)

    ranked = _canonical_rank(
        items,
        RecommendationPriority.QUALITY,
    )

    assert items == before

    assert {
        item["product_id"]
        for item in ranked
    } == {
        item["product_id"]
        for item in items
    }


def test_ranking_uses_accessors_not_legacy_field_ownership() -> None:
    items = [
        {
            "id": "A",
            "canonical": 40,
        },
        {
            "id": "B",
            "canonical": 90,
        },
    ]

    ranked = rank_candidates(
        items,
        RecommendationPriority.MIX,
        final_score=lambda item: item[
            "canonical"
        ],
    )

    assert [
        item["id"]
        for item in ranked
    ] == [
        "B",
        "A",
    ]


def test_price_priority_requires_price_accessor() -> None:
    with pytest.raises(
        ValueError,
        match="price accessor",
    ):
        rank_candidates(
            [],
            RecommendationPriority.PRICE,
            final_score=lambda item: 0,
        )


def test_quality_priority_requires_quality_accessor() -> None:
    with pytest.raises(
        ValueError,
        match="quality_score accessor",
    ):
        rank_candidates(
            [],
            RecommendationPriority.QUALITY,
            final_score=lambda item: 0,
        )


def test_trust_priority_requires_trust_signal_accessor() -> None:
    with pytest.raises(
        ValueError,
        match="trust_signal accessor",
    ):
        rank_candidates(
            [],
            RecommendationPriority.TRUST,
            final_score=lambda item: 0,
        )


def test_missing_price_sorts_after_valid_prices() -> None:
    items = [
        {
            "id": "missing",
            "price": None,
            "score": 100,
        },
        {
            "id": "priced",
            "price": 10000,
            "score": 50,
        },
    ]

    ranked = rank_candidates(
        items,
        RecommendationPriority.PRICE,
        final_score=lambda item: item[
            "score"
        ],
        price=lambda item: item[
            "price"
        ],
    )

    assert [
        item["id"]
        for item in ranked
    ] == [
        "priced",
        "missing",
    ]
