from __future__ import annotations

import pytest

from app.services.preference.policy import (
    decide_adaptive_priority as canonical_decide,
)
from app.services.preference_service import (
    decide_adaptive_priority as legacy_decide,
)


@pytest.mark.parametrize(
    (
        "preference",
        "default_priority",
    ),
    [
        (
            None,
            "trust",
        ),
        (
            {},
            "trust",
        ),
        (
            {
                "price_affinity": 4,
                "quality_affinity": 0,
                "trust_affinity": 0,
                "exploration_affinity": 0,
            },
            "trust",
        ),
        (
            {
                "price_affinity": 8,
                "quality_affinity": 5,
                "trust_affinity": 0,
                "exploration_affinity": 0,
            },
            "trust",
        ),
        (
            {
                "price_affinity": 10,
                "quality_affinity": 0,
                "trust_affinity": 0,
                "exploration_affinity": 0,
            },
            "trust",
        ),
        (
            {
                "price_affinity": 0,
                "quality_affinity": 10,
                "trust_affinity": 0,
                "exploration_affinity": 0,
            },
            "trust",
        ),
        (
            {
                "price_affinity": 0,
                "quality_affinity": 0,
                "trust_affinity": 10,
                "exploration_affinity": 0,
            },
            "quality",
        ),
        (
            {
                "price_affinity": 0,
                "quality_affinity": 0,
                "trust_affinity": 0,
                "exploration_affinity": 10,
            },
            "trust",
        ),
    ],
)
def test_adaptive_priority_matches_legacy(
    preference,
    default_priority: str,
) -> None:
    assert canonical_decide(
        preference,
        default_priority=default_priority,
    ) == legacy_decide(
        preference,
        default_priority=default_priority,
    )
