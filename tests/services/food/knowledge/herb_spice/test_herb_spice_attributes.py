from __future__ import annotations

from copy import deepcopy

import pytest

from app.services.food.knowledge.herb_spice.attributes import (
    build_herb_spice_attributes,
    extract_herb_spice_additives,
    extract_herb_spice_certifications,
    extract_herb_spice_flavor_notes,
    extract_herb_spice_organic_status,
    extract_herb_spice_salt_added,
)
from app.services.food.knowledge.herb_spice.parser import (
    HerbSpiceParser,
)


def _complete_herb_product() -> dict[str, object]:
    return {
        "product_name": (
            "프랑스산 건조 로즈마리 오븐 구이용"
        ),
        "classification": "herb",
        "ingredient": "rosemary",
        "origin": "France",
        "country": "France",
        "country_code": "fr",
        "product_form": "dried herb",
        "recommended_usage": "roasting",
        "weight": "50g",
        "packaging_type": "zip pouch",
        "certifications": [
            "Organic",
            "HACCP",
        ],
        "flavor_notes": [
            "솔향",
            "우디",
        ],
        "additives": [],
        "organic": True,
        "salt_added": False,
    }


def test_complete_herb_attributes() -> None:
    product = _complete_herb_product()

    parse_result = HerbSpiceParser().parse_product(
        product
    )

    attributes = build_herb_spice_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["product_name"] == (
        product["product_name"]
    )
    assert attributes["classification"] == "herb"
    assert attributes["ingredient"] == "rosemary"
    assert attributes["origin"] == "france"
    assert attributes["form"] == "dried"
    assert attributes["usage"] == "roasting"

    assert attributes["country"] == "France"
    assert attributes["country_code"] == "FR"
    assert attributes["weight"] == "50g"
    assert (
        attributes["packaging_type"]
        == "zip pouch"
    )
    assert attributes["certifications"] == [
        "Organic",
        "HACCP",
    ]
    assert attributes["flavor_notes"] == [
        "솔향",
        "우디",
    ]
    assert attributes["additives"] == []
    assert attributes["organic"] is True
    assert attributes["salt_added"] is False

    assert attributes["matched_field_count"] == 4
    assert attributes["is_complete"] is True
    assert attributes["is_usable"] is True
    assert (
        attributes["has_ingredient_conflict"]
        is False
    )


def test_complete_herb_registry_metadata() -> None:
    product = _complete_herb_product()

    parse_result = HerbSpiceParser().parse_product(
        product
    )

    attributes = build_herb_spice_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert (
        attributes["ingredient_registry_key"]
        == "rosemary"
    )
    assert (
        attributes["ingredient_botanical_name"]
        == "Salvia rosmarinus"
    )
    assert (
        attributes["ingredient_plant_part"]
        == "leaf"
    )
    assert (
        attributes["ingredient_flavor_profile"]
        == "piney aromatic"
    )
    assert (
        attributes["herb_fresh_available"]
        is True
    )
    assert (
        attributes["herb_dried_available"]
        is True
    )

    assert (
        attributes["origin_registry_key"]
        == "france"
    )
    assert (
        attributes["origin_country_code"]
        == "FR"
    )

    assert (
        attributes["form_registry_key"]
        == "dried"
    )
    assert attributes["form_dried"] is True
    assert attributes["form_ground"] is False

    assert (
        attributes["usage_registry_key"]
        == "roasting"
    )
    assert attributes["usage_dry_heat"] is True
    assert (
        attributes["usage_wet_cooking"]
        is False
    )


def test_complete_spice_registry_metadata() -> None:
    product = {
        "product_name": (
            "인도산 큐민 파우더 스튜용"
        ),
        "classification": "spice",
        "ingredient": "cumin",
        "origin": "India",
        "product_form": "powder",
        "recommended_usage": "stew",
    }

    parse_result = HerbSpiceParser().parse_product(
        product
    )

    attributes = build_herb_spice_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["classification"] == "spice"
    assert attributes["ingredient"] == "cumin"
    assert (
        attributes["ingredient_registry_key"]
        == "cumin"
    )
    assert attributes["spice_heat_level"] == 1.0
    assert attributes["spice_pungent"] is False

    assert "herb_fresh_available" not in attributes
    assert "herb_dried_available" not in attributes


def test_partial_attributes() -> None:
    product = {
        "product_name": "프랑스산 건조 상품",
        "weight": "30g",
    }

    parse_result = HerbSpiceParser().parse_product(
        product
    )

    attributes = build_herb_spice_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["classification"] is None
    assert attributes["ingredient"] is None
    assert attributes["origin"] == "france"
    assert attributes["form"] == "dried"
    assert attributes["usage"] is None
    assert attributes["weight"] == "30g"

    assert attributes["matched_field_count"] == 2
    assert attributes["is_complete"] is False
    assert attributes["is_usable"] is True

    assert (
        attributes["origin_registry_key"]
        == "france"
    )
    assert (
        attributes["form_registry_key"]
        == "dried"
    )
    assert "ingredient_registry_key" not in attributes


def test_unknown_attributes() -> None:
    product = {
        "product_name": "일반 식품 상품",
    }

    parse_result = HerbSpiceParser().parse_product(
        product
    )

    attributes = build_herb_spice_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["classification"] is None
    assert attributes["ingredient"] is None
    assert attributes["origin"] is None
    assert attributes["form"] is None
    assert attributes["usage"] is None

    assert attributes["matched_field_count"] == 0
    assert attributes["is_complete"] is False
    assert attributes["is_usable"] is False
    assert attributes["confidence"] == 0.0
    assert attributes["parser_warnings"]


def test_country_falls_back_to_origin_registry() -> None:
    product = {
        "product_name": "인도산 큐민",
    }

    parse_result = HerbSpiceParser().parse_product(
        product
    )

    attributes = build_herb_spice_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["origin"] == "india"
    assert attributes["country"] == "India"
    assert attributes["country_code"] == "IN"


def test_explicit_country_has_priority() -> None:
    product = {
        "product_name": "인도산 큐민",
        "country": "Republic of India",
        "country_code": "in",
    }

    parse_result = HerbSpiceParser().parse_product(
        product
    )

    attributes = build_herb_spice_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["country"] == (
        "Republic of India"
    )
    assert attributes["country_code"] == "IN"


def test_certifications_are_normalized() -> None:
    assert extract_herb_spice_certifications(
        {
            "certifications": [
                "Organic",
                "organic",
                " HACCP ",
                "",
            ]
        }
    ) == [
        "Organic",
        "HACCP",
    ]

    assert extract_herb_spice_certifications(
        {
            "certification": "USDA Organic",
        }
    ) == [
        "USDA Organic",
    ]

    assert extract_herb_spice_certifications(
        {}
    ) == []


def test_flavor_notes_are_normalized() -> None:
    assert extract_herb_spice_flavor_notes(
        {
            "flavor_notes": (
                "솔향, 우디 / 허브향"
            )
        }
    ) == [
        "솔향",
        "우디",
        "허브향",
    ]

    assert extract_herb_spice_flavor_notes(
        {}
    ) == []


def test_additives_are_normalized() -> None:
    assert extract_herb_spice_additives(
        {
            "additives": (
                "소금, 설탕 / 향료"
            )
        }
    ) == [
        "소금",
        "설탕",
        "향료",
    ]

    assert extract_herb_spice_additives(
        {}
    ) == []


@pytest.mark.parametrize(
    (
        "value",
        "expected",
    ),
    [
        (True, True),
        (False, False),
        ("organic", True),
        ("non-organic", False),
        ("unknown", None),
        (None, None),
    ],
)
def test_extract_organic_status(
    value: object,
    expected: bool | None,
) -> None:
    product: dict[str, object] = {}

    if value is not None:
        product["organic"] = value

    assert (
        extract_herb_spice_organic_status(
            product
        )
        is expected
    )


@pytest.mark.parametrize(
    (
        "value",
        "expected",
    ),
    [
        (True, True),
        (False, False),
        ("salted", True),
        ("unsalted", False),
        ("unknown", None),
        (None, None),
    ],
)
def test_extract_salt_added(
    value: object,
    expected: bool | None,
) -> None:
    product: dict[str, object] = {}

    if value is not None:
        product["salt_added"] = value

    assert (
        extract_herb_spice_salt_added(
            product
        )
        is expected
    )


def test_attributes_preserve_conflict_evidence() -> None:
    product = {
        "product_name": (
            "생고수 고수씨 혼합 향신료"
        ),
    }

    parse_result = HerbSpiceParser().parse_product(
        product
    )

    attributes = build_herb_spice_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert (
        parse_result.has_ingredient_conflict
        is True
    )
    assert (
        attributes["has_ingredient_conflict"]
        is True
    )
    assert attributes["classification"] in {
        "herb",
        "spice",
    }


def test_attributes_do_not_mutate_inputs() -> None:
    product = _complete_herb_product()
    product_before = deepcopy(product)

    parse_result = HerbSpiceParser().parse_product(
        product
    )
    parse_result_before = (
        parse_result.to_dict()
    )

    build_herb_spice_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert product == product_before
    assert (
        parse_result.to_dict()
        == parse_result_before
    )


def test_attribute_collections_are_copies() -> None:
    product = _complete_herb_product()

    parse_result = HerbSpiceParser().parse_product(
        product
    )

    attributes = build_herb_spice_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert (
        attributes["detected_keywords"]
        is not parse_result.detected_keywords
    )
    assert (
        attributes["parser_warnings"]
        is not parse_result.warnings
    )


def test_build_attributes_rejects_invalid_product() -> None:
    parse_result = HerbSpiceParser().parse(
        "로즈마리"
    )

    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        build_herb_spice_attributes(
            product="로즈마리",  # type: ignore[arg-type]
            parse_result=parse_result,
        )


def test_build_attributes_rejects_wrong_result() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "parse_result must be "
            "HerbSpiceParseResult"
        ),
    ):
        build_herb_spice_attributes(
            product={
                "product_name": "로즈마리",
            },
            parse_result=object(),  # type: ignore[arg-type]
        )
