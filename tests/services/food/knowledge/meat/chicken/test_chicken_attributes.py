from __future__ import annotations

import pytest

from app.services.food.knowledge.meat.chicken.attributes import (
    build_chicken_attributes,
    extract_chicken_bone_status,
    extract_chicken_certifications,
    extract_chicken_country_code,
    extract_chicken_country_text,
    extract_chicken_product_name,
    extract_chicken_skin_status,
    extract_chicken_storage_type,
    extract_chicken_weight,
)
from app.services.food.knowledge.meat.chicken.parser import (
    ChickenParser,
)


def test_extract_chicken_product_fields() -> None:
    product = {
        "title": "국내산 토종닭 닭다리살",
        "origin_country": "대한민국",
        "origin_country_code": "kr",
        "net_weight": "500g",
        "storage": "냉장",
        "labels": ["무항생제", "HACCP"],
        "bone_status": "boneless",
        "skin_status": "skinless",
    }

    assert (
        extract_chicken_product_name(product)
        == "국내산 토종닭 닭다리살"
    )
    assert (
        extract_chicken_country_text(product)
        == "대한민국"
    )
    assert (
        extract_chicken_country_code(product)
        == "KR"
    )
    assert (
        extract_chicken_weight(product)
        == "500g"
    )
    assert (
        extract_chicken_storage_type(product)
        == "냉장"
    )
    assert extract_chicken_certifications(
        product
    ) == ["무항생제", "HACCP"]
    assert (
        extract_chicken_bone_status(product)
        == "boneless"
    )
    assert (
        extract_chicken_skin_status(product)
        == "skinless"
    )


def test_build_complete_chicken_attributes() -> None:
    product = {
        "product_name": (
            "국내산 토종닭 Ross 308 "
            "닭다리살 500g"
        ),
        "country": "대한민국",
        "country_code": "kr",
        "weight": "500g",
        "storage_type": "냉장",
        "certifications": [
            "무항생제",
            "HACCP",
        ],
        "bone_status": "boneless",
        "skin_status": "skinless",
    }

    parse_result = ChickenParser().parse_product(
        product
    )

    attributes = build_chicken_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["product_name"] == (
        "국내산 토종닭 Ross 308 "
        "닭다리살 500g"
    )
    assert attributes["country"] == "대한민국"
    assert attributes["country_code"] == "KR"
    assert attributes["weight"] == "500g"
    assert attributes["storage_type"] == "냉장"
    assert attributes["certifications"] == [
        "무항생제",
        "HACCP",
    ]
    assert attributes["bone_status"] == "boneless"
    assert attributes["skin_status"] == "skinless"

    assert attributes["chicken_type"] == "토종닭"
    assert attributes["breed"] == "로스 308"
    assert attributes["cut"] == "닭다리살"
    assert attributes["is_complete"] is True
    assert attributes["is_usable"] is True

    assert (
        attributes[
            "chicken_type_registry_key"
        ]
        == "native_chicken"
    )
    assert (
        attributes["chicken_type_category"]
        == "native_chicken"
    )
    assert (
        attributes["chicken_type_score"]
        == 88.0
    )
    assert (
        attributes[
            "chicken_type_typical_uses"
        ]
        == ["soup", "braising", "boiling"]
    )

    assert (
        attributes["breed_registry_key"]
        == "ross_308"
    )
    assert (
        attributes["breed_growth_score"]
        == 94.0
    )

    assert (
        attributes["cut_registry_key"]
        == "thigh"
    )
    assert (
        attributes["cut_group"]
        == "leg"
    )
    assert (
        attributes["cut_cooking_methods"]
        == [
            "grilling",
            "frying",
            "braising",
            "roasting",
        ]
    )


def test_build_cut_only_attributes() -> None:
    product = {
        "product_name": "국내산 닭가슴살 1kg",
    }

    parse_result = ChickenParser().parse_product(
        product
    )

    attributes = build_chicken_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["chicken_type"] is None
    assert attributes["breed"] is None
    assert attributes["cut"] == "닭가슴살"
    assert attributes["is_complete"] is False
    assert attributes["is_usable"] is True
    assert (
        attributes["cut_registry_key"]
        == "breast"
    )
    assert (
        "breed_registry_key"
        not in attributes
    )
    assert (
        "chicken_type_registry_key"
        not in attributes
    )


def test_attributes_do_not_infer_structured_values() -> None:
    product = {
        "product_name": (
            "국내산 냉동 무항생제 "
            "순살 닭가슴살 500g"
        ),
    }

    parse_result = ChickenParser().parse_product(
        product
    )

    attributes = build_chicken_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["country"] is None
    assert attributes["country_code"] is None
    assert attributes["weight"] is None
    assert attributes["storage_type"] is None
    assert attributes["certifications"] == []
    assert attributes["bone_status"] is None
    assert attributes["skin_status"] is None


def test_certifications_are_deduplicated() -> None:
    assert extract_chicken_certifications(
        {
            "certifications": [
                "HACCP",
                " haccp ",
                "무항생제",
                "",
            ]
        }
    ) == ["HACCP", "무항생제"]


def test_weight_preserves_zero_value() -> None:
    assert extract_chicken_weight(
        {"weight": 0}
    ) == 0


def test_build_attributes_rejects_non_mapping() -> None:
    parse_result = ChickenParser().parse(
        "닭가슴살"
    )

    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        build_chicken_attributes(
            product="닭가슴살",  # type: ignore[arg-type]
            parse_result=parse_result,
        )


def test_build_attributes_rejects_wrong_parse_result() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "parse_result must be "
            "ChickenParseResult"
        ),
    ):
        build_chicken_attributes(
            product={
                "product_name": "닭가슴살"
            },
            parse_result=object(),  # type: ignore[arg-type]
        )
