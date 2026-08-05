from __future__ import annotations

from copy import deepcopy

import pytest

from app.services.food.knowledge.tea.attributes import (
    build_tea_attributes,
    extract_tea_caffeine_status,
    extract_tea_certifications,
    extract_tea_flavor_notes,
)
from app.services.food.knowledge.tea.parser import (
    TeaParser,
)


def _complete_product() -> dict[str, object]:
    return {
        "product_name": (
            "제주 야부키타 증제 "
            "비산화 감칠맛 녹차"
        ),
        "tea_type": "green tea",
        "origin": "Jeju",
        "country": "South Korea",
        "country_code": "kr",
        "cultivar": "Yabukita",
        "processing_method": "steamed tea",
        "oxidation_level": "unoxidized",
        "flavor_notes": [
            "감칠맛",
            "풀향",
        ],
        "weight": "100g",
        "packaging_type": "loose leaf",
        "harvest_year": 2026,
        "grade": "premium",
        "leaf_style": "whole leaf",
        "caffeine_status": "regular",
        "certifications": [
            "Organic",
            "HACCP",
        ],
    }


def test_complete_tea_attributes() -> None:
    product = _complete_product()

    parse_result = TeaParser().parse_product(
        product
    )

    attributes = build_tea_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["product_name"] == (
        product["product_name"]
    )
    assert attributes["tea_type"] == "green"
    assert attributes["origin"] == "jeju"
    assert attributes["variety"] == "yabukita"
    assert attributes["processing"] == "steamed"
    assert attributes["oxidation"] == "unoxidized"
    assert attributes["flavor"] == "umami"

    assert attributes["country"] == "South Korea"
    assert attributes["country_code"] == "KR"
    assert attributes["weight"] == "100g"
    assert (
        attributes["packaging_type"]
        == "loose leaf"
    )
    assert attributes["harvest_year"] == 2026
    assert attributes["grade"] == "premium"
    assert attributes["leaf_style"] == "whole leaf"
    assert (
        attributes["caffeine_status"]
        == "regular"
    )
    assert attributes["certifications"] == [
        "Organic",
        "HACCP",
    ]
    assert attributes["flavor_notes"] == [
        "감칠맛",
        "풀향",
    ]

    assert attributes["matched_field_count"] == 6
    assert attributes["is_complete"] is True
    assert attributes["is_usable"] is True


def test_complete_registry_metadata() -> None:
    product = _complete_product()

    parse_result = TeaParser().parse_product(
        product
    )

    attributes = build_tea_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert (
        attributes["tea_type_registry_key"]
        == "green"
    )
    assert (
        attributes["origin_registry_key"]
        == "jeju"
    )
    assert (
        attributes["variety_registry_key"]
        == "yabukita"
    )
    assert (
        attributes["processing_registry_key"]
        == "steamed"
    )
    assert (
        attributes["oxidation_registry_key"]
        == "unoxidized"
    )
    assert (
        attributes["flavor_registry_key"]
        == "umami"
    )

    assert attributes["origin_country_code"] == "KR"
    assert (
        attributes["origin_country_name"]
        == "South Korea"
    )
    assert attributes["origin_region_name"] == "Jeju"

    assert (
        attributes["variety_botanical_name"]
        == "Camellia sinensis"
    )
    assert attributes["variety_kind"] == "cultivar"
    assert attributes["variety_country_code"] == "JP"

    assert (
        attributes["processing_category"]
        == "heat_fixation"
    )
    assert (
        attributes["processing_heat_fixation"]
        is True
    )
    assert (
        attributes[
            "processing_microbial_fermentation"
        ]
        is False
    )

    assert attributes["oxidation_level"] == 0
    assert (
        attributes["oxidation_min_percent"]
        == 0.0
    )
    assert (
        attributes["oxidation_max_percent"]
        == 5.0
    )
    assert (
        attributes["oxidation_fully_oxidized"]
        is False
    )

    assert attributes["flavor_family"] == "savory"
    assert (
        attributes["flavor_sensory_dimension"]
        == "taste"
    )
    assert (
        attributes["flavor_aroma_dominant"]
        is False
    )
    assert (
        attributes["flavor_taste_dominant"]
        is True
    )


def test_partial_tea_attributes() -> None:
    product = {
        "product_name": (
            "다즐링 꽃향 차 100g"
        ),
        "weight": "100g",
    }

    parse_result = TeaParser().parse_product(
        product
    )

    attributes = build_tea_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["tea_type"] is None
    assert attributes["origin"] == "darjeeling"
    assert attributes["flavor"] == "floral"
    assert attributes["weight"] == "100g"

    assert attributes["matched_field_count"] == 2
    assert attributes["is_complete"] is False
    assert attributes["is_usable"] is True

    assert (
        attributes["origin_registry_key"]
        == "darjeeling"
    )
    assert (
        attributes["flavor_registry_key"]
        == "floral"
    )

    assert "tea_type_registry_key" not in attributes
    assert "variety_registry_key" not in attributes


def test_unknown_tea_attributes() -> None:
    product = {
        "product_name": "일반 식품 상품",
    }

    parse_result = TeaParser().parse_product(
        product
    )

    attributes = build_tea_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["tea_type"] is None
    assert attributes["origin"] is None
    assert attributes["variety"] is None
    assert attributes["processing"] is None
    assert attributes["oxidation"] is None
    assert attributes["flavor"] is None

    assert attributes["matched_field_count"] == 0
    assert attributes["is_complete"] is False
    assert attributes["is_usable"] is False
    assert attributes["confidence"] == 0.0
    assert attributes["parser_warnings"]


def test_country_falls_back_to_origin_registry() -> None:
    product = {
        "product_name": "제주 녹차",
    }

    parse_result = TeaParser().parse_product(
        product
    )

    attributes = build_tea_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["origin"] == "jeju"
    assert attributes["country"] == "South Korea"
    assert attributes["country_code"] == "KR"


def test_explicit_country_has_priority() -> None:
    product = {
        "product_name": "제주 녹차",
        "country": "Republic of Korea",
        "country_code": "kr",
    }

    parse_result = TeaParser().parse_product(
        product
    )

    attributes = build_tea_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["origin"] == "jeju"
    assert (
        attributes["country"]
        == "Republic of Korea"
    )
    assert attributes["country_code"] == "KR"


@pytest.mark.parametrize(
    (
        "value",
        "expected",
    ),
    [
        (True, "decaf"),
        (False, "regular"),
        ("caffeine free", "caffeine free"),
        ("regular", "regular"),
        (None, None),
    ],
)
def test_extract_tea_caffeine_status(
    value: object,
    expected: str | None,
) -> None:
    product: dict[str, object] = {}

    if value is not None:
        product["caffeine_status"] = value

    assert (
        extract_tea_caffeine_status(
            product
        )
        == expected
    )


def test_certifications_are_normalized() -> None:
    assert extract_tea_certifications(
        {
            "certifications": [
                "Organic",
                "Organic",
                " HACCP ",
                "",
            ]
        }
    ) == [
        "Organic",
        "HACCP",
    ]

    assert extract_tea_certifications(
        {
            "certification": "JAS",
        }
    ) == [
        "JAS",
    ]

    assert extract_tea_certifications({}) == []


def test_flavor_notes_are_normalized() -> None:
    assert extract_tea_flavor_notes(
        {
            "flavor_notes": (
                "꽃향, 감칠맛 / 풀향"
            )
        }
    ) == [
        "꽃향",
        "감칠맛",
        "풀향",
    ]

    assert extract_tea_flavor_notes(
        {
            "tasting_notes": [
                "꿀향",
                "꿀향",
                " 시트러스 ",
                "",
            ]
        }
    ) == [
        "꿀향",
        "시트러스",
    ]

    assert extract_tea_flavor_notes({}) == []


def test_attributes_do_not_mutate_inputs() -> None:
    product = _complete_product()
    product_before = deepcopy(product)

    parse_result = TeaParser().parse_product(
        product
    )
    parse_result_before = (
        parse_result.to_dict()
    )

    build_tea_attributes(
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

    parse_result = TeaParser().parse_product(
        product
    )

    attributes = build_tea_attributes(
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
    parse_result = TeaParser().parse(
        "녹차"
    )

    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        build_tea_attributes(
            product="녹차",  # type: ignore[arg-type]
            parse_result=parse_result,
        )


def test_attributes_reject_invalid_parse_result() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "parse_result must be "
            "TeaParseResult"
        ),
    ):
        build_tea_attributes(
            product={
                "product_name": "녹차",
            },
            parse_result=object(),  # type: ignore[arg-type]
        )


def test_attributes_are_deterministic() -> None:
    product = _complete_product()

    parse_result = TeaParser().parse_product(
        product
    )

    first = build_tea_attributes(
        product=product,
        parse_result=parse_result,
    )
    second = build_tea_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert first == second


def test_attributes_do_not_calculate_scores() -> None:
    product = _complete_product()

    parse_result = TeaParser().parse_product(
        product
    )

    attributes = build_tea_attributes(
        product=product,
        parse_result=parse_result,
    )

    registry_score_keys = {
        "tea_type_score",
        "origin_score",
        "variety_score",
        "processing_score",
        "oxidation_score",
        "flavor_score",
    }

    assert registry_score_keys.issubset(
        attributes.keys()
    )

    assert "knowledge_score" not in attributes
    assert "final_score" not in attributes
    assert "quality_score" not in attributes
    assert "price_score" not in attributes
    assert "trust_score" not in attributes
