from __future__ import annotations

import pytest

from app.services.food.knowledge.meat.chicken.parser import (
    ChickenParser,
)
from app.services.food.knowledge.meat.chicken.provider import (
    ChickenKnowledgeProvider,
)
from app.services.food.knowledge.models import (
    FoodKnowledgeContext,
    FoodKnowledgeResult,
)


@pytest.fixture
def provider() -> ChickenKnowledgeProvider:
    return ChickenKnowledgeProvider()


@pytest.fixture
def complete_product() -> dict[str, object]:
    return {
        "product_name": (
            "국내산 토종닭 Ross 308 "
            "닭다리살 500g"
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
    provider: ChickenKnowledgeProvider,
) -> None:
    assert provider.category_id == "chicken"
    assert provider.category_name == "닭고기"
    assert isinstance(
        provider.parser,
        ChickenParser,
    )


def test_provider_supports_category_id(
    provider: ChickenKnowledgeProvider,
) -> None:
    assert provider.supports(
        category_id="chicken"
    )
    assert provider.supports(
        category_id="CHICKEN"
    )
    assert provider.supports(
        category_id="닭고기"
    )
    assert not provider.supports(
        category_id="lamb"
    )


def test_provider_supports_product_name(
    provider: ChickenKnowledgeProvider,
) -> None:
    assert provider.supports(
        product_name="국내산 닭가슴살 1kg"
    )
    assert provider.supports(
        product_name="토종닭 백숙용"
    )
    assert provider.supports(
        product_name="Chicken Breast 500g"
    )
    assert not provider.supports(
        product_name="한우 등심 500g"
    )


def test_provider_accepts_parser_injection() -> None:
    parser = ChickenParser()
    provider = ChickenKnowledgeProvider(
        parser=parser
    )

    assert provider.parser is parser


def test_provider_complete_analysis(
    provider: ChickenKnowledgeProvider,
    complete_product: dict[str, object],
) -> None:
    context = FoodKnowledgeContext(
        query="프리미엄 닭다리살",
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

    assert result.category_id == "chicken"
    assert result.category_name == "닭고기"
    assert result.product_name == (
        "국내산 토종닭 Ross 308 "
        "닭다리살 500g"
    )

    assert (
        result.attributes["chicken_type"]
        == "토종닭"
    )
    assert result.attributes["breed"] == (
        "로스 308"
    )
    assert result.attributes["cut"] == (
        "닭다리살"
    )

    assert result.scores["knowledge"] == 86.8
    assert result.final_score == 83.4
    assert result.confidence > 0.0
    assert result.warnings == []
    assert result.reasons

    assert (
        result.metadata["provider_id"]
        == "chicken"
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
    provider: ChickenKnowledgeProvider,
) -> None:
    product = {
        "product_name": "국내산 닭가슴살 1kg",
        "country": "대한민국",
    }

    result = provider.analyze(product)

    assert result.attributes[
        "chicken_type"
    ] is None
    assert result.attributes["breed"] is None
    assert result.attributes["cut"] == (
        "닭가슴살"
    )

    assert result.scores["knowledge"] == 82.0
    assert result.final_score == 41.0
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
    provider: ChickenKnowledgeProvider,
) -> None:
    result = provider.analyze(
        {
            "product_name": "일반 식품 상품",
            "country": "대한민국",
        }
    )

    assert result.attributes[
        "chicken_type"
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
    provider: ChickenKnowledgeProvider,
) -> None:
    result = provider.analyze(
        {
            "product_name": "국내산 닭고기",
            "chicken_type": "영계",
            "chicken_breed": "Cobb 500",
            "cut": "닭안심",
            "country": "대한민국",
            "weight": "500g",
            "storage_type": "냉장",
            "bone_status": "boneless",
            "skin_status": "skinless",
        }
    )

    assert result.attributes[
        "chicken_type"
    ] == "영계"
    assert result.attributes["breed"] == (
        "코브 500"
    )
    assert result.attributes["cut"] == "닭안심"
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
    provider: ChickenKnowledgeProvider,
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
    provider: ChickenKnowledgeProvider,
) -> None:
    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        provider.analyze(
            "닭고기"  # type: ignore[arg-type]
        )
