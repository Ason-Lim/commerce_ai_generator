from app.services.food.knowledge.vegetable.parser import (
    VegetableParser,
    parse_vegetable,
)


def test_vegetable_parser_reads_structured_fields():
    parser = VegetableParser()

    result = parser.parse(
        {
            "product_name": "국산 유기농 상추 500g",
            "origin": "국산",
            "variety": "상추",
            "grade": "특",
            "weight": "500g",
        }
    )

    assert result.origin == "국산"
    assert result.variety == "상추"
    assert result.grade == "특"
    assert result.weight_grams == 500.0
    assert "유기농" in result.detected_keywords
    assert 0.0 <= result.confidence <= 1.0


def test_parse_vegetable_is_deterministic():
    product = {
        "product_name": "무농약 시금치 300g",
        "origin": "국산",
        "variety": "시금치",
    }

    first = parse_vegetable(product)
    second = parse_vegetable(product)

    assert first.to_dict() == second.to_dict()


def test_vegetable_parser_does_not_guess_missing_fields():
    result = parse_vegetable(
        {
            "product_name": "신선 채소",
        }
    )

    assert result.origin is None
    assert result.variety is None
    assert result.grade is None
