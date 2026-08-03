from __future__ import annotations

import inspect
from collections.abc import Mapping

import pytest

from app.services.food.knowledge.meat.goat import (
    GoatKnowledgeProvider,
    GoatParser,
)
from app.services.food.knowledge.models import (
    FoodKnowledgeContext,
    FoodKnowledgeResult,
)


@pytest.fixture
def provider() -> GoatKnowledgeProvider:
    return GoatKnowledgeProvider()


@pytest.fixture
def complete_product() -> dict[str, object]:
    return {
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
        "quality_score": 80,
        "price_score": 70,
        "trust_score": 90,
    }


def test_provider_identity(
    provider: GoatKnowledgeProvider,
) -> None:
    assert provider.category_id == "goat"
    assert provider.category_name == "염소고기"
    assert provider.parent_category_id == "meat"
    assert provider.provider_id == "goat"
    assert isinstance(
        provider.parser,
        GoatParser,
    )


def test_provider_supports(
    provider: GoatKnowledgeProvider,
) -> None:
    assert provider.supports(
        category_id="goat"
    )
    assert provider.supports(
        category_id="GOAT"
    )
    assert provider.supports(
        category_id="염소고기"
    )
    assert provider.supports(
        product_name="국내산 흑염소 정육"
    )
    assert provider.supports(
        product_name="Boer goat tenderloin"
    )

    assert not provider.supports(
        product_name="한우 등심"
    )
    assert not provider.supports(
        product_name="양고기 프렌치랙"
    )
    assert not provider.supports(
        product_name="안심 500g"
    )


def test_provider_accepts_parser_injection() -> None:
    parser = GoatParser()

    provider = GoatKnowledgeProvider(
        parser=parser
    )

    assert provider.parser is parser


def test_provider_complete_analysis(
    provider: GoatKnowledgeProvider,
    complete_product: dict[str, object],
) -> None:
    context = FoodKnowledgeContext(
        query="프리미엄 염소안심",
        priority="quality",
    )

    result = provider.analyze(
        complete_product,
        context=context,
    )

    assert isinstance(
        result,
        FoodKnowledgeResult,
    )

    assert result.category_id == "goat"
    assert result.category_name == "염소고기"
    assert result.attributes[
        "goat_type"
    ] == "어린염소"
    assert result.attributes["breed"] == "보어"
    assert result.attributes["cut"] == "염소안심"

    assert result.scores["knowledge"] == 95.0
    assert result.final_score == 87.5
    assert result.confidence > 0.0
    assert result.reasons
    assert result.warnings == []

    assert (
        result.metadata["provider_id"]
        == "goat"
    )
    assert (
        result.metadata["category_id"]
        == "goat"
    )
    assert (
        result.metadata[
            "parent_category_id"
        ]
        == "meat"
    )
    assert (
        result.metadata["priority"]
        == "quality"
    )
    assert (
        result.metadata["is_complete"]
        is True
    )
    assert (
        result.metadata["is_usable"]
        is True
    )

    assert isinstance(
        result.attributes,
        Mapping,
    )
    assert isinstance(
        result.scores,
        Mapping,
    )
    assert result.raw_product == (
        complete_product
    )
    assert (
        result.raw_product
        is not complete_product
    )


def test_provider_cut_only_analysis(
    provider: GoatKnowledgeProvider,
) -> None:
    result = provider.analyze(
        {
            "product_name": "염소안심 500g",
            "country": "뉴질랜드",
        }
    )

    assert result.attributes[
        "goat_type"
    ] is None
    assert result.attributes["breed"] is None
    assert result.attributes["cut"] == "염소안심"
    assert result.scores["knowledge"] == 96.0
    assert result.final_score == 48.0
    assert result.warnings

    assert (
        result.metadata[
            "matched_field_count"
        ]
        == 1
    )
    assert (
        result.metadata["is_complete"]
        is False
    )
    assert (
        result.metadata["is_usable"]
        is True
    )


def test_provider_unrecognized_analysis(
    provider: GoatKnowledgeProvider,
) -> None:
    result = provider.analyze(
        {
            "product_name": "일반 식품 상품",
            "country": "대한민국",
        }
    )

    assert result.attributes[
        "goat_type"
    ] is None
    assert result.attributes["breed"] is None
    assert result.attributes["cut"] is None
    assert result.scores["knowledge"] == 0.0
    assert result.final_score == 0.0
    assert result.confidence == 0.0
    assert result.warnings

    assert (
        result.metadata[
            "matched_field_count"
        ]
        == 0
    )
    assert (
        result.metadata["is_complete"]
        is False
    )
    assert (
        result.metadata["is_usable"]
        is False
    )


def test_provider_rejects_invalid_input(
    provider: GoatKnowledgeProvider,
) -> None:
    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        provider.analyze(
            "염소고기"  # type: ignore[arg-type]
        )

    with pytest.raises(
        ValueError,
        match="product must not be empty",
    ):
        provider.analyze({})


def test_provider_has_no_generator_dependency() -> None:
    source = inspect.getsource(
        GoatKnowledgeProvider
    )

    assert "domain_generator" not in source
    assert "tools." not in source
