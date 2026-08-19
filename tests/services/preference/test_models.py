from app.services.preference.models import (
    PreferenceProfile,
)


def test_preference_profile_from_mapping() -> None:
    profile = PreferenceProfile.from_mapping(
        {
            "session_id": "session-1",
            "price_affinity": 7,
            "quality_affinity": 3,
            "trust_affinity": None,
            "exploration_affinity": 2,
            "search_count": 4,
            "click_count": 5,
            "last_query": "apple",
            "last_priority": "price",
        }
    )

    assert profile.session_id == "session-1"
    assert profile.price_affinity == 7.0
    assert profile.quality_affinity == 3.0
    assert profile.trust_affinity == 0.0
    assert profile.exploration_affinity == 2.0
    assert profile.search_count == 4
    assert profile.click_count == 5
    assert profile.last_query == "apple"
    assert profile.last_priority == "price"


def test_affinity_scores() -> None:
    profile = PreferenceProfile(
        session_id="session-1",
        price_affinity=8,
        quality_affinity=3,
        trust_affinity=2,
        exploration_affinity=1,
    )

    assert profile.affinity_scores() == {
        "price": 8,
        "quality": 3,
        "trust": 2,
        "exploration": 1,
    }
