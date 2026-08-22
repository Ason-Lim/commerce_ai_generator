from dataclasses import FrozenInstanceError

import pytest

from app.services.recommendation.cross_border_candidate_reference_binding import (
    CrossBorderCandidateReferenceBinding,
    bind_cross_border_candidate_reference,
)


def test_binding_preserves_explicit_reference_and_position():
    binding = bind_cross_border_candidate_reference(
        candidate_ref="amazon-us:offer:123",
        candidate_position=1,
        binding_source="cross_border_handoff",
    )

    assert isinstance(
        binding,
        CrossBorderCandidateReferenceBinding,
    )
    assert binding.candidate_ref == (
        "amazon-us:offer:123"
    )
    assert binding.candidate_position == 1
    assert binding.binding_source == (
        "cross_border_handoff"
    )


def test_binding_normalizes_reference_whitespace():
    binding = bind_cross_border_candidate_reference(
        candidate_ref="  candidate:first  ",
        candidate_position=2,
        binding_source="cross_border_handoff",
    )

    assert binding.candidate_ref == "candidate:first"


def test_binding_normalizes_source_whitespace():
    binding = bind_cross_border_candidate_reference(
        candidate_ref="candidate:first",
        candidate_position=1,
        binding_source="  explicit_handoff  ",
    )

    assert binding.binding_source == "explicit_handoff"


@pytest.mark.parametrize(
    "candidate_ref",
    [
        "",
        " ",
        "\t",
        "\n",
    ],
)
def test_binding_rejects_empty_candidate_reference(
    candidate_ref,
):
    with pytest.raises(
        ValueError,
        match="candidate_ref must be non-empty",
    ):
        bind_cross_border_candidate_reference(
            candidate_ref=candidate_ref,
            candidate_position=1,
            binding_source="cross_border_handoff",
        )


@pytest.mark.parametrize(
    "candidate_position",
    [
        0,
        -1,
        -100,
    ],
)
def test_binding_rejects_non_positive_candidate_position(
    candidate_position,
):
    with pytest.raises(
        ValueError,
        match=(
            "candidate_position must be greater than zero"
        ),
    ):
        bind_cross_border_candidate_reference(
            candidate_ref="candidate:first",
            candidate_position=candidate_position,
            binding_source="cross_border_handoff",
        )


@pytest.mark.parametrize(
    "binding_source",
    [
        "",
        " ",
        "\t",
        "\n",
    ],
)
def test_binding_rejects_empty_binding_source(
    binding_source,
):
    with pytest.raises(
        ValueError,
        match="binding_source must be non-empty",
    ):
        bind_cross_border_candidate_reference(
            candidate_ref="candidate:first",
            candidate_position=1,
            binding_source=binding_source,
        )


def test_binding_is_immutable():
    binding = bind_cross_border_candidate_reference(
        candidate_ref="candidate:first",
        candidate_position=1,
        binding_source="cross_border_handoff",
    )

    with pytest.raises(FrozenInstanceError):
        binding.candidate_position = 2


def test_same_reference_may_be_explicitly_bound_to_different_positions():
    first = bind_cross_border_candidate_reference(
        candidate_ref="candidate:first",
        candidate_position=1,
        binding_source="source:a",
    )
    second = bind_cross_border_candidate_reference(
        candidate_ref="candidate:first",
        candidate_position=2,
        binding_source="source:b",
    )

    assert first.candidate_ref == second.candidate_ref
    assert (
        first.candidate_position
        != second.candidate_position
    )


def test_reference_is_not_reinterpreted_as_product_identity():
    binding = bind_cross_border_candidate_reference(
        candidate_ref="amazon-us:offer:123",
        candidate_position=1,
        binding_source="cross_border_handoff",
    )

    assert not hasattr(binding, "product_id")
    assert not hasattr(
        binding,
        "product_identity_key",
    )
    assert not hasattr(binding, "product_url")
    assert not hasattr(binding, "listing_id")
    assert not hasattr(binding, "offer_id")


def test_binding_does_not_expose_ranking_or_scoring_authority():
    binding = bind_cross_border_candidate_reference(
        candidate_ref="candidate:first",
        candidate_position=1,
        binding_source="cross_border_handoff",
    )

    assert not hasattr(binding, "rank")
    assert not hasattr(binding, "score")
    assert not hasattr(binding, "final_score")
    assert not hasattr(binding, "selected")
    assert not hasattr(binding, "recommended")


def test_distinct_references_remain_distinct():
    first = bind_cross_border_candidate_reference(
        candidate_ref="amazon-us:offer:123",
        candidate_position=1,
        binding_source="cross_border_handoff",
    )
    second = bind_cross_border_candidate_reference(
        candidate_ref="korea-direct:offer:456",
        candidate_position=2,
        binding_source="cross_border_handoff",
    )

    assert first.candidate_ref != second.candidate_ref
    assert first != second
