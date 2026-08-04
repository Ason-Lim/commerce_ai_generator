from __future__ import annotations

import pytest

from app.services.food.knowledge.wine.attributes import (
    build_wine_attributes,
    extract_wine_product_name,
)
from app.services.food.knowledge.wine.parser import (
    WineParser,
)


def test_extract_wine_product_name_priority() -> None:
    product = {
        "product_name": "Primary Name",
        "title": "Secondary Name",
        "name": "Third Name",
    }

    assert (
        extract_wine_product_name(product)
        == "Primary Name"
    )


def test_extract_wine_product_name_fallback() -> None:
    product = {
        "title": "Wine Title",
    }

    assert (
        extract_wine_product_name(product)
        == "Wine Title"
    )


def test_build_wine_attributes_from_parser_result() -> None:
    product = {
        "product_name": (
            "2020 보르도 카베르네 소비뇽 "
            "레드 와인 드라이 풀 바디 높은 산도"
        ),
        "volume": "750ml",
        "packaging_type": "bottle",
        "closure_type": "cork",
        "producer": "Example Winery",
    }

    parse_result = WineParser().parse_product(
        product
    )

    attributes = build_wine_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["wine_type"] == "red"
    assert (
        attributes["grape"]
        == "cabernet_sauvignon"
    )
    assert attributes["region"] == "bordeaux"
    assert attributes["country"] == "France"
    assert attributes["country_code"] == "FR"
    assert attributes["sweetness"] == "dry"
    assert attributes["body"] == "full"
    assert attributes["acidity"] == "high"
    assert attributes["vintage"] == 2020
    assert attributes["volume"] == "750ml"
    assert (
        attributes["packaging_type"]
        == "bottle"
    )
    assert attributes["closure_type"] == "cork"
    assert (
        attributes["producer"]
        == "Example Winery"
    )
    assert attributes["is_usable"] is True
    assert attributes["matched_field_count"] == 6


def test_build_wine_attributes_registry_metadata() -> None:
    product = {
        "product_name": (
            "부르고뉴 샤르도네 "
            "화이트 와인 드라이 "
            "미디엄 바디 높은 산도"
        ),
    }

    parse_result = WineParser().parse_product(
        product
    )

    attributes = build_wine_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert (
        attributes["wine_type_color_family"]
        == "white"
    )
    assert (
        attributes["wine_type_sparkling"]
        is False
    )
    assert attributes["grape_color"] == "white"
    assert (
        attributes["grape_species"]
        == "vitis_vinifera"
    )
    assert (
        attributes["region_appellation"]
        == "Bourgogne"
    )
    assert attributes["sweetness_level"] == 1
    assert attributes["body_level"] == 2
    assert attributes["acidity_level"] == 3


def test_structured_country_overrides_registry_country() -> None:
    product = {
        "product_name": "보르도 레드 와인",
        "country": "Custom Country",
        "country_code": "xy",
    }

    parse_result = WineParser().parse_product(
        product
    )

    attributes = build_wine_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert (
        attributes["country"]
        == "Custom Country"
    )
    assert attributes["country_code"] == "XY"


def test_build_wine_attributes_certifications() -> None:
    product = {
        "product_name": "보르도 레드 와인",
        "certifications": [
            "Organic",
            "AOC",
            "Organic",
            "",
        ],
    }

    parse_result = WineParser().parse_product(
        product
    )

    attributes = build_wine_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["certifications"] == [
        "Organic",
        "AOC",
    ]


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
        ("no", False),
    ],
)
def test_build_wine_attributes_organic_status(
    raw_value: object,
    expected: bool,
) -> None:
    product = {
        "product_name": "보르도 레드 와인",
        "organic": raw_value,
    }

    parse_result = WineParser().parse_product(
        product
    )

    attributes = build_wine_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["organic"] is expected


def test_build_wine_attributes_biodynamic_status() -> None:
    product = {
        "product_name": "부르고뉴 와인",
        "biodynamic": "바이오다이나믹",
    }

    parse_result = WineParser().parse_product(
        product
    )

    attributes = build_wine_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["biodynamic"] is True


def test_build_wine_attributes_preserves_alcohol_percent() -> None:
    product = {
        "product_name": (
            "2021 나파 밸리 "
            "카베르네 소비뇽 레드 와인 13.5%"
        ),
    }

    parse_result = WineParser().parse_product(
        product
    )

    attributes = build_wine_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert attributes["vintage"] == 2021
    assert attributes["alcohol_percent"] == 13.5


def test_build_wine_attributes_rejects_invalid_product() -> None:
    parse_result = WineParser().parse(
        "보르도 레드 와인"
    )

    with pytest.raises(TypeError):
        build_wine_attributes(
            product="invalid",  # type: ignore[arg-type]
            parse_result=parse_result,
        )


def test_build_wine_attributes_rejects_invalid_parse_result() -> None:
    with pytest.raises(TypeError):
        build_wine_attributes(
            product={
                "product_name": "보르도 와인",
            },
            parse_result=None,  # type: ignore[arg-type]
        )


def test_build_wine_attributes_is_deterministic() -> None:
    product = {
        "product_name": (
            "2020 보르도 카베르네 소비뇽 "
            "레드 와인 드라이"
        ),
        "certifications": [
            "AOC",
            "Organic",
        ],
    }

    parse_result = WineParser().parse_product(
        product
    )

    first = build_wine_attributes(
        product=product,
        parse_result=parse_result,
    )
    second = build_wine_attributes(
        product=product,
        parse_result=parse_result,
    )

    assert first == second
