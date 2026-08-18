from app.services.recommendation.recommendation_score_v8 import (
    normalize_priority,
)


def test_priority_contract_preserves_supported_modes() -> None:
    assert normalize_priority("quality") == "quality"
    assert normalize_priority("taste") == "quality"

    assert normalize_priority("price") == "price"
    assert normalize_priority("value") == "price"

    assert normalize_priority("trust") == "trust"

    assert normalize_priority("mix") == "mix"
    assert normalize_priority("ranking") == "mix"

    assert normalize_priority("exploration") == "exploration"
    assert normalize_priority("discovery") == "discovery"


def test_priority_contract_strips_adaptive_suffix() -> None:
    assert normalize_priority("quality_adaptive") == "quality"
    assert normalize_priority("price_adaptive") == "price"
    assert normalize_priority("trust_adaptive") == "trust"
    assert normalize_priority("exploration_adaptive") == "exploration"


def test_priority_contract_unknown_falls_back_to_mix() -> None:
    assert normalize_priority(None) == "mix"
    assert normalize_priority("") == "mix"
    assert normalize_priority("unknown") == "mix"
    assert normalize_priority("balanced") == "mix"
