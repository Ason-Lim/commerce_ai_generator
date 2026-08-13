from __future__ import annotations

import pytest

from app.services.food.knowledge.seafood.parser import (
    detect_species,
    normalize_species,
    parse_seafood,
)


@pytest.mark.parametrize(
    ("product_name", "species", "group"),
    [
        ("노르웨이 생연어 500g", "salmon", "fish"),
        ("참치 횟감 300g", "tuna", "fish"),
        ("냉동 고등어 1kg", "mackerel", "fish"),
        ("자연산 대게 1kg", "crab", "crustacean"),
        ("냉동 새우 800g", "shrimp", "crustacean"),
        ("생물 전복 1kg", "abalone", "mollusk"),
        ("손질 오징어 500g", "squid", "cephalopod"),
        ("문어 1kg", "octopus", "cephalopod"),
    ],
)
def test_seafood_parser_detects_species_and_group(
    product_name,
    species,
    group,
):
    parsed = parse_seafood(
        {"product_name": product_name}
    )

    assert parsed.species == species
    assert parsed.seafood_group == group


def test_seafood_parser_prefers_structured_species():
    parsed = parse_seafood(
        {
            "product_name": "프리미엄 수산물",
            "species": "salmon",
        }
    )

    assert parsed.species == "salmon"
    assert parsed.seafood_group == "fish"


def test_seafood_parser_normalizes_structured_alias():
    parsed = parse_seafood(
        {
            "product_name": "프리미엄 수산물",
            "species": "연어",
        }
    )

    assert parsed.species == "salmon"


def test_seafood_parser_extracts_weight_from_name():
    parsed = parse_seafood(
        {"product_name": "냉동 새우 800g"}
    )

    assert parsed.weight_grams == 800.0


def test_seafood_parser_detects_frozen_state():
    parsed = parse_seafood(
        {"product_name": "냉동 새우 800g"}
    )

    assert parsed.processing_state == "frozen"


def test_seafood_parser_detects_wild_status():
    parsed = parse_seafood(
        {"product_name": "자연산 대게 1kg"}
    )

    assert parsed.wild_farmed_status == "wild"


def test_seafood_parser_does_not_guess_origin():
    parsed = parse_seafood(
        {"product_name": "노르웨이산 생연어 500g"}
    )

    assert parsed.origin is None


def test_seafood_parser_uses_explicit_origin():
    parsed = parse_seafood(
        {
            "product_name": "노르웨이산 생연어 500g",
            "origin": "노르웨이",
        }
    )

    assert parsed.origin == "노르웨이"


def test_seafood_parser_unknown_product_does_not_guess_species():
    parsed = parse_seafood(
        {"product_name": "프리미엄 식품 500g"}
    )

    assert parsed.species is None
    assert parsed.seafood_group is None


def test_detect_species_prefers_longer_alias():
    assert detect_species("킹크랩 1kg") == "crab"


def test_normalize_species_keeps_unknown_explicit_value():
    assert normalize_species("unknown fish") == "unknown fish"


def test_seafood_parser_rejects_non_mapping():
    with pytest.raises(TypeError):
        parse_seafood("연어")
