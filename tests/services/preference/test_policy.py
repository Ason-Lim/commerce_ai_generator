import pytest

from app.services.preference.models import (
    PreferenceProfile,
)
from app.services.preference.policy import (
    decide_adaptive_priority,
)


def test_none_uses_default_priority() -> None:
    assert (
        decide_adaptive_priority(None)
        == "trust"
    )


def test_custom_default_priority() -> None:
    assert (
        decide_adaptive_priority(
            None,
            default_priority="quality",
        )
        == "quality"
    )


def test_top_score_below_threshold() -> None:
    pref = {
        "price_affinity": 4,
        "quality_affinity": 0,
        "trust_affinity": 0,
        "exploration_affinity": 0,
    }

    assert (
        decide_adaptive_priority(pref)
        == "trust"
    )


def test_close_scores_are_balanced() -> None:
    pref = {
        "price_affinity": 8,
        "quality_affinity": 5,
        "trust_affinity": 1,
        "exploration_affinity": 0,
    }

    assert (
        decide_adaptive_priority(pref)
        == "balanced_adaptive"
    )


@pytest.mark.parametrize(
    ("field", "expected"),
    [
        (
            "price_affinity",
            "price_adaptive",
        ),
        (
            "quality_affinity",
            "quality_adaptive",
        ),
        (
            "trust_affinity",
            "trust_adaptive",
        ),
        (
            "exploration_affinity",
            "exploration_adaptive",
        ),
    ],
)
def test_dominant_affinity_selects_adaptive_mode(
    field: str,
    expected: str,
) -> None:
    pref = {
        "price_affinity": 0,
        "quality_affinity": 0,
        "trust_affinity": 0,
        "exploration_affinity": 0,
    }
    pref[field] = 10

    assert (
        decide_adaptive_priority(pref)
        == expected
    )


def test_profile_model_is_supported() -> None:
    profile = PreferenceProfile(
        session_id="session-1",
        quality_affinity=10,
        trust_affinity=2,
    )

    assert (
        decide_adaptive_priority(profile)
        == "quality_adaptive"
    )
