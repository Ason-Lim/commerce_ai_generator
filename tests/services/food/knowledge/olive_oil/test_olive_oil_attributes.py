from __future__ import annotations

import pytest

from app.services.food.knowledge.olive_oil.attributes import (
    extract_olive_oil_product_name,
)


def test_extract_product_name_uses_primary_field() -> None:
    product = {
        "product_name": "Primary Olive Oil",
        "title": "Secondary Olive Oil",
        "name": "Third Olive Oil",
    }

    assert (
        extract_olive_oil_product_name(product)
        == "Primary Olive Oil"
    )


def test_extract_product_name_uses_title_fallback() -> None:
    product = {
        "title": "스페인 엑스트라 버진 올리브오일",
    }

    assert (
        extract_olive_oil_product_name(product)
        == "스페인 엑스트라 버진 올리브오일"
    )


def test_extract_product_name_uses_name_fallback() -> None:
    product = {
        "name": "아르베키나 올리브오일",
    }

    assert (
        extract_olive_oil_product_name(product)
        == "아르베키나 올리브오일"
    )


def test_extract_product_name_uses_raw_name_fallback() -> None:
    product = {
        "raw_name": "냉압착 올리브유",
    }

    assert (
        extract_olive_oil_product_name(product)
        == "냉압착 올리브유"
    )


def test_extract_product_name_uses_display_name_fallback() -> None:
    product = {
        "display_name": "그리스산 올리브오일",
    }

    assert (
        extract_olive_oil_product_name(product)
        == "그리스산 올리브오일"
    )


def test_extract_product_name_strips_whitespace() -> None:
    product = {
        "product_name": "  엑스트라 버진 올리브오일  ",
    }

    assert (
        extract_olive_oil_product_name(product)
        == "엑스트라 버진 올리브오일"
    )


def test_extract_product_name_returns_empty_string() -> None:
    assert extract_olive_oil_product_name({}) == ""


from app.services.food.knowledge.olive_oil.attributes import (
    extract_olive_oil_country_code,
    extract_olive_oil_country_text,
)
from app.services.food.knowledge.olive_oil.parser import (
    OliveOilParser,
)


def test_country_falls_back_to_origin_registry() -> None:
    product = {
        "product_name": "스페인산 엑스트라 버진 올리브오일",
    }

    parse_result = OliveOilParser().parse_product(
        product
    )

    assert (
        extract_olive_oil_country_text(
            product=product,
            parse_result=parse_result,
        )
        == "spain"
    )

    assert (
        extract_olive_oil_country_code(
            product=product,
            parse_result=parse_result,
        )
        == "ES"
    )


def test_explicit_country_has_priority() -> None:
    product = {
        "product_name": "스페인산 올리브오일",
        "country": "Kingdom of Spain",
        "country_code": "es",
    }

    parse_result = OliveOilParser().parse_product(
        product
    )

    assert (
        extract_olive_oil_country_text(
            product=product,
            parse_result=parse_result,
        )
        == "Kingdom of Spain"
    )

    assert (
        extract_olive_oil_country_code(
            product=product,
            parse_result=parse_result,
        )
        == "ES"
    )


def test_country_extractors_return_none_without_origin() -> None:
    product = {
        "product_name": "일반 식품 상품",
    }

    parse_result = OliveOilParser().parse_product(
        product
    )

    assert (
        extract_olive_oil_country_text(
            product=product,
            parse_result=parse_result,
        )
        is None
    )

    assert (
        extract_olive_oil_country_code(
            product=product,
            parse_result=parse_result,
        )
        is None
    )


from app.services.food.knowledge.olive_oil.attributes import (
    extract_olive_oil_certifications,
    extract_olive_oil_organic_status,
    extract_olive_oil_packaging_type,
    extract_olive_oil_volume,
)


def test_extract_volume_uses_priority_order() -> None:
    product = {
        "volume": "500ml",
        "volume_ml": 750,
        "capacity": "1L",
    }

    assert (
        extract_olive_oil_volume(product)
        == "500ml"
    )


def test_extract_volume_uses_fallback_fields() -> None:
    assert extract_olive_oil_volume(
        {
            "volume_ml": 750,
        }
    ) == 750

    assert extract_olive_oil_volume(
        {
            "capacity": "1L",
        }
    ) == "1L"

    assert extract_olive_oil_volume({}) is None


def test_extract_packaging_type() -> None:
    assert (
        extract_olive_oil_packaging_type(
            {
                "packaging_type": "dark glass bottle",
            }
        )
        == "dark glass bottle"
    )

    assert (
        extract_olive_oil_packaging_type(
            {
                "container_type": "tin",
            }
        )
        == "tin"
    )

    assert (
        extract_olive_oil_packaging_type({})
        is None
    )


def test_certifications_are_normalized() -> None:
    assert extract_olive_oil_certifications(
        {
            "certifications": [
                "Organic",
                "PDO",
                "Organic",
                " PDO ",
                "",
            ]
        }
    ) == [
        "Organic",
        "PDO",
    ]

    assert extract_olive_oil_certifications(
        {
            "certification": "PGI",
        }
    ) == [
        "PGI",
    ]

    assert (
        extract_olive_oil_certifications({})
        == []
    )


@pytest.mark.parametrize(
    (
        "raw_value",
        "expected",
    ),
    [
        (True, True),
        (False, False),
        ("organic", True),
        ("유기농", True),
        ("yes", True),
        ("no", False),
        ("non-organic", False),
        ("일반", False),
        ("unknown", None),
    ],
)
def test_extract_organic_status(
    raw_value: object,
    expected: bool | None,
) -> None:
    assert (
        extract_olive_oil_organic_status(
            {
                "organic": raw_value,
            }
        )
        is expected
    )


def test_extract_organic_status_uses_field_presence() -> None:
    assert (
        extract_olive_oil_organic_status(
            {
                "is_organic": False,
            }
        )
        is False
    )

    assert (
        extract_olive_oil_organic_status({})
        is None
    )


from copy import deepcopy

from app.services.food.knowledge.olive_oil.attributes import (
    build_olive_oil_attributes,
)


def _complete_olive_oil_product() -> dict[str, object]:
    return {
        "product_name": (
            "스페인산 아르베키나 단일 품종 "
            "냉압착 엑스트라 버진 올리브오일"
        ),
        "olive_oil_type": "single varietal",
        "cultivar": "Arbequina",
        "origin_country": "Spain",
        "country": "Spain",
        "country_code": "es",
        "extraction_method": "cold pressed",
        "grade": "extra virgin olive oil",
        "volume": "500ml",
        "packaging_type": "dark glass bottle",
        "organic": True,
        "certifications": [
            "Organic",
            "PDO",
        ],
    }


def test_build_complete_olive_oil_attributes() -> None:
    product = _complete_olive_oil_product()

    parse_result = OliveOilParser().parse_product(
        product
    )

    attributes = build_olive_oil_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["product_name"] == (
        product["product_name"]
    )
    assert (
        attributes["olive_oil_type"]
        == "single_varietal"
    )
    assert attributes["variety"] == "arbequina"
    assert attributes["origin"] == "spain"
    assert attributes["processing"] == "cold_pressed"
    assert attributes["grade"] == "extra_virgin"

    assert attributes["country"] == "Spain"
    assert attributes["country_code"] == "ES"
    assert attributes["volume"] == "500ml"
    assert (
        attributes["packaging_type"]
        == "dark glass bottle"
    )
    assert attributes["organic"] is True
    assert attributes["certifications"] == [
        "Organic",
        "PDO",
    ]

    assert attributes["matched_field_count"] == 5
    assert attributes["is_complete"] is True
    assert attributes["is_usable"] is True


def test_build_attributes_registry_metadata() -> None:
    product = _complete_olive_oil_product()

    parse_result = OliveOilParser().parse_product(
        product
    )

    attributes = build_olive_oil_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert (
        attributes[
            "olive_oil_type_registry_key"
        ]
        == "single_varietal"
    )
    assert (
        attributes["variety_registry_key"]
        == "arbequina"
    )
    assert (
        attributes["origin_registry_key"]
        == "spain"
    )
    assert (
        attributes["processing_registry_key"]
        == "cold_pressed"
    )
    assert (
        attributes["grade_registry_key"]
        == "extra_virgin"
    )

    assert (
        attributes["variety_cultivar_origin"]
        == "Spain"
    )
    assert (
        attributes["origin_country_code"]
        == "ES"
    )
    assert (
        attributes[
            "processing_mechanical_only"
        ]
        is True
    )
    assert (
        attributes[
            "processing_cold_extracted"
        ]
        is True
    )
    assert (
        attributes["processing_refined"]
        is False
    )
    assert attributes["grade_virgin"] is True
    assert attributes["grade_refined"] is False
    assert attributes["grade_pomace"] is False
    assert attributes["grade_score"] == 95.0


def test_build_partial_olive_oil_attributes() -> None:
    product = {
        "product_name": (
            "스페인 아르베키나 올리브오일"
        ),
        "volume": "250ml",
    }

    parse_result = OliveOilParser().parse_product(
        product
    )

    attributes = build_olive_oil_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["variety"] == "arbequina"
    assert attributes["origin"] == "spain"
    assert attributes["volume"] == "250ml"
    assert attributes["matched_field_count"] >= 2
    assert attributes["is_complete"] is False
    assert attributes["is_usable"] is True


def test_build_unknown_olive_oil_attributes() -> None:
    product = {
        "product_name": "일반 식품 상품",
    }

    parse_result = OliveOilParser().parse_product(
        product
    )

    attributes = build_olive_oil_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["olive_oil_type"] is None
    assert attributes["variety"] is None
    assert attributes["origin"] is None
    assert attributes["processing"] is None
    assert attributes["grade"] is None
    assert attributes["matched_field_count"] == 0
    assert attributes["is_complete"] is False
    assert attributes["is_usable"] is False
    assert attributes["confidence"] == 0.0
    assert attributes["parser_warnings"]


def test_builder_does_not_mutate_inputs() -> None:
    product = _complete_olive_oil_product()
    product_before = deepcopy(product)

    parse_result = OliveOilParser().parse_product(
        product
    )
    parse_result_before = (
        parse_result.to_dict()
    )

    build_olive_oil_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert product == product_before
    assert (
        parse_result.to_dict()
        == parse_result_before
    )


def test_builder_list_values_are_copies() -> None:
    product = _complete_olive_oil_product()

    parse_result = OliveOilParser().parse_product(
        product
    )

    attributes = build_olive_oil_attributes(
        product=product,
        parse_result=parse_result,
    )

    attributes["certifications"].append(
        "TEST"
    )
    attributes["detected_keywords"].append(
        "TEST"
    )

    assert "TEST" not in product[
        "certifications"
    ]
    assert (
        "TEST"
        not in parse_result.detected_keywords
    )


def test_builder_rejects_invalid_product() -> None:
    parse_result = OliveOilParser().parse(
        "엑스트라 버진 올리브오일"
    )

    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        build_olive_oil_attributes(
            product="invalid",  # type: ignore[arg-type]
            parse_result=parse_result,
        )


def test_builder_rejects_invalid_parse_result() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "parse_result must be "
            "OliveOilParseResult"
        ),
    ):
        build_olive_oil_attributes(
            product={
                "product_name": "올리브오일",
            },
            parse_result=object(),  # type: ignore[arg-type]
        )


def test_builder_is_deterministic() -> None:
    product = _complete_olive_oil_product()

    parse_result = OliveOilParser().parse_product(
        product
    )

    first = build_olive_oil_attributes(
        product=product,
        parse_result=parse_result,
    )
    second = build_olive_oil_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert first == second


def test_builder_does_not_calculate_scores() -> None:
    product = _complete_olive_oil_product()

    parse_result = OliveOilParser().parse_product(
        product
    )

    attributes = build_olive_oil_attributes(
        product=product,
        parse_result=parse_result,
    )

    registry_score_keys = {
        "olive_oil_type_score",
        "variety_score",
        "origin_score",
        "processing_score",
        "grade_score",
    }

    assert registry_score_keys.issubset(
        attributes.keys()
    )

    assert "knowledge_score" not in attributes
    assert "final_score" not in attributes
    assert "quality_score" not in attributes
    assert "price_score" not in attributes
    assert "trust_score" not in attributes
