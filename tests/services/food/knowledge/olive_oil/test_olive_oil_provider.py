from __future__ import annotations

from copy import deepcopy

import pytest

from app.services.food.knowledge.models import (
    FoodKnowledgeContext,
    FoodKnowledgeResult,
)
from app.services.food.knowledge.olive_oil.parser import (
    OliveOilParser,
)
from app.services.food.knowledge.olive_oil.provider import (
    OliveOilKnowledgeProvider,
)


def _complete_product() -> dict[str, object]:
    return {
        "product_name": (
            "스페인산 아르베키나 단일 품종 "
            "냉압착 엑스트라 버진 올리브오일"
        ),
        "olive_oil_type": "single varietal",
        "cultivar": "Arbequina",
        "origin_country": "Spain",
        "country": "Spain",
        "country_code": "ES",
        "extraction_method": "cold pressed",
        "grade": "extra virgin olive oil",
        "volume": "500ml",
        "packaging_type": "dark glass bottle",
        "organic": True,
        "certifications": [
            "Organic",
            "PDO",
        ],
        "quality_score": 80,
        "price_score": 70,
        "trust_score": 90,
    }


def test_provider_identity() -> None:
    provider = OliveOilKnowledgeProvider()

    assert provider.category_id == "olive_oil"
    assert provider.category_name == "올리브오일"
    assert isinstance(provider.parser, OliveOilParser)


def test_provider_parser_injection() -> None:
    parser = OliveOilParser()

    provider = OliveOilKnowledgeProvider(
        parser=parser
    )

    assert provider.parser is parser


@pytest.mark.parametrize(
    "category_id",
    [
        "olive_oil",
        "OLIVE_OIL",
        "olive oil",
        "올리브오일",
        "올리브유",
    ],
)
def test_supports_category_aliases(
    category_id: str,
) -> None:
    assert OliveOilKnowledgeProvider().supports(
        category_id=category_id
    )


@pytest.mark.parametrize(
    "product_name",
    [
        "스페인산 엑스트라 버진 올리브오일",
        "냉압착 올리브오일 500ml",
        "Organic EVOO",
        "Extra Virgin Olive Oil",
        "버진 올리브유",
        "포마스 올리브유",
    ],
)
def test_supports_product_name_aliases(
    product_name: str,
) -> None:
    assert OliveOilKnowledgeProvider().supports(
        product_name=product_name
    )


@pytest.mark.parametrize(
    "product_name",
    [
        "프랑스 브리 치즈",
        "에티오피아 아라비카 원두",
        "제주 녹차",
        "카베르네 소비뇽 레드 와인",
        "국내산 한우 등심",
        "",
    ],
)
def test_rejects_non_olive_oil_products(
    product_name: str,
) -> None:
    assert not OliveOilKnowledgeProvider().supports(
        product_name=product_name
    )


def test_analyze_returns_food_knowledge_result() -> None:
    result = OliveOilKnowledgeProvider().analyze(
        _complete_product()
    )

    assert isinstance(
        result,
        FoodKnowledgeResult,
    )

    assert result.category_id == "olive_oil"
    assert result.category_name == "올리브오일"
    assert result.product_name == (
        _complete_product()["product_name"]
    )


def test_analyze_complete_product_contract() -> None:
    result = OliveOilKnowledgeProvider().analyze(
        _complete_product()
    )

    assert result.attributes["olive_oil_type"] == (
        "single_varietal"
    )
    assert result.attributes["variety"] == "arbequina"
    assert result.attributes["origin"] == "spain"
    assert result.attributes["processing"] == (
        "cold_pressed"
    )
    assert result.attributes["grade"] == (
        "extra_virgin"
    )

    assert result.scores["quality"] == 80.0
    assert result.scores["price"] == 70.0
    assert result.scores["trust"] == 90.0
    assert result.scores["knowledge"] == 95.0
    assert result.final_score == 87.5

    assert result.reasons
    assert result.warnings == []
    assert result.confidence > 0.0


def test_analyze_metadata_contract() -> None:
    context = FoodKnowledgeContext(
        query="프리미엄 올리브오일",
        priority="quality",
        user_mode="expert",
        season="summer",
        region="KR",
    )

    result = OliveOilKnowledgeProvider().analyze(
        _complete_product(),
        context=context,
    )

    assert result.metadata["provider_id"] == (
        "olive_oil"
    )
    assert result.metadata["provider"] == (
        "OliveOilKnowledgeProvider"
    )
    assert result.metadata["parser"] == (
        "OliveOilParser"
    )
    assert result.metadata["priority"] == "quality"
    assert result.metadata["query"] == (
        "프리미엄 올리브오일"
    )
    assert result.metadata["user_mode"] == "expert"
    assert result.metadata["season"] == "summer"
    assert result.metadata["region"] == "KR"
    assert result.metadata["matched_field_count"] == 5
    assert result.metadata["expected_field_count"] == 5
    assert result.metadata["is_complete"] is True
    assert result.metadata["is_usable"] is True


def test_analyze_partial_product() -> None:
    result = OliveOilKnowledgeProvider().analyze(
        {
            "product_name": (
                "스페인 아르베키나 올리브오일"
            ),
        }
    )

    assert result.category_id == "olive_oil"
    assert result.attributes["variety"] == "arbequina"
    assert result.attributes["origin"] == "spain"
    assert result.metadata["is_complete"] is False
    assert result.metadata["is_usable"] is True
    assert result.warnings


def test_analyze_unknown_product() -> None:
    result = OliveOilKnowledgeProvider().analyze(
        {
            "product_name": "일반 식품 상품",
        }
    )

    assert result.attributes["olive_oil_type"] is None
    assert result.attributes["variety"] is None
    assert result.attributes["origin"] is None
    assert result.attributes["processing"] is None
    assert result.attributes["grade"] is None

    assert result.scores["knowledge"] == 0.0
    assert result.final_score == 0.0
    assert result.metadata["is_usable"] is False
    assert result.warnings


def test_analyze_preserves_raw_product_copy() -> None:
    product = _complete_product()

    result = OliveOilKnowledgeProvider().analyze(
        product
    )

    assert result.raw_product == product
    assert result.raw_product is not product


def test_analyze_does_not_mutate_input() -> None:
    product = _complete_product()
    before = deepcopy(product)

    OliveOilKnowledgeProvider().analyze(
        product
    )

    assert product == before


def test_analyze_is_deterministic() -> None:
    provider = OliveOilKnowledgeProvider()
    product = _complete_product()

    first = provider.analyze(product)
    second = provider.analyze(product)

    assert first.to_dict() == second.to_dict()
    assert first is not second


def test_analyze_rejects_non_mapping() -> None:
    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        OliveOilKnowledgeProvider().analyze(
            "olive oil"  # type: ignore[arg-type]
        )


def test_analyze_rejects_empty_mapping() -> None:
    with pytest.raises(
        ValueError,
        match="product must not be empty",
    ):
        OliveOilKnowledgeProvider().analyze({})
