from __future__ import annotations

import pytest

from app.services.food.knowledge.wine.parser import (
    WineParser,
)
from app.services.food.knowledge.wine.parser_models import (
    WineParseResult,
)


def test_wine_parser_detects_multiple_attributes() -> None:
    parser = WineParser()

    result = parser.parse(
        "2020 보르도 카베르네 소비뇽 "
        "레드 와인 드라이 풀 바디 높은 산도 13.5%"
    )

    assert isinstance(
        result,
        WineParseResult,
    )
    assert result.wine_type == "red"
    assert (
        result.grape
        == "cabernet_sauvignon"
    )
    assert result.region == "bordeaux"
    assert result.sweetness == "dry"
    assert result.body == "full"
    assert result.acidity == "high"
    assert result.vintage == 2020
    assert result.alcohol_percent == 13.5
    assert result.is_complete is True
    assert result.is_usable is True


@pytest.mark.parametrize(
    (
        "text",
        "field_name",
        "expected",
    ),
    [
        (
            "화이트 와인",
            "wine_type",
            "white",
        ),
        (
            "샤르도네 와인",
            "grape",
            "chardonnay",
        ),
        (
            "부르고뉴 와인",
            "region",
            "burgundy",
        ),
        (
            "세미 드라이 와인",
            "sweetness",
            "off_dry",
        ),
        (
            "미디엄 바디 와인",
            "body",
            "medium",
        ),
        (
            "낮은 산도 와인",
            "acidity",
            "low",
        ),
    ],
)
def test_wine_parser_detects_each_registry_field(
    text: str,
    field_name: str,
    expected: str,
) -> None:
    result = WineParser().parse(
        text
    )

    assert (
        getattr(result, field_name)
        == expected
    )


def test_wine_parser_extracts_vintage() -> None:
    result = WineParser().parse(
        "2019 나파 밸리 레드 와인"
    )

    assert result.vintage == 2019


@pytest.mark.parametrize(
    (
        "text",
        "expected",
    ),
    [
        (
            "알코올 12.5%",
            12.5,
        ),
        (
            "ABV 14%",
            14.0,
        ),
        (
            "도수 13도",
            13.0,
        ),
    ],
)
def test_wine_parser_extracts_alcohol_percent(
    text: str,
    expected: float,
) -> None:
    result = WineParser().parse(
        text
    )

    assert (
        result.alcohol_percent
        == expected
    )


def test_wine_parser_uses_structured_fields_first() -> None:
    result = WineParser().parse_product(
        {
            "product_name": (
                "일반 레드 와인"
            ),
            "wine_type": (
                "화이트 와인"
            ),
            "grape_variety": (
                "샤르도네"
            ),
            "region": "부르고뉴",
            "sweetness": "드라이",
            "body": "미디엄 바디",
            "acidity": "높은 산도",
            "vintage": 2021,
            "alcohol_percent": 12.5,
        }
    )

    assert result.wine_type == "white"
    assert result.grape == "chardonnay"
    assert result.region == "burgundy"
    assert result.sweetness == "dry"
    assert result.body == "medium"
    assert result.acidity == "high"
    assert result.vintage == 2021
    assert result.alcohol_percent == 12.5
    assert (
        result.metadata[
            "structured_field_priority"
        ]
        is True
    )


def test_wine_parser_records_detection_evidence() -> None:
    result = WineParser().parse(
        "보르도 카베르네 소비뇽 레드 와인"
    )

    assert "보르도" in result.detected_keywords
    assert (
        "카베르네 소비뇽"
        in result.detected_keywords
    )
    assert "레드 와인" in result.detected_keywords
    assert result.confidence > 0.0


def test_wine_parser_returns_unusable_result_for_unknown_text() -> None:
    result = WineParser().parse(
        "등록되지 않은 임의의 상품"
    )

    assert result.has_match is False
    assert result.is_usable is False
    assert result.confidence == 0.0
    assert result.warnings


def test_wine_parser_rejects_empty_text() -> None:
    parser = WineParser()

    with pytest.raises(ValueError):
        parser.parse("")


def test_wine_parser_rejects_non_mapping_product() -> None:
    parser = WineParser()

    with pytest.raises(TypeError):
        parser.parse_product(  # type: ignore[arg-type]
            "not-a-mapping"
        )


def test_wine_parser_rejects_empty_product() -> None:
    parser = WineParser()

    with pytest.raises(ValueError):
        parser.parse_product({})


def test_wine_parser_is_deterministic() -> None:
    parser = WineParser()
    text = (
        "2020 보르도 카베르네 소비뇽 "
        "레드 와인 드라이"
    )

    first = parser.parse(text)
    second = parser.parse(text)

    assert first.to_dict() == second.to_dict()
