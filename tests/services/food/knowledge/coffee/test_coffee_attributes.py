from __future__ import annotations

from copy import deepcopy

import pytest

from app.services.food.knowledge.coffee import (
    CoffeeParser,
    build_coffee_attributes,
    extract_coffee_certifications,
    extract_coffee_decaf,
    extract_coffee_flavor_notes,
)


def _complete_product() -> dict[str, object]:
    return {
        "product_name": (
            "에티오피아 100% 아라비카 "
            "라이트 로스트 워시드 원두"
        ),
        "bean_type": "100% arabica",
        "origin_country": "Ethiopia",
        "country_code": "et",
        "roast_level": "light roast",
        "processing_method": "washed process",
        "weight": "200g",
        "grind_type": "whole bean",
        "product_form": "원두",
        "decaf": False,
        "certifications": [
            "Organic",
            "Fair Trade",
        ],
        "flavor_notes": [
            "자스민",
            "레몬",
            "베르가못",
        ],
        "altitude": "1,900m",
        "roast_date": "2026-08-01",
    }


def test_complete_coffee_attributes() -> None:
    product = _complete_product()

    parse_result = (
        CoffeeParser().parse_product(
            product
        )
    )

    attributes = build_coffee_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["product_name"] == (
        product["product_name"]
    )

    assert attributes["bean"] == "아라비카"
    assert attributes["origin"] == "에티오피아"
    assert attributes["country"] == "Ethiopia"
    assert attributes["country_code"] == "ET"
    assert attributes["roast"] == (
        "라이트 로스트"
    )
    assert attributes["process"] == "워시드"

    assert attributes["weight"] == "200g"
    assert attributes["grind_type"] == (
        "whole bean"
    )
    assert attributes["product_form"] == "원두"
    assert attributes["decaf"] is False
    assert attributes["certifications"] == [
        "Organic",
        "Fair Trade",
    ]
    assert attributes["flavor_notes"] == [
        "자스민",
        "레몬",
        "베르가못",
    ]
    assert attributes["altitude"] == "1,900m"
    assert attributes["roast_date"] == (
        "2026-08-01"
    )

    assert attributes["bean_registry_key"] == (
        "arabica"
    )
    assert attributes["origin_registry_key"] == (
        "ethiopia"
    )
    assert attributes["roast_registry_key"] == (
        "light"
    )
    assert attributes["process_registry_key"] == (
        "washed"
    )

    assert attributes["bean_score"] == 92.0
    assert attributes["origin_score"] == 96.0
    assert attributes["roast_score"] == 91.0
    assert attributes["process_score"] == 91.0

    assert attributes["matched_field_count"] == 4
    assert attributes["is_complete"] is True
    assert attributes["is_usable"] is True


def test_partial_coffee_attributes() -> None:
    product = {
        "product_name": (
            "에티오피아 워시드 커피 200g"
        ),
        "weight": "200g",
    }

    parse_result = (
        CoffeeParser().parse_product(
            product
        )
    )

    attributes = build_coffee_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["bean"] is None
    assert attributes["origin"] == "에티오피아"
    assert attributes["process"] == "워시드"
    assert attributes["roast"] is None

    assert attributes["origin_registry_key"] == (
        "ethiopia"
    )
    assert attributes["process_registry_key"] == (
        "washed"
    )

    assert "bean_registry_key" not in attributes
    assert "roast_registry_key" not in attributes

    assert attributes["matched_field_count"] == 2
    assert attributes["is_complete"] is False
    assert attributes["is_usable"] is True


def test_unknown_coffee_attributes() -> None:
    product = {
        "product_name": "일반 식품 상품",
    }

    parse_result = (
        CoffeeParser().parse_product(
            product
        )
    )

    attributes = build_coffee_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["bean"] is None
    assert attributes["origin"] is None
    assert attributes["roast"] is None
    assert attributes["process"] is None

    assert attributes["matched_field_count"] == 0
    assert attributes["is_complete"] is False
    assert attributes["is_usable"] is False
    assert attributes["confidence"] == 0.0
    assert attributes["parser_warnings"]


def test_country_falls_back_to_origin_registry() -> None:
    product = {
        "product_name": (
            "에티오피아 아라비카 원두"
        ),
    }

    parse_result = (
        CoffeeParser().parse_product(
            product
        )
    )

    attributes = build_coffee_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["origin"] == "에티오피아"
    assert attributes["country"] == "에티오피아"
    assert attributes["country_code"] == "ET"


def test_explicit_country_has_priority() -> None:
    product = {
        "product_name": (
            "에티오피아 아라비카 원두"
        ),
        "country": "Ethiopia",
        "country_code": "et",
    }

    parse_result = (
        CoffeeParser().parse_product(
            product
        )
    )

    attributes = build_coffee_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["origin"] == "에티오피아"
    assert attributes["country"] == "Ethiopia"
    assert attributes["country_code"] == "ET"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (True, True),
        (False, False),
        ("decaf", True),
        ("디카페인", True),
        ("regular", False),
        ("unknown", None),
        (None, None),
    ],
)
def test_extract_coffee_decaf(
    value: object,
    expected: bool | None,
) -> None:
    product = {}

    if value is not None:
        product["decaf"] = value

    assert extract_coffee_decaf(
        product
    ) is expected


def test_certifications_are_normalized() -> None:
    assert extract_coffee_certifications(
        {
            "certifications": [
                "Organic",
                "Organic",
                " Fair Trade ",
                "",
            ]
        }
    ) == [
        "Organic",
        "Fair Trade",
    ]

    assert extract_coffee_certifications(
        {
            "certification": "Rainforest Alliance",
        }
    ) == [
        "Rainforest Alliance",
    ]

    assert extract_coffee_certifications({}) == []


def test_flavor_notes_are_normalized() -> None:
    assert extract_coffee_flavor_notes(
        {
            "flavor_notes": (
                "자스민, 레몬 / 베르가못"
            )
        }
    ) == [
        "자스민",
        "레몬",
        "베르가못",
    ]

    assert extract_coffee_flavor_notes(
        {
            "tasting_notes": [
                "초콜릿",
                "초콜릿",
                " 견과류 ",
                "",
            ]
        }
    ) == [
        "초콜릿",
        "견과류",
    ]

    assert extract_coffee_flavor_notes({}) == []


def test_attributes_do_not_mutate_inputs() -> None:
    product = _complete_product()
    product_before = deepcopy(product)

    parse_result = (
        CoffeeParser().parse_product(
            product
        )
    )
    parse_result_before = (
        parse_result.to_dict()
    )

    build_coffee_attributes(
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
        CoffeeParser().parse_product(
            product
        )
    )

    attributes = build_coffee_attributes(
        product=product,
        parse_result=parse_result,
    )

    attributes["certifications"].append(
        "테스트"
    )
    attributes["flavor_notes"].append(
        "테스트"
    )
    attributes["detected_keywords"].append(
        "테스트"
    )

    assert "테스트" not in product[
        "certifications"
    ]
    assert "테스트" not in product[
        "flavor_notes"
    ]
    assert (
        "테스트"
        not in parse_result.detected_keywords
    )


def test_attributes_reject_invalid_product() -> None:
    parse_result = CoffeeParser().parse(
        "아라비카 원두"
    )

    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        build_coffee_attributes(
            product="아라비카",  # type: ignore[arg-type]
            parse_result=parse_result,
        )


def test_attributes_reject_invalid_parse_result() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "parse_result must be "
            "CoffeeParseResult"
        ),
    ):
        build_coffee_attributes(
            product={
                "product_name": (
                    "아라비카 원두"
                ),
            },
            parse_result=object(),  # type: ignore[arg-type]
        )


def test_attributes_do_not_calculate_scores() -> None:
    product = _complete_product()

    parse_result = (
        CoffeeParser().parse_product(
            product
        )
    )

    attributes = build_coffee_attributes(
        product=product,
        parse_result=parse_result,
    )

    registry_score_keys = {
        "bean_score",
        "origin_score",
        "roast_score",
        "process_score",
    }

    assert registry_score_keys.issubset(
        attributes.keys()
    )

    assert "knowledge_score" not in attributes
    assert "final_score" not in attributes
    assert "quality_score" not in attributes
    assert "price_score" not in attributes
    assert "trust_score" not in attributes
