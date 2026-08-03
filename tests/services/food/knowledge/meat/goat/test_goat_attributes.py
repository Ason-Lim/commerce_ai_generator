from __future__ import annotations

from copy import deepcopy

import pytest

from app.services.food.knowledge.meat.goat import (
    GoatParser,
    build_goat_attributes,
)


def test_complete_goat_attributes() -> None:
    product = {
        "product_name": (
            "국내산 어린염소 보어 "
            "염소안심 500g"
        ),
        "goat_type": "어린 염소",
        "goat_breed": "Boer",
        "cut": "goat tenderloin",
        "country": "대한민국",
        "country_code": "KR",
        "weight": "500g",
        "storage_type": "냉장",
        "certifications": ["HACCP"],
        "bone_status": "boneless",
        "skin_status": "skinless",
    }

    parse_result = GoatParser().parse_product(
        product
    )

    attributes = build_goat_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["goat_type"] == "어린염소"
    assert attributes["breed"] == "보어"
    assert attributes["cut"] == "염소안심"

    assert (
        attributes[
            "goat_type_registry_key"
        ]
        == "kid"
    )
    assert (
        attributes[
            "breed_registry_key"
        ]
        == "boer"
    )
    assert (
        attributes[
            "cut_registry_key"
        ]
        == "tenderloin"
    )

    assert attributes["goat_type_score"] == 94.0
    assert attributes["breed_score"] == 94.0
    assert attributes["cut_score"] == 96.0

    assert attributes["country"] == "대한민국"
    assert attributes["country_code"] == "KR"
    assert attributes["weight"] == "500g"
    assert attributes["storage_type"] == "냉장"
    assert attributes["certifications"] == [
        "HACCP"
    ]
    assert attributes["bone_status"] == (
        "boneless"
    )
    assert attributes["skin_status"] == (
        "skinless"
    )

    assert attributes["is_complete"] is True
    assert attributes["is_usable"] is True


def test_cut_only_goat_attributes() -> None:
    product = {
        "product_name": "염소안심 500g",
        "country": "뉴질랜드",
    }

    parse_result = GoatParser().parse_product(
        product
    )

    attributes = build_goat_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["goat_type"] is None
    assert attributes["breed"] is None
    assert attributes["cut"] == "염소안심"
    assert attributes["cut_registry_key"] == (
        "tenderloin"
    )
    assert attributes["is_complete"] is False
    assert attributes["is_usable"] is True


def test_unknown_goat_attributes() -> None:
    product = {
        "product_name": "일반 식품 상품",
    }

    parse_result = GoatParser().parse_product(
        product
    )

    attributes = build_goat_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["goat_type"] is None
    assert attributes["breed"] is None
    assert attributes["cut"] is None
    assert attributes["is_complete"] is False
    assert attributes["is_usable"] is False


def test_attributes_do_not_mutate_inputs() -> None:
    product = {
        "product_name": "염소안심",
        "certifications": [
            "HACCP",
        ],
    }

    original = deepcopy(product)
    parse_result = GoatParser().parse_product(
        product
    )

    build_goat_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert product == original


def test_attributes_reject_invalid_product() -> None:
    parse_result = GoatParser().parse(
        "염소안심"
    )

    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        build_goat_attributes(
            product="염소안심",  # type: ignore[arg-type]
            parse_result=parse_result,
        )


def test_attributes_reject_invalid_parse_result() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "parse_result must be "
            "GoatParseResult"
        ),
    ):
        build_goat_attributes(
            product={
                "product_name": "염소안심"
            },
            parse_result=object(),  # type: ignore[arg-type]
        )
