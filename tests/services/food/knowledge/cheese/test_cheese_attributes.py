from __future__ import annotations

from copy import deepcopy

import pytest

from app.services.food.knowledge.cheese import (
    CheeseParser,
    build_cheese_attributes,
    extract_cheese_certifications,
    extract_cheese_pasteurization,
)


def _complete_product() -> dict[str, object]:
    return {
        "product_name": (
            "프랑스 산양유 브리 "
            "소프트 치즈 12개월 숙성"
        ),
        "cheese_type": "brie",
        "milk_source": "goat milk",
        "country": "프랑스",
        "country_code": "FR",
        "texture": "soft cheese",
        "aging": "12개월 숙성",
        "weight": "200g",
        "storage_type": "냉장",
        "packaging_type": "wheel",
        "pasteurized": True,
        "certifications": [
            "AOP",
            "유기농",
        ],
        "fat_content": "45%",
        "rind_type": "bloomy rind",
    }


def test_complete_cheese_attributes() -> None:
    product = _complete_product()

    parse_result = (
        CheeseParser().parse_product(
            product
        )
    )

    attributes = build_cheese_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["product_name"] == (
        product["product_name"]
    )

    assert attributes["cheese_type"] == "브리"
    assert attributes["milk_source"] == "산양유"
    assert attributes["origin"] == "프랑스"
    assert attributes["country"] == "프랑스"
    assert attributes["country_code"] == "FR"
    assert attributes["texture"] == "연성"
    assert attributes["aging"] == "장기숙성"

    assert attributes["weight"] == "200g"
    assert attributes["storage_type"] == "냉장"
    assert attributes["packaging_type"] == "wheel"
    assert attributes["pasteurization"] == (
        "pasteurized"
    )
    assert attributes["certifications"] == [
        "AOP",
        "유기농",
    ]
    assert attributes["fat_content"] == "45%"
    assert attributes["rind_type"] == (
        "bloomy rind"
    )

    assert (
        attributes[
            "cheese_type_registry_key"
        ]
        == "brie"
    )
    assert (
        attributes[
            "milk_source_registry_key"
        ]
        == "goat"
    )
    assert (
        attributes["origin_registry_key"]
        == "france"
    )
    assert (
        attributes["texture_registry_key"]
        == "soft"
    )
    assert (
        attributes["aging_registry_key"]
        == "long_aged"
    )

    assert attributes["cheese_type_score"] == 92.0
    assert attributes["milk_source_score"] == 91.0
    assert attributes["origin_score"] == 96.0
    assert attributes["texture_score"] == 89.0
    assert attributes["aging_score"] == 94.0

    assert attributes["is_complete"] is True
    assert attributes["is_usable"] is True
    assert attributes["matched_field_count"] == 5


def test_partial_cheese_attributes() -> None:
    product = {
        "product_name": (
            "24개월 숙성 "
            "파르미자노 레지아노"
        ),
        "weight": "150g",
    }

    parse_result = (
        CheeseParser().parse_product(
            product
        )
    )

    attributes = build_cheese_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["cheese_type"] == (
        "파르미자노 레지아노"
    )
    assert attributes["aging"] == (
        "초장기숙성"
    )

    assert attributes["milk_source"] is None
    assert attributes["origin"] is None
    assert attributes["texture"] is None

    assert (
        attributes[
            "cheese_type_registry_key"
        ]
        == "parmesan"
    )
    assert (
        attributes["aging_registry_key"]
        == "extra_aged"
    )

    assert "milk_source_registry_key" not in (
        attributes
    )
    assert "origin_registry_key" not in attributes
    assert "texture_registry_key" not in (
        attributes
    )

    assert attributes["weight"] == "150g"
    assert attributes["is_complete"] is False
    assert attributes["is_usable"] is True


def test_unknown_cheese_attributes() -> None:
    product = {
        "product_name": "일반 식품 상품",
    }

    parse_result = (
        CheeseParser().parse_product(
            product
        )
    )

    attributes = build_cheese_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["cheese_type"] is None
    assert attributes["milk_source"] is None
    assert attributes["origin"] is None
    assert attributes["texture"] is None
    assert attributes["aging"] is None

    assert attributes["matched_field_count"] == 0
    assert attributes["is_complete"] is False
    assert attributes["is_usable"] is False
    assert attributes["confidence"] == 0.0
    assert attributes["parser_warnings"]


def test_country_falls_back_to_origin_registry() -> None:
    product = {
        "product_name": (
            "이탈리아 파르미자노 "
            "레지아노"
        ),
    }

    parse_result = (
        CheeseParser().parse_product(
            product
        )
    )

    attributes = build_cheese_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["origin"] == "이탈리아"
    assert attributes["country"] == "이탈리아"
    assert attributes["country_code"] == "IT"


def test_explicit_country_has_priority() -> None:
    product = {
        "product_name": "프랑스 브리 치즈",
        "country": "France",
        "country_code": "fr",
    }

    parse_result = (
        CheeseParser().parse_product(
            product
        )
    )

    attributes = build_cheese_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["origin"] == "프랑스"
    assert attributes["country"] == "France"
    assert attributes["country_code"] == "FR"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (True, "pasteurized"),
        (False, "unpasteurized"),
        ("raw milk", "raw milk"),
        (None, None),
    ],
)
def test_extract_cheese_pasteurization(
    value: object,
    expected: str | None,
) -> None:
    product = {}

    if value is not None:
        product["pasteurized"] = value

    assert (
        extract_cheese_pasteurization(
            product
        )
        == expected
    )


def test_certifications_are_normalized() -> None:
    assert extract_cheese_certifications(
        {
            "certifications": [
                "AOP",
                "AOP",
                " 유기농 ",
                "",
            ]
        }
    ) == [
        "AOP",
        "유기농",
    ]

    assert extract_cheese_certifications(
        {
            "certification": "PDO",
        }
    ) == [
        "PDO",
    ]

    assert extract_cheese_certifications({}) == []


def test_attributes_do_not_mutate_inputs() -> None:
    product = _complete_product()
    product_before = deepcopy(product)

    parse_result = (
        CheeseParser().parse_product(
            product
        )
    )
    parse_result_before = (
        parse_result.to_dict()
    )

    build_cheese_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert product == product_before
    assert (
        parse_result.to_dict()
        == parse_result_before
    )


def test_attribute_lists_are_copies() -> None:
    product = _complete_product()

    parse_result = (
        CheeseParser().parse_product(
            product
        )
    )

    attributes = build_cheese_attributes(
        product=product,
        parse_result=parse_result,
    )

    attributes["certifications"].append(
        "테스트"
    )
    attributes["detected_keywords"].append(
        "테스트"
    )
    attributes[
        "cheese_type_typical_uses"
    ].append(
        "테스트"
    )

    assert "테스트" not in product[
        "certifications"
    ]
    assert (
        "테스트"
        not in parse_result.detected_keywords
    )
    assert (
        "테스트"
        not in (
            parse_result
            .cheese_type_match
            .entry
            .typical_uses
        )
    )


def test_attributes_reject_invalid_product() -> None:
    parse_result = CheeseParser().parse(
        "브리 치즈"
    )

    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        build_cheese_attributes(
            product="브리 치즈",  # type: ignore[arg-type]
            parse_result=parse_result,
        )


def test_attributes_reject_invalid_parse_result() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "parse_result must be "
            "CheeseParseResult"
        ),
    ):
        build_cheese_attributes(
            product={
                "product_name": "브리 치즈",
            },
            parse_result=object(),  # type: ignore[arg-type]
        )


def test_attributes_contain_no_scores_calculated_locally() -> None:
    product = _complete_product()

    parse_result = (
        CheeseParser().parse_product(
            product
        )
    )

    attributes = build_cheese_attributes(
        product=product,
        parse_result=parse_result,
    )

    registry_score_keys = {
        "cheese_type_score",
        "milk_source_score",
        "origin_score",
        "texture_score",
        "aging_score",
    }

    assert registry_score_keys.issubset(
        attributes.keys()
    )

    assert "knowledge_score" not in attributes
    assert "final_score" not in attributes
    assert "quality_score" not in attributes
    assert "price_score" not in attributes
    assert "trust_score" not in attributes
