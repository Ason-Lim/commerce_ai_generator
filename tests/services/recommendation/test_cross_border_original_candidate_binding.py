from __future__ import annotations

import pytest

from app.services.recommendation.cross_border_candidate_reference_binding import (
    bind_cross_border_candidate_reference,
)
from app.services.recommendation.cross_border_original_candidate_binding import (
    CrossBorderOriginalCandidateBinding,
    bind_cross_border_original_candidate,
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


def test_original_item_is_preserved():
    reference = bind_cross_border_candidate_reference(
        candidate_ref="opaque-cross-border-ref-A",
        candidate_position=1,
        binding_source="test",
    )
    candidate = _candidate(
        product_id="PRODUCT-A",
        rank=1,
    )

    result = bind_cross_border_original_candidate(
        reference_binding=reference,
        candidate=candidate,
    )

    assert result.candidate_ref == (
        "opaque-cross-border-ref-A"
    )
    assert result.candidate_position == 1
    assert result.item == candidate.item
    assert result.item["product_id"] == "PRODUCT-A"


def test_candidate_ref_is_not_product_identity():
    reference = bind_cross_border_candidate_reference(
        candidate_ref="NOT-THE-PRODUCT-ID",
        candidate_position=1,
        binding_source="test",
    )
    candidate = _candidate(
        product_id="ACTUAL-PRODUCT-ID",
        rank=1,
    )

    result = bind_cross_border_original_candidate(
        reference_binding=reference,
        candidate=candidate,
    )

    assert result.candidate_ref == "NOT-THE-PRODUCT-ID"
    assert (
        result.item["product_id"]
        == "ACTUAL-PRODUCT-ID"
    )


def test_item_is_immutable_snapshot():
    source = {
        "product_id": "A",
        "price": 10000,
    }

    binding = CrossBorderOriginalCandidateBinding(
        candidate_ref="opaque-A",
        candidate_position=1,
        item=source,
    )

    source["price"] = 99999

    assert binding.item["price"] == 10000

    with pytest.raises(TypeError):
        binding.item["price"] = 20000


@pytest.mark.parametrize(
    "candidate_ref",
    [
        "",
        " ",
        "\t",
    ],
)
def test_empty_candidate_ref_is_rejected(
    candidate_ref,
):
    with pytest.raises(
        ValueError,
        match="candidate_ref must be non-empty",
    ):
        CrossBorderOriginalCandidateBinding(
            candidate_ref=candidate_ref,
            candidate_position=1,
            item={"product_id": "A"},
        )


@pytest.mark.parametrize(
    "candidate_position",
    [
        0,
        -1,
    ],
)
def test_non_positive_position_is_rejected(
    candidate_position,
):
    with pytest.raises(
        ValueError,
        match=(
            "candidate_position must be greater than zero"
        ),
    ):
        CrossBorderOriginalCandidateBinding(
            candidate_ref="opaque-A",
            candidate_position=candidate_position,
            item={"product_id": "A"},
        )


def test_binding_does_not_expose_scoring_or_activation_state():
    binding = CrossBorderOriginalCandidateBinding(
        candidate_ref="opaque-A",
        candidate_position=1,
        item={"product_id": "A"},
    )

    forbidden = {
        "score",
        "winner",
        "selected",
        "rank",
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
        for name in dir(binding)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(public_names)
