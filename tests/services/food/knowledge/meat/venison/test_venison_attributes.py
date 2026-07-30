from __future__ import annotations

import pytest

from app.services.food.knowledge.meat.venison import (
    VenisonParser,
    build_venison_attributes,
    extract_venison_bone_status,
    extract_venison_certifications,
    extract_venison_country_code,
    extract_venison_country_text,
    extract_venison_product_name,
    extract_venison_skin_status,
    extract_venison_storage_type,
    extract_venison_weight,
)
from app.services.food.knowledge.meat.venison.parser_models import (
    VenisonParseResult,
)


def test_extract_venison_product_fields() -> None:
    product = {
        "product_name": (
            "뉴질랜드 어린사슴 "
            "레드디어 사슴안심"
        ),
        "country": "뉴질랜드",
        "country_code": "nz",
        "weight": "500g",
        "storage_type": "냉동",
        "certifications": [
            "HACCP",
            "무항생제",
        ],
        "bone_status": "무뼈",
        "skin_status": "껍질 제거",
    }

    assert extract_venison_product_name(
        product
    ) == (
        "뉴질랜드 어린사슴 "
        "레드디어 사슴안심"
    )
    assert extract_venison_country_text(
        product
    ) == "뉴질랜드"
    assert extract_venison_country_code(
        product
    ) == "NZ"
    assert extract_venison_weight(
        product
    ) == "500g"
    assert extract_venison_storage_type(
        product
    ) == "냉동"
    assert extract_venison_certifications(
        product
    ) == [
        "HACCP",
        "무항생제",
    ]
    assert extract_venison_bone_status(
        product
    ) == "무뼈"
    assert extract_venison_skin_status(
        product
    ) == "껍질 제거"


def test_extractors_support_fallback_fields() -> None:
    product = {
        "title": "사슴등심 구이용",
        "origin_country": "대한민국",
        "origin_country_code": "kr",
        "net_weight": 1000,
        "temperature_type": "냉장",
        "labels": "HACCP",
        "bone_type": "뼈 없음",
        "skin_type": "근막 정리",
    }

    assert extract_venison_product_name(
        product
    ) == "사슴등심 구이용"
    assert extract_venison_country_text(
        product
    ) == "대한민국"
    assert extract_venison_country_code(
        product
    ) == "KR"
    assert extract_venison_weight(
        product
    ) == 1000
    assert extract_venison_storage_type(
        product
    ) == "냉장"
    assert extract_venison_certifications(
        product
    ) == ["HACCP"]
    assert extract_venison_bone_status(
        product
    ) == "뼈 없음"
    assert extract_venison_skin_status(
        product
    ) == "근막 정리"


def test_build_complete_venison_attributes() -> None:
    product = {
        "product_name": (
            "뉴질랜드산 어린사슴 "
            "레드디어 사슴안심 500g"
        ),
        "venison_type": "어린 사슴",
        "deer_species": "Red Deer",
        "cut": "사슴 안심",
        "country": "뉴질랜드",
        "country_code": "NZ",
        "weight": "500g",
        "storage_type": "냉장",
        "certifications": [
            "HACCP",
            "무항생제",
        ],
        "bone_status": "무뼈",
        "skin_status": "근막 제거",
    }

    parse_result = (
        VenisonParser().parse_product(
            product
        )
    )

    attributes = build_venison_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["product_name"] == (
        product["product_name"]
    )
    assert attributes["country"] == (
        "뉴질랜드"
    )
    assert attributes["country_code"] == (
        "NZ"
    )
    assert attributes["weight"] == "500g"
    assert attributes["storage_type"] == (
        "냉장"
    )
    assert attributes["certifications"] == [
        "HACCP",
        "무항생제",
    ]
    assert attributes["bone_status"] == (
        "무뼈"
    )
    assert attributes["skin_status"] == (
        "근막 제거"
    )

    assert attributes["venison_type"] == (
        "어린사슴"
    )
    assert attributes["breed"] == "레드디어"
    assert attributes["cut"] == "사슴안심"

    assert attributes[
        "venison_type_registry_key"
    ] == "young_deer"
    assert attributes[
        "breed_registry_key"
    ] == "red_deer"
    assert attributes[
        "cut_registry_key"
    ] == "tenderloin"

    assert attributes[
        "venison_type_score"
    ] == 92.0
    assert attributes["breed_score"] == 90.0
    assert attributes["cut_score"] == 96.0

    assert attributes[
        "venison_type_premium"
    ] is True
    assert attributes["breed_premium"] is True
    assert attributes["cut_premium"] is True

    assert attributes["cut_group"] == "loin"
    assert attributes[
        "cut_tenderness_score"
    ] == 96.0
    assert attributes[
        "cut_flavor_score"
    ] == 86.0
    assert attributes[
        "cut_fat_score"
    ] == 30.0
    assert attributes[
        "cut_yield_score"
    ] == 55.0

    assert "스테이크" in attributes[
        "cut_cooking_methods"
    ]

    assert attributes["is_complete"] is True
    assert attributes["is_usable"] is True
    assert attributes["confidence"] > 0.0


def test_attributes_preserve_parser_priority() -> None:
    product = {
        "product_name": "뉴질랜드 사슴고기",
        "venison_type": "어린 사슴",
        "deer_species": "Red Deer",
        "cut": "사슴 안심",
    }

    parse_result = (
        VenisonParser().parse_product(
            product
        )
    )

    attributes = build_venison_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes[
        "cut_registry_key"
    ] == "tenderloin"
    assert attributes["cut"] == "사슴안심"


def test_build_cut_only_attributes() -> None:
    product = {
        "product_name": "사슴 뒷다리 정육",
        "cut": "사슴 뒷다리",
        "weight": "1kg",
    }

    parse_result = (
        VenisonParser().parse_product(
            product
        )
    )

    attributes = build_venison_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["venison_type"] is None
    assert attributes["breed"] is None
    assert attributes["cut"] == "사슴뒷다리"
    assert attributes[
        "cut_registry_key"
    ] == "leg"
    assert attributes["cut_group"] == "leg"
    assert attributes["is_complete"] is False
    assert attributes["is_usable"] is True

    assert (
        "venison_type_registry_key"
        not in attributes
    )
    assert (
        "breed_registry_key"
        not in attributes
    )




def test_build_breast_cut_attributes() -> None:
    product = {
        "product_name": (
            "뉴질랜드산 어린사슴 "
            "레드디어 사슴가슴살 500g"
        ),
        "venison_type": "어린 사슴",
        "deer_species": "Red Deer",
        "cut": "사슴 가슴살",
    }

    parse_result = (
        VenisonParser().parse_product(product)
    )

    attributes = build_venison_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["cut"] == "사슴가슴살"
    assert (
        attributes["cut_registry_key"]
        == "breast"
    )
    assert attributes["cut_score"] == 83.0
    assert attributes["cut_premium"] is False
    assert attributes["cut_group"] == "breast"
    assert (
        attributes["cut_tenderness_score"]
        == 72.0
    )
    assert attributes["cut_flavor_score"] == 90.0
    assert attributes["cut_fat_score"] == 38.0
    assert attributes["cut_yield_score"] == 76.0


def test_attributes_do_not_infer_structured_values() -> None:
    product = {
        "product_name": (
            "뉴질랜드 냉동 사슴안심 500g"
        )
    }

    parse_result = (
        VenisonParser().parse_product(
            product
        )
    )

    attributes = build_venison_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["country"] is None
    assert attributes["country_code"] is None
    assert attributes["weight"] is None
    assert attributes["storage_type"] is None


def test_certifications_are_deduplicated() -> None:
    product = {
        "certifications": [
            "HACCP",
            "haccp",
            " 무항생제 ",
            "",
        ]
    }

    assert extract_venison_certifications(
        product
    ) == [
        "HACCP",
        "무항생제",
    ]


def test_weight_preserves_zero_value() -> None:
    assert extract_venison_weight(
        {
            "weight": 0,
        }
    ) == 0


def test_build_attributes_copies_lists() -> None:
    product = {
        "product_name": (
            "어린사슴 레드디어 "
            "사슴안심"
        ),
    }

    parse_result = (
        VenisonParser().parse_product(
            product
        )
    )

    attributes = build_venison_attributes(
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


def test_build_attributes_rejects_non_mapping() -> None:
    parse_result = VenisonParser().parse(
        "사슴안심"
    )

    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        build_venison_attributes(
            product="사슴안심",  # type: ignore[arg-type]
            parse_result=parse_result,
        )


def test_build_attributes_rejects_wrong_parse_result() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "parse_result must be "
            "VenisonParseResult"
        ),
    ):
        build_venison_attributes(
            product={
                "product_name": "사슴안심",
            },
            parse_result=object(),  # type: ignore[arg-type]
        )


def test_empty_extractors_return_defaults() -> None:
    product: dict[str, object] = {}

    assert extract_venison_product_name(
        product
    ) == ""
    assert extract_venison_country_text(
        product
    ) is None
    assert extract_venison_country_code(
        product
    ) is None
    assert extract_venison_weight(
        product
    ) is None
    assert extract_venison_storage_type(
        product
    ) is None
    assert extract_venison_certifications(
        product
    ) == []
    assert extract_venison_bone_status(
        product
    ) is None
    assert extract_venison_skin_status(
        product
    ) is None


def test_parse_result_type_contract() -> None:
    result = VenisonParser().parse(
        "어린사슴 레드디어 사슴안심"
    )

    assert isinstance(
        result,
        VenisonParseResult,
    )
