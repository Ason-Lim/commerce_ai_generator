from __future__ import annotations

import pytest

from app.services.food.knowledge.meat.duck.parser import (
    DuckParser,
)
from app.services.food.knowledge.meat.duck.provider import (
    DuckKnowledgeProvider,
)
from app.services.food.knowledge.models import (
    FoodKnowledgeContext,
    FoodKnowledgeResult,
)


@pytest.fixture
def provider() -> DuckKnowledgeProvider:
    return DuckKnowledgeProvider()


@pytest.fixture
def complete_product() -> dict[str, object]:
    return {
        "product_name": (
            "국내산 훈제오리 체리밸리 "
            "오리가슴살 500g"
        ),
        "country": "대한민국",
        "country_code": "KR",
        "storage_type": "냉장",
        "certifications": [
            "무항생제",
            "HACCP",
        ],
        "quality_score": 80,
        "price_score": 70,
        "trust_score": 90,
    }


def test_provider_identity(
    provider: DuckKnowledgeProvider,
) -> None:
    assert provider.category_id == "duck"
    assert provider.category_name == "오리고기"
    assert isinstance(
        provider.parser,
        DuckParser,
    )


def test_provider_supports_category_id(
    provider: DuckKnowledgeProvider,
) -> None:
    assert provider.supports(
        category_id="duck"
    )
    assert provider.supports(
        category_id="DUCK"
    )
    assert provider.supports(
        category_id="오리고기"
    )
    assert not provider.supports(
        category_id="chicken"
    )


def test_provider_supports_product_name(
    provider: DuckKnowledgeProvider,
) -> None:
    assert provider.supports(
        product_name="국내산 오리가슴살 1kg"
    )
    assert provider.supports(
        product_name="훈제오리 슬라이스"
    )
    assert provider.supports(
        product_name="Duck Breast 500g"
    )
    assert not provider.supports(
        product_name="한우 등심 500g"
    )


def test_provider_accepts_parser_injection() -> None:
    parser = DuckParser()
    provider = DuckKnowledgeProvider(
        parser=parser
    )

    assert provider.parser is parser


def test_provider_complete_analysis(
    provider: DuckKnowledgeProvider,
    complete_product: dict[str, object],
) -> None:
    context = FoodKnowledgeContext(
        query="프리미엄 오리가슴살",
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

    assert result.category_id == "duck"
    assert result.category_name == "오리고기"
    assert result.product_name == (
        "국내산 훈제오리 체리밸리 "
        "오리가슴살 500g"
    )

    assert (
        result.attributes["duck_type"]
        == "훈제오리"
    )
    assert result.attributes["breed"] == (
        "체리밸리"
    )
    assert result.attributes["cut"] == (
        "오리가슴살"
    )

    assert result.scores["knowledge"] == 86.6
    assert result.final_score == 83.3
    assert result.confidence > 0.0
    assert result.warnings == []
    assert result.reasons

    assert (
        result.metadata["provider_id"]
        == "duck"
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
    assert result.raw_product == (
        complete_product
    )
    assert (
        result.raw_product
        is not complete_product
    )


def test_provider_cut_only_analysis(
    provider: DuckKnowledgeProvider,
) -> None:
    product = {
        "product_name": "국내산 오리가슴살 1kg",
        "country": "대한민국",
    }

    result = provider.analyze(product)

    assert result.attributes[
        "duck_type"
    ] is None
    assert result.attributes["breed"] is None
    assert result.attributes["cut"] == (
        "오리가슴살"
    )

    assert result.scores["knowledge"] == 90.0
    assert result.final_score == 45.0
    assert result.confidence > 0.0
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
    provider: DuckKnowledgeProvider,
) -> None:
    result = provider.analyze(
        {
            "product_name": "일반 식품 상품",
            "country": "대한민국",
        }
    )

    assert result.attributes[
        "duck_type"
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


def test_provider_preserves_structured_fields(
    provider: DuckKnowledgeProvider,
) -> None:
    result = provider.analyze(
        {
            "product_name": "국내산 오리고기",
            "duck_type": "훈제오리",
            "duck_breed": "Cherry Valley",
            "cut": "오리가슴살",
            "country": "대한민국",
            "weight": "500g",
            "storage_type": "냉장",
            "bone_status": "boneless",
            "skin_status": "skinless",
        }
    )

    assert result.attributes[
        "duck_type"
    ] == "훈제오리"
    assert result.attributes["breed"] == (
        "체리밸리"
    )
    assert result.attributes["cut"] == (
        "오리가슴살"
    )
    assert result.attributes["weight"] == "500g"
    assert (
        result.attributes["storage_type"]
        == "냉장"
    )
    assert (
        result.attributes["bone_status"]
        == "boneless"
    )
    assert (
        result.attributes["skin_status"]
        == "skinless"
    )


def test_provider_does_not_mutate_product(
    provider: DuckKnowledgeProvider,
    complete_product: dict[str, object],
) -> None:
    original = {
        key: (
            list(value)
            if isinstance(value, list)
            else value
        )
        for key, value in complete_product.items()
    }

    provider.analyze(complete_product)

    assert complete_product == original


def test_provider_rejects_invalid_input(
    provider: DuckKnowledgeProvider,
) -> None:
    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        provider.analyze(
            "오리고기"  # type: ignore[arg-type]
        )
