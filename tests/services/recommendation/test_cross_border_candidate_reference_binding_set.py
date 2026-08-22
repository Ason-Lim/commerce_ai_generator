from dataclasses import FrozenInstanceError

import pytest

from app.services.recommendation.cross_border_candidate_reference_binding import (
    bind_cross_border_candidate_reference,
)
from app.services.recommendation.cross_border_candidate_reference_binding_set import (
    CrossBorderCandidateReferenceBindingSet,
    validate_cross_border_candidate_reference_bindings,
)


def _binding(
    candidate_ref: str,
    candidate_position: int,
    *,
    source: str = "cross_border_handoff",
):
    return bind_cross_border_candidate_reference(
        candidate_ref=candidate_ref,
        candidate_position=candidate_position,
        binding_source=source,
    )


def test_valid_pair_is_accepted():
    first = _binding(
        "candidate:first",
        1,
    )
    second = _binding(
        "candidate:second",
        2,
    )

    result = (
        validate_cross_border_candidate_reference_bindings(
            (first, second)
        )
    )

    assert isinstance(
        result,
        CrossBorderCandidateReferenceBindingSet,
    )
    assert result.bindings == (
        first,
        second,
    )


def test_input_order_is_preserved():
    first = _binding(
        "candidate:first",
        1,
    )
    second = _binding(
        "candidate:second",
        2,
    )

    result = (
        validate_cross_border_candidate_reference_bindings(
            (second, first)
        )
    )

    assert result.bindings == (
        second,
        first,
    )


def test_tuple_order_does_not_define_candidate_position():
    position_two = _binding(
        "candidate:second",
        2,
    )
    position_one = _binding(
        "candidate:first",
        1,
    )

    result = (
        validate_cross_border_candidate_reference_bindings(
            (position_two, position_one)
        )
    )

    assert (
        result.bindings[0].candidate_position
        == 2
    )
    assert (
        result.bindings[1].candidate_position
        == 1
    )


@pytest.mark.parametrize(
    "bindings",
    [
        (),
        (
            _binding(
                "candidate:first",
                1,
            ),
        ),
        (
            _binding(
                "candidate:first",
                1,
            ),
            _binding(
                "candidate:second",
                2,
            ),
            _binding(
                "candidate:third",
                3,
            ),
        ),
    ],
)
def test_binding_set_requires_exactly_two_bindings(
    bindings,
):
    with pytest.raises(
        ValueError,
        match="exactly two bindings",
    ):
        validate_cross_border_candidate_reference_bindings(
            bindings
        )


def test_duplicate_candidate_references_are_rejected():
    with pytest.raises(
        ValueError,
        match="candidate_ref values must be unique",
    ):
        validate_cross_border_candidate_reference_bindings(
            (
                _binding(
                    "candidate:same",
                    1,
                ),
                _binding(
                    "candidate:same",
                    2,
                ),
            )
        )


def test_duplicate_candidate_references_after_normalization_are_rejected():
    with pytest.raises(
        ValueError,
        match="candidate_ref values must be unique",
    ):
        validate_cross_border_candidate_reference_bindings(
            (
                _binding(
                    " candidate:same ",
                    1,
                ),
                _binding(
                    "candidate:same",
                    2,
                ),
            )
        )


def test_duplicate_candidate_positions_are_rejected():
    with pytest.raises(
        ValueError,
        match="candidate_position values must be unique",
    ):
        validate_cross_border_candidate_reference_bindings(
            (
                _binding(
                    "candidate:first",
                    1,
                ),
                _binding(
                    "candidate:second",
                    1,
                ),
            )
        )


@pytest.mark.parametrize(
    "positions",
    [
        (1, 3),
        (2, 3),
        (3, 4),
    ],
)
def test_positions_must_cover_one_and_two(
    positions,
):
    with pytest.raises(
        ValueError,
        match=(
            "candidate_position values must cover "
            "positions 1 and 2"
        ),
    ):
        validate_cross_border_candidate_reference_bindings(
            (
                _binding(
                    "candidate:first",
                    positions[0],
                ),
                _binding(
                    "candidate:second",
                    positions[1],
                ),
            )
        )


def test_distinct_binding_sources_are_preserved():
    first = _binding(
        "candidate:first",
        1,
        source="source:a",
    )
    second = _binding(
        "candidate:second",
        2,
        source="source:b",
    )

    result = (
        validate_cross_border_candidate_reference_bindings(
            (first, second)
        )
    )

    assert (
        result.bindings[0].binding_source
        == "source:a"
    )
    assert (
        result.bindings[1].binding_source
        == "source:b"
    )


def test_binding_set_is_immutable():
    result = (
        validate_cross_border_candidate_reference_bindings(
            (
                _binding(
                    "candidate:first",
                    1,
                ),
                _binding(
                    "candidate:second",
                    2,
                ),
            )
        )
    )

    with pytest.raises(FrozenInstanceError):
        result.bindings = ()


def test_binding_set_does_not_expose_identity_authority():
    result = (
        validate_cross_border_candidate_reference_bindings(
            (
                _binding(
                    "amazon-us:offer:123",
                    1,
                ),
                _binding(
                    "korea-direct:offer:456",
                    2,
                ),
            )
        )
    )

    assert not hasattr(result, "product_id")
    assert not hasattr(
        result,
        "product_identity_key",
    )
    assert not hasattr(result, "listing_id")
    assert not hasattr(result, "offer_id")
    assert not hasattr(result, "product_url")


def test_binding_set_does_not_expose_scoring_or_ranking_authority():
    result = (
        validate_cross_border_candidate_reference_bindings(
            (
                _binding(
                    "candidate:first",
                    1,
                ),
                _binding(
                    "candidate:second",
                    2,
                ),
            )
        )
    )

    assert not hasattr(result, "rank")
    assert not hasattr(result, "score")
    assert not hasattr(result, "final_score")
    assert not hasattr(result, "selected")
    assert not hasattr(result, "recommended")
