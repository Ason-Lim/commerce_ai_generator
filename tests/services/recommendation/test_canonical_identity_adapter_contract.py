import pytest

from app.services.recommendation.identity_adapter import (
    adapt_canonical_identity,
)


@pytest.mark.parametrize(
    ("item", "expected"),
    [
        (
            {"identity_score": 80},
            80.0,
        ),
        (
            {"_identity_score": 70},
            70.0,
        ),
        (
            {
                "_identity_validation": {
                    "identity_score": 60,
                },
            },
            60.0,
        ),
    ],
)
def test_existing_identity_evidence_is_adapted(
    item,
    expected,
):
    result = adapt_canonical_identity(item)
    assert result == expected


def test_canonical_identity_score_has_highest_precedence():
    result = adapt_canonical_identity(
        {
            "identity_score": 90,
            "_identity_score": 80,
            "_identity_validation": {
                "identity_score": 70,
            },
        }
    )

    assert result == 90.0


def test_legacy_identity_score_precedes_validation_fallback():
    result = adapt_canonical_identity(
        {
            "_identity_score": 80,
            "_identity_validation": {
                "identity_score": 70,
            },
        }
    )

    assert result == 80.0


def test_missing_identity_evidence_is_unavailable():
    assert adapt_canonical_identity({}) is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (-10, 0.0),
        (0, 0.0),
        (50, 50.0),
        (100, 100.0),
        (120, 100.0),
    ],
)
def test_identity_is_clamped_to_canonical_range(
    value,
    expected,
):
    result = adapt_canonical_identity(
        {
            "identity_score": value,
        }
    )

    assert result == expected


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "not-a-score",
        object(),
    ],
)
def test_invalid_primary_identity_can_fall_through_to_legacy_score(
    value,
):
    result = adapt_canonical_identity(
        {
            "identity_score": value,
            "_identity_score": 70,
        }
    )

    assert result == 70.0


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "not-a-score",
        object(),
    ],
)
def test_invalid_legacy_identity_can_fall_through_to_validation(
    value,
):
    result = adapt_canonical_identity(
        {
            "_identity_score": value,
            "_identity_validation": {
                "identity_score": 65,
            },
        }
    )

    assert result == 65.0


@pytest.mark.parametrize(
    "value",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_nonfinite_identity_is_unavailable_without_fallback(
    value,
):
    result = adapt_canonical_identity(
        {
            "identity_score": value,
        }
    )

    assert result is None


def test_zero_is_real_available_identity_evidence():
    result = adapt_canonical_identity(
        {
            "identity_score": 0,
            "_identity_score": 90,
            "_identity_validation": {
                "identity_score": 80,
            },
        }
    )

    assert result == 0.0


@pytest.mark.parametrize(
    "item",
    [
        {"identity_confidence": 95},
        {"identity_cluster_confidence": 95},
        {"product_family_confidence": 95},
        {"product_variant_confidence": 95},
        {"market_cluster_confidence": 95},
        {"product_identity": "abc"},
        {"product_identity_key": "abc"},
    ],
)
def test_noncanonical_identity_evidence_is_not_reinterpreted(
    item,
):
    result = adapt_canonical_identity(item)

    assert result is None


def test_identity_does_not_fall_back_to_trust():
    result = adapt_canonical_identity(
        {
            "trust_score": 95,
            "seller_trust_score": 90,
        }
    )

    assert result is None


def test_identity_does_not_fall_back_to_quality():
    result = adapt_canonical_identity(
        {
            "quality_score": 95,
            "food_intelligence_score": 90,
        }
    )

    assert result is None


def test_adapter_is_deterministic():
    item = {
        "identity_score": 72,
        "_identity_score": 65,
        "_identity_validation": {
            "identity_score": 55,
        },
    }

    first = adapt_canonical_identity(item)
    second = adapt_canonical_identity(item)

    assert first == second
