from __future__ import annotations

import pytest

from app.services.food.knowledge.meat.duck.attributes import (
    build_duck_attributes,
    extract_duck_bone_status,
    extract_duck_certifications,
    extract_duck_country_code,
    extract_duck_country_text,
    extract_duck_product_name,
    extract_duck_skin_status,
    extract_duck_storage_type,
    extract_duck_weight,
)
from app.services.food.knowledge.meat.duck.parser import (
    DuckParser,
)


def test_extract_duck_product_fields() -> None:
    product = {
        "title": "국내산 훈제오리 오리가슴살",
        "origin_country": "대한민국",
        "origin_country_code": "kr",
        "net_weight": "500g",
        "storage": "냉장",
        "labels": ["무항생제", "HACCP"],
        "bone_status": "boneless",
        "skin_status": "skin_on",
    }

    assert (
        extract_duck_product_name(product)
        == "국내산 훈제오리 오리가슴살"
    )
    assert (
        extract_duck_country_text(product)
        == "대한민국"
    )
    assert (
        extract_duck_country_code(product)
        == "KR"
    )
    assert extract_duck_weight(product) == "500g"
    assert (
        extract_duck_storage_type(product)
        == "냉장"
    )
    assert extract_duck_certifications(
        product
    ) == ["무항생제", "HACCP"]
    assert (
        extract_duck_bone_status(product)
        == "boneless"
    )
    assert (
        extract_duck_skin_status(product)
        == "skin_on"
    )


def test_build_complete_duck_attributes() -> None:
    product = {
        "product_name": (
            "국내산 훈제오리 체리밸리 "
            "오리가슴살 500g"
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
        "skin_status": "skin_on",
    }

    parse_result = DuckParser().parse_product(
        product
    )

    attributes = build_duck_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["product_name"] == (
        "국내산 훈제오리 체리밸리 "
        "오리가슴살 500g"
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
    assert attributes["skin_status"] == "skin_on"

    assert attributes["duck_type"] == "훈제오리"
    assert attributes["breed"] == "체리밸리"
    assert attributes["cut"] == "오리가슴살"
    assert attributes["is_complete"] is True
    assert attributes["is_usable"] is True
    assert attributes["confidence"] > 0.0

    assert parse_result.duck_type_match is not None
    assert parse_result.breed_match is not None
    assert parse_result.cut_match is not None

    duck_type = (
        parse_result.duck_type_match.duck_type
    )
    breed = parse_result.breed_match.breed
    cut = parse_result.cut_match.cut

    assert (
        attributes["duck_type_registry_key"]
        == duck_type.registry_key
    )
    assert (
        attributes["breed_registry_key"]
        == breed.registry_key
    )
    assert (
        attributes["cut_registry_key"]
        == cut.registry_key
    )

    assert (
        attributes["duck_type_score"]
        == duck_type.score
    )
    assert (
        attributes["breed_growth_score"]
        == breed.growth_score
    )
    assert (
        attributes["cut_score"]
        == cut.score
    )

    assert attributes[
        "duck_type_typical_uses"
    ] == list(duck_type.typical_uses)

    assert attributes[
        "cut_cooking_methods"
    ] == list(cut.cooking_methods)


def test_build_cut_only_attributes() -> None:
    product = {
        "product_name": "국내산 오리가슴살 1kg",
    }

    parse_result = DuckParser().parse_product(
        product
    )

    attributes = build_duck_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["duck_type"] is None
    assert attributes["breed"] is None
    assert attributes["cut"] == "오리가슴살"
    assert attributes["is_complete"] is False
    assert attributes["is_usable"] is True

    assert parse_result.cut_match is not None

    assert (
        attributes["cut_registry_key"]
        == parse_result.cut_match.cut.registry_key
    )
    assert (
        "breed_registry_key"
        not in attributes
    )
    assert (
        "duck_type_registry_key"
        not in attributes
    )


def test_attributes_do_not_infer_structured_values() -> None:
    product = {
        "product_name": (
            "국내산 냉동 무항생제 "
            "순살 오리가슴살 500g"
        ),
    }

    parse_result = DuckParser().parse_product(
        product
    )

    attributes = build_duck_attributes(
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
    assert extract_duck_certifications(
        {
            "certifications": [
                "HACCP",
                " haccp ",
                "무항생제",
                "",
            ]
        }
    ) == ["HACCP", "무항생제"]


def test_certification_string_is_preserved() -> None:
    assert extract_duck_certifications(
        {
            "certification": "HACCP",
        }
    ) == ["HACCP"]


def test_weight_preserves_zero_value() -> None:
    assert extract_duck_weight(
        {"weight": 0}
    ) == 0


def test_build_attributes_copies_mutable_lists() -> None:
    product = {
        "product_name": (
            "훈제오리 체리밸리 오리가슴살"
        )
    }

    parse_result = DuckParser().parse_product(
        product
    )

    attributes = build_duck_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert (
        attributes["detected_keywords"]
        is not parse_result.detected_keywords
    )
    assert (
        attributes["warnings"]
        is not parse_result.warnings
    )

    original_keywords = list(
        parse_result.detected_keywords
    )
    original_warnings = list(
        parse_result.warnings
    )

    attributes["detected_keywords"].append(
        "mutated"
    )
    attributes["warnings"].append(
        "mutated"
    )

    assert (
        parse_result.detected_keywords
        == original_keywords
    )
    assert (
        parse_result.warnings
        == original_warnings
    )


def test_build_attributes_rejects_non_mapping() -> None:
    parse_result = DuckParser().parse(
        "오리가슴살"
    )

    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        build_duck_attributes(
            product="오리가슴살",  # type: ignore[arg-type]
            parse_result=parse_result,
        )


def test_build_attributes_rejects_wrong_parse_result() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "parse_result must be "
            "DuckParseResult"
        ),
    ):
        build_duck_attributes(
            product={
                "product_name": "오리가슴살"
            },
            parse_result=object(),  # type: ignore[arg-type]
        )
