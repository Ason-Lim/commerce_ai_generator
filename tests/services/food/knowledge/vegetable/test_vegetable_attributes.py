from app.services.food.knowledge.vegetable.attributes import (
    build_vegetable_attributes,
)
from app.services.food.knowledge.vegetable.parser import (
    parse_vegetable,
)


def test_build_vegetable_attributes():
    product = {
        "product_name": "국산 상추 500g",
        "origin": "국산",
        "variety": "상추",
        "weight": "500g",
    }

    parsed = parse_vegetable(product)

    attributes = build_vegetable_attributes(
        product=product,
        parse_result=parsed,
    )

    assert attributes["product_name"] == "국산 상추 500g"
    assert attributes["origin"] == "국산"
    assert attributes["variety"] == "상추"
    assert attributes["weight_grams"] == 500.0
    assert "confidence" in attributes
