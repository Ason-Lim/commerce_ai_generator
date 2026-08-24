from decimal import Decimal

import pytest

from app.services.recommendation.cross_border_bound_price_signal_composition import (
    compose_bound_cross_border_price_signals,
)
from app.services.recommendation.cross_border_candidate_component_alignment import (
    CrossBorderCandidateComponentBinding,
    align_cross_border_candidate_components,
)
from app.services.recommendation.cross_border_scoring_binding import (
    BoundCrossBorderScoringInput,
    CrossBorderScoringDirection,
)
from app.services.recommendation.scoring import (
    RecommendationScoreComponents,
)


def _input():
    return BoundCrossBorderScoringInput(
        first_candidate_ref="candidate:first",
        second_candidate_ref="candidate:second",
        first_landed_cost=Decimal("80"),
        second_landed_cost=Decimal("100"),
        currency="USD",
        direction=CrossBorderScoringDirection.FIRST,
        first_evidence_quality="verified",
        second_evidence_quality="verified",
        source_schema_id="test",
        source_schema_version="1",
    )


def _components(
    *,
    quality,
    price,
    trust,
    popularity,
    market,
    identity,
):
    return RecommendationScoreComponents(
        quality=quality,
        price=price,
        trust=trust,
        popularity=popularity,
        market=market,
        identity=identity,
        available=frozenset(
            {
                "quality",
                "price",
                "trust",
                "popularity",
                "market",
                "identity",
            }
        ),
    )


def test_alignment_preserves_candidate_specific_non_price_axes():
    signals = compose_bound_cross_border_price_signals(
        _input()
    )

    first_base = _components(
        quality=91.0,
        price=10.0,
        trust=81.0,
        popularity=71.0,
        market=61.0,
        identity=51.0,
    )
    second_base = _components(
        quality=92.0,
        price=20.0,
        trust=82.0,
        popularity=72.0,
        market=62.0,
        identity=52.0,
    )

    aligned = align_cross_border_candidate_components(
        price_signals=signals,
        first_binding=CrossBorderCandidateComponentBinding(
            candidate_ref="candidate:first",
            base_components=first_base,
        ),
        second_binding=CrossBorderCandidateComponentBinding(
            candidate_ref="candidate:second",
            base_components=second_base,
        ),
    )

    assert aligned.first_components.quality == 91.0
    assert aligned.first_components.trust == 81.0
    assert aligned.first_components.popularity == 71.0
    assert aligned.first_components.market == 61.0
    assert aligned.first_components.identity == 51.0

    assert aligned.second_components.quality == 92.0
    assert aligned.second_components.trust == 82.0
    assert aligned.second_components.popularity == 72.0
    assert aligned.second_components.market == 62.0
    assert aligned.second_components.identity == 52.0


def test_alignment_replaces_only_price_with_cross_border_utility():
    signals = compose_bound_cross_border_price_signals(
        _input()
    )

    first_base = _components(
        quality=90.0,
        price=1.0,
        trust=80.0,
        popularity=70.0,
        market=60.0,
        identity=50.0,
    )
    second_base = _components(
        quality=89.0,
        price=2.0,
        trust=79.0,
        popularity=69.0,
        market=59.0,
        identity=49.0,
    )

    aligned = align_cross_border_candidate_components(
        price_signals=signals,
        first_binding=CrossBorderCandidateComponentBinding(
            candidate_ref="candidate:first",
            base_components=first_base,
        ),
        second_binding=CrossBorderCandidateComponentBinding(
            candidate_ref="candidate:second",
            base_components=second_base,
        ),
    )

    assert (
        aligned.first_components.price
        == signals.first_price.utility
    )
    assert (
        aligned.second_components.price
        == signals.second_price.utility
    )

    assert aligned.first_components is not first_base
    assert aligned.second_components is not second_base

    assert aligned.first_base_components is first_base
    assert aligned.second_base_components is second_base


def test_alignment_preserves_and_adds_price_availability():
    signals = compose_bound_cross_border_price_signals(
        _input()
    )

    first_base = RecommendationScoreComponents(
        quality=90.0,
        price=None,
        trust=80.0,
        popularity=None,
        market=None,
        identity=None,
        available=frozenset(
            {
                "quality",
                "trust",
            }
        ),
    )
    second_base = RecommendationScoreComponents(
        quality=85.0,
        price=None,
        trust=75.0,
        popularity=None,
        market=None,
        identity=None,
        available=frozenset(
            {
                "quality",
                "trust",
            }
        ),
    )

    aligned = align_cross_border_candidate_components(
        price_signals=signals,
        first_binding=CrossBorderCandidateComponentBinding(
            candidate_ref="candidate:first",
            base_components=first_base,
        ),
        second_binding=CrossBorderCandidateComponentBinding(
            candidate_ref="candidate:second",
            base_components=second_base,
        ),
    )

    assert aligned.first_components.available == frozenset(
        {
            "quality",
            "trust",
            "price",
        }
    )
    assert aligned.second_components.available == frozenset(
        {
            "quality",
            "trust",
            "price",
        }
    )


@pytest.mark.parametrize(
    (
        "first_ref",
        "second_ref",
    ),
    [
        (
            "wrong:first",
            "candidate:second",
        ),
        (
            "candidate:first",
            "wrong:second",
        ),
    ],
)
def test_alignment_fails_closed_on_positional_identity_mismatch(
    first_ref,
    second_ref,
):
    signals = compose_bound_cross_border_price_signals(
        _input()
    )
    base = _components(
        quality=90.0,
        price=70.0,
        trust=80.0,
        popularity=60.0,
        market=50.0,
        identity=40.0,
    )

    with pytest.raises(ValueError):
        align_cross_border_candidate_components(
            price_signals=signals,
            first_binding=CrossBorderCandidateComponentBinding(
                candidate_ref=first_ref,
                base_components=base,
            ),
            second_binding=CrossBorderCandidateComponentBinding(
                candidate_ref=second_ref,
                base_components=base,
            ),
        )


def test_binding_rejects_empty_candidate_ref():
    base = _components(
        quality=90.0,
        price=70.0,
        trust=80.0,
        popularity=60.0,
        market=50.0,
        identity=40.0,
    )

    with pytest.raises(
        ValueError,
        match="candidate_ref must be non-empty",
    ):
        CrossBorderCandidateComponentBinding(
            candidate_ref="   ",
            base_components=base,
        )
