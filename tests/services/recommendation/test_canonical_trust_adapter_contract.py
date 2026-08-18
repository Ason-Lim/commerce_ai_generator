import pytest

from app.services.recommendation.trust_adapter import (
    TrustObservation,
    adapt_trust_evidence,
)


def test_explicit_trust_score_is_preferred():
    observation = adapt_trust_evidence(
        {
            "trust_score": 88,
            "platform_trust_score": 72,
        }
    )

    assert observation == TrustObservation(
        score=88.0,
        available=True,
        source="trust_score",
    )


def test_platform_trust_score_is_accepted_as_trust_specific_evidence():
    observation = adapt_trust_evidence(
        {
            "platform_trust_score": 72,
        }
    )

    assert observation == TrustObservation(
        score=72.0,
        available=True,
        source="platform_trust_score",
    )


@pytest.mark.parametrize(
    "field",
    [
        "platform_boost_score",
        "v7_platform_score",
        "v8_platform_score",
    ],
)
def test_platform_composite_scores_are_not_canonical_trust(
    field,
):
    observation = adapt_trust_evidence(
        {
            field: 95,
        }
    )

    assert observation.available is False
    assert observation.score == 0.0
    assert observation.source is None


def test_identity_score_is_not_canonical_trust():
    observation = adapt_trust_evidence(
        {
            "identity_score": 95,
        }
    )

    assert observation.available is False


def test_reaction_signal_is_not_implicitly_canonical_trust():
    observation = adapt_trust_evidence(
        {
            "reaction_score": 90,
            "click_count": 100,
            "ctr_pct": 20,
        }
    )

    assert observation.available is False


def test_rating_and_review_count_are_not_calculated_inline():
    observation = adapt_trust_evidence(
        {
            "rating": 4.9,
            "review_count": 10000,
        }
    )

    assert observation.available is False


def test_missing_trust_remains_unavailable():
    observation = adapt_trust_evidence(
        {}
    )

    assert observation == TrustObservation()


def test_observed_zero_trust_remains_available():
    observation = adapt_trust_evidence(
        {
            "trust_score": 0,
        }
    )

    assert observation.score == 0.0
    assert observation.available is True
    assert observation.source == "trust_score"


def test_string_trust_value_is_supported():
    observation = adapt_trust_evidence(
        {
            "trust_score": "82.5",
        }
    )

    assert observation.score == 82.5
    assert observation.available is True


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "invalid",
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_invalid_explicit_trust_falls_back_to_platform_trust(
    value,
):
    observation = adapt_trust_evidence(
        {
            "trust_score": value,
            "platform_trust_score": 70,
        }
    )

    assert observation == TrustObservation(
        score=70.0,
        available=True,
        source="platform_trust_score",
    )


def test_trust_scores_are_clamped_to_canonical_range():
    high = adapt_trust_evidence(
        {
            "trust_score": 150,
        }
    )

    low = adapt_trust_evidence(
        {
            "trust_score": -20,
        }
    )

    assert high.score == 100.0
    assert low.score == 0.0

    assert high.available is True
    assert low.available is True


def test_adapter_is_deterministic():
    item = {
        "trust_score": 84,
        "platform_trust_score": 70,
    }

    first = adapt_trust_evidence(
        item
    )

    second = adapt_trust_evidence(
        item
    )

    assert first == second


def test_adapter_does_not_mutate_input():
    item = {
        "trust_score": 84,
        "platform_boost_score": 66.2,
    }

    before = dict(
        item
    )

    adapt_trust_evidence(
        item
    )

    assert item == before


def test_source_provenance_distinguishes_explicit_and_platform_evidence():
    explicit = adapt_trust_evidence(
        {
            "trust_score": 80,
        }
    )

    platform = adapt_trust_evidence(
        {
            "platform_trust_score": 80,
        }
    )

    assert explicit.source == "trust_score"
    assert platform.source == "platform_trust_score"
    assert explicit.source != platform.source
