from __future__ import annotations

import pytest

from app.services.food.knowledge.seafood.attributes import (
    build_seafood_attributes,
)
from app.services.food.knowledge.seafood.parser import (
    parse_seafood,
)


def test_build_seafood_attributes():
    product = {
        "product_name": "냉동 새우 800g",
        "origin": "베트남",
        "weight": "800g",
    }

    parsed = parse_seafood(product)

    attributes = build_seafood_attributes(
        product=product,
        parse_result=parsed,
    )

    assert attributes["species"] == "shrimp"
    assert attributes["seafood_group"] == "crustacean"
    assert attributes["origin"] == "베트남"
    assert attributes["processing_state"] == "frozen"
    assert attributes["weight"] == "800g"
    assert attributes["weight_grams"] == 800.0


def test_build_seafood_attributes_contains_parser_metadata():
    product = {
        "product_name": "생물 전복 1kg",
    }

    parsed = parse_seafood(product)

    attributes = build_seafood_attributes(
        product=product,
        parse_result=parsed,
    )

    assert "confidence" in attributes
    assert "matched_field_count" in attributes
    assert "is_complete" in attributes
    assert "is_usable" in attributes


def test_build_seafood_attributes_rejects_invalid_product():
    parsed = parse_seafood(
        {"product_name": "연어"}
    )

    with pytest.raises(TypeError):
        build_seafood_attributes(
            product="연어",
            parse_result=parsed,
        )
