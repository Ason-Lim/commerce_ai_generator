from app.services.food.knowledge.vegetable.parser_models import (
    VegetableParseResult,
)


def test_vegetable_parse_result_serializes():
    result = VegetableParseResult(
        original_text="국산 유기농 상추 500g",
        normalized_text="국산 유기농 상추 500g",
        confidence=0.8,
        origin="국산",
        variety="상추",
        grade=None,
        weight_grams=500.0,
        detected_keywords=["유기농"],
    )

    payload = result.to_dict()

    assert payload["origin"] == "국산"
    assert payload["variety"] == "상추"
    assert payload["weight_grams"] == 500.0
    assert payload["confidence"] == 0.8
    assert payload["is_usable"] is True


def test_vegetable_parse_result_is_frozen():
    result = VegetableParseResult(
        original_text="상추",
        normalized_text="상추",
        confidence=0.5,
    )

    try:
        result.origin = "국산"
    except Exception:
        pass
    else:
        raise AssertionError(
            "VegetableParseResult must be frozen"
        )
