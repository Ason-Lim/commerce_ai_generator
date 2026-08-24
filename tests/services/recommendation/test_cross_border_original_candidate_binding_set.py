from __future__ import annotations

import pytest

from app.services.recommendation.cross_border_candidate_reference_binding import (
    bind_cross_border_candidate_reference,
)
from app.services.recommendation.cross_border_candidate_reference_binding_set import (
    CrossBorderCandidateReferenceBindingSet,
)
from app.services.recommendation.cross_border_original_candidate_binding import (
    CrossBorderOriginalCandidateBinding,
)
from app.services.recommendation.cross_border_original_candidate_binding_set import (
    CrossBorderOriginalCandidateBindingSet,
    bind_cross_border_original_candidate_set,
)
from app.services.recommendation.models import (
    RecommendationCandidate,
    RecommendationPriority,
    RecommendationScoreComponents,
    RecommendationScoreResult,
)


def _candidate(
    *,
    product_id: str,
    rank: int,
) -> RecommendationCandidate:
    return RecommendationCandidate(
        item={
            "product_id": product_id,
            "product_name": f"상품 {product_id}",
            "price": 10000 + rank,
        },
        score=RecommendationScoreResult(
            final_score=80.0,
            priority=RecommendationPriority.MIX,
            components=RecommendationScoreComponents(),
        ),
        rank=rank,
    )


def _reference_set():
    return CrossBorderCandidateReferenceBindingSet(
        bindings=(
            bind_cross_border_candidate_reference(
                candidate_ref="opaque-ref-1",
                candidate_position=1,
                binding_source="test",
            ),
            bind_cross_border_candidate_reference(
                candidate_ref="opaque-ref-2",
                candidate_position=2,
                binding_source="test",
            ),
        )
    )


def test_pairwise_original_items_are_preserved_by_position():
    candidates = (
        _candidate(
            product_id="PRODUCT-A",
            rank=1,
        ),
        _candidate(
            product_id="PRODUCT-B",
            rank=2,
        ),
    )

    result = bind_cross_border_original_candidate_set(
        reference_binding_set=_reference_set(),
        candidates=candidates,
    )

    assert len(result.bindings) == 2

    first, second = result.bindings

    assert first.candidate_position == 1
    assert first.candidate_ref == "opaque-ref-1"
    assert first.item["product_id"] == "PRODUCT-A"

    assert second.candidate_position == 2
    assert second.candidate_ref == "opaque-ref-2"
    assert second.item["product_id"] == "PRODUCT-B"


def test_candidate_refs_are_not_product_identity():
    candidates = (
        _candidate(
            product_id="ACTUAL-A",
            rank=1,
        ),
        _candidate(
            product_id="ACTUAL-B",
            rank=2,
        ),
    )

    result = bind_cross_border_original_candidate_set(
        reference_binding_set=_reference_set(),
        candidates=candidates,
    )

    first, second = result.bindings

    assert first.candidate_ref == "opaque-ref-1"
    assert first.item["product_id"] == "ACTUAL-A"

    assert second.candidate_ref == "opaque-ref-2"
    assert second.item["product_id"] == "ACTUAL-B"


@pytest.mark.parametrize(
    "candidates",
    [
        (),
        (_candidate(product_id="A", rank=1),),
        (
            _candidate(product_id="A", rank=1),
            _candidate(product_id="B", rank=2),
            _candidate(product_id="C", rank=3),
        ),
    ],
)
def test_non_pair_candidate_sequence_is_rejected(
    candidates,
):
    with pytest.raises(
        ValueError,
        match="exactly two recommendation candidates are required",
    ):
        bind_cross_border_original_candidate_set(
            reference_binding_set=_reference_set(),
            candidates=candidates,
        )


def test_binding_set_rejects_duplicate_positions():
    with pytest.raises(
        ValueError,
        match=(
            "original candidate binding positions "
            "must be exactly"
        ),
    ):
        CrossBorderOriginalCandidateBindingSet(
            bindings=(
                CrossBorderOriginalCandidateBinding(
                    candidate_ref="opaque-A",
                    candidate_position=1,
                    item={"product_id": "A"},
                ),
                CrossBorderOriginalCandidateBinding(
                    candidate_ref="opaque-B",
                    candidate_position=1,
                    item={"product_id": "B"},
                ),
            )
        )


def test_binding_set_orders_positions_deterministically():
    result = CrossBorderOriginalCandidateBindingSet(
        bindings=(
            CrossBorderOriginalCandidateBinding(
                candidate_ref="opaque-B",
                candidate_position=2,
                item={"product_id": "B"},
            ),
            CrossBorderOriginalCandidateBinding(
                candidate_ref="opaque-A",
                candidate_position=1,
                item={"product_id": "A"},
            ),
        )
    )

    assert tuple(
        binding.candidate_position
        for binding in result.bindings
    ) == (1, 2)


def test_pairwise_binding_does_not_expose_activation_state():
    result = bind_cross_border_original_candidate_set(
        reference_binding_set=_reference_set(),
        candidates=(
            _candidate(product_id="A", rank=1),
            _candidate(product_id="B", rank=2),
        ),
    )

    forbidden = {
        "winner",
        "selected",
        "production_enabled",
        "rollout_started",
        "route_traffic",
        "shipping_route",
        "payment",
        "purchase",
        "dispatch",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(public_names)
