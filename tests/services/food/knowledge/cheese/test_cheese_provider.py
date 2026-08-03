from __future__ import annotations

from copy import deepcopy

import pytest

from app.services.food.knowledge.base import (
    FoodKnowledgeProvider,
)
from app.services.food.knowledge.cheese import (
    CheeseKnowledgeProvider,
    CheeseParser,
)
from app.services.food.knowledge.models import (
    FoodKnowledgeContext,
    FoodKnowledgeResult,
)


def _complete_product() -> dict[str, object]:
    return {
        "product_name": (
            "프랑스 산양유 브리 "
            "소프트 치즈 12개월 숙성"
        ),
        "cheese_type": "brie",
        "milk_source": "goat milk",
        "country": "프랑스",
        "country_code": "FR",
        "texture": "soft cheese",
        "aging": "12개월 숙성",
        "weight": "200g",
        "storage_type": "냉장",
        "packaging_type": "wheel",
        "pasteurized": True,
        "certifications": [
            "AOP",
            "유기농",
        ],
        "fat_content": "45%",
        "rind_type": "bloomy rind",
        "quality_score": 80,
        "price_score": 70,
        "trust_score": 90,
    }


def test_provider_contract() -> None:
    provider = CheeseKnowledgeProvider()

    assert isinstance(
        provider,
        FoodKnowledgeProvider,
    )
    assert provider.category_id == "cheese"
    assert provider.category_name == "치즈"
    assert provider.aliases


def test_provider_parser_injection() -> None:
    parser = CheeseParser()

    provider = CheeseKnowledgeProvider(
        parser=parser
    )

    assert provider.parser is parser


@pytest.mark.parametrize(
    "category_id",
    [
        "cheese",
        "CHEESE",
        " cheese ",
        "치즈",
        "모차렐라",
        "parmesan",
    ],
)
def test_provider_supports_category_id(
    category_id: str,
) -> None:
    provider = CheeseKnowledgeProvider()

    assert provider.supports(
        category_id=category_id
    )


@pytest.mark.parametrize(
    "product_name",
    [
        "프랑스 브리 치즈 200g",
        "이탈리아 모짜렐라",
        "숙성 체다치즈",
        "파르미자노 레지아노",
        "blue cheese 150g",
        "plain cream cheese",
    ],
)
def test_provider_supports_product_name(
    product_name: str,
) -> None:
    provider = CheeseKnowledgeProvider()

    assert provider.supports(
        product_name=product_name
    )


@pytest.mark.parametrize(
    "product_name",
    [
        "국내산 한우 등심",
        "양고기 프렌치랙",
        "훈제오리 슬라이스",
        "닭가슴살 1kg",
        "사슴 안심 스테이크",
        "보어 염소 갈비",
        "",
    ],
)
def test_provider_rejects_non_cheese_product_name(
    product_name: str,
) -> None:
    provider = CheeseKnowledgeProvider()

    assert (
        provider.supports(
            product_name=product_name
        )
        is False
    )


def test_provider_supports_returns_false_without_input() -> None:
    provider = CheeseKnowledgeProvider()

    assert provider.supports() is False


def test_provider_analyzes_complete_product() -> None:
    provider = CheeseKnowledgeProvider()

    result = provider.analyze(
        _complete_product()
    )

    assert isinstance(
        result,
        FoodKnowledgeResult,
    )

    assert result.category_id == "cheese"
    assert result.category_name == "치즈"
    assert result.product_name == (
        "프랑스 산양유 브리 "
        "소프트 치즈 12개월 숙성"
    )

    assert result.attributes["cheese_type"] == (
        "브리"
    )
    assert result.attributes["milk_source"] == (
        "산양유"
    )
    assert result.attributes["origin"] == (
        "프랑스"
    )
    assert result.attributes["texture"] == (
        "연성"
    )
    assert result.attributes["aging"] == (
        "장기숙성"
    )

    assert result.scores["quality"] == 80.0
    assert result.scores["price"] == 70.0
    assert result.scores["trust"] == 90.0
    assert result.scores["knowledge"] == 92.6

    assert result.final_score == 86.3
    assert 0.0 <= result.confidence <= 1.0
    assert result.reasons
    assert result.warnings == []


def test_provider_result_metadata() -> None:
    provider = CheeseKnowledgeProvider()

    context = FoodKnowledgeContext(
        query="프랑스 브리 치즈",
        priority="quality",
        user_mode="expert",
        season="summer",
        region="seoul",
        metadata={
            "request_id": "test-request",
        },
    )

    result = provider.analyze(
        _complete_product(),
        context=context,
    )

    assert result.metadata == {
        "provider_id": "cheese",
        "provider": (
            "CheeseKnowledgeProvider"
        ),
        "parser": "CheeseParser",
        "priority": "quality",
        "query": "프랑스 브리 치즈",
        "user_mode": "expert",
        "season": "summer",
        "region": "seoul",
        "matched_field_count": 5,
        "expected_field_count": 5,
        "is_complete": True,
        "is_usable": True,
    }


def test_provider_analyzes_partial_product() -> None:
    provider = CheeseKnowledgeProvider()

    result = provider.analyze(
        {
            "product_name": (
                "24개월 숙성 "
                "파르미자노 레지아노"
            ),
            "quality_score": 80,
            "price_score": 70,
            "trust_score": 90,
        }
    )

    assert result.attributes["cheese_type"] == (
        "파르미자노 레지아노"
    )
    assert result.attributes["aging"] == (
        "초장기숙성"
    )

    assert result.scores["knowledge"] == 96.4
    assert result.final_score == 88.2

    assert result.metadata[
        "matched_field_count"
    ] == 2
    assert result.metadata["is_complete"] is False
    assert result.metadata["is_usable"] is True

    assert result.reasons
    assert result.warnings


def test_provider_analyzes_unknown_product() -> None:
    provider = CheeseKnowledgeProvider()

    result = provider.analyze(
        {
            "product_name": "일반 식품 상품",
        }
    )

    assert result.attributes["cheese_type"] is None
    assert result.attributes["is_usable"] is False

    assert result.scores["knowledge"] == 0.0
    assert result.final_score == 0.0
    assert result.confidence == 0.0

    assert result.metadata[
        "matched_field_count"
    ] == 0
    assert result.metadata["is_complete"] is False
    assert result.metadata["is_usable"] is False

    assert result.reasons == []
    assert result.warnings


def test_provider_uses_title_as_product_name() -> None:
    provider = CheeseKnowledgeProvider()

    result = provider.analyze(
        {
            "title": "프랑스 브리 치즈",
        }
    )

    assert result.product_name == (
        "프랑스 브리 치즈"
    )
    assert result.attributes["cheese_type"] == (
        "브리"
    )


def test_provider_preserves_raw_product_copy() -> None:
    provider = CheeseKnowledgeProvider()
    product = _complete_product()

    result = provider.analyze(product)

    assert result.raw_product == product
    assert result.raw_product is not product


def test_provider_does_not_mutate_product() -> None:
    provider = CheeseKnowledgeProvider()
    product = _complete_product()
    product_before = deepcopy(product)

    provider.analyze(product)

    assert product == product_before


def test_provider_result_is_serializable() -> None:
    provider = CheeseKnowledgeProvider()

    result = provider.analyze(
        _complete_product()
    )

    payload = result.to_dict()

    assert payload["category_id"] == "cheese"
    assert payload["category_name"] == "치즈"
    assert payload["attributes"]["cheese_type"] == (
        "브리"
    )
    assert payload["scores"]["knowledge"] == 92.6
    assert payload["final_score"] == 86.3


def test_provider_is_deterministic() -> None:
    provider = CheeseKnowledgeProvider()
    product = _complete_product()

    first = provider.analyze(product)
    second = provider.analyze(product)

    assert first.to_dict() == second.to_dict()
    assert first is not second


def test_provider_rejects_non_mapping() -> None:
    provider = CheeseKnowledgeProvider()

    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        provider.analyze(
            "브리 치즈"  # type: ignore[arg-type]
        )


def test_provider_rejects_empty_mapping() -> None:
    provider = CheeseKnowledgeProvider()

    with pytest.raises(
        ValueError,
        match="product must not be empty",
    ):
        provider.analyze({})


def test_provider_rejects_mapping_without_usable_text() -> None:
    provider = CheeseKnowledgeProvider()

    with pytest.raises(
        ValueError,
        match="usable text field",
    ):
        provider.analyze(
            {
                "price": 10000,
                "review_count": 10,
            }
        )
