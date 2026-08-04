from __future__ import annotations

from copy import deepcopy

import pytest

from app.services.food.knowledge.base import (
    FoodKnowledgeProvider,
)
from app.services.food.knowledge.coffee import (
    CoffeeKnowledgeProvider,
    CoffeeParser,
)
from app.services.food.knowledge.models import (
    FoodKnowledgeContext,
    FoodKnowledgeResult,
)


def _complete_product() -> dict[str, object]:
    return {
        "product_name": (
            "에티오피아 100% 아라비카 "
            "라이트 로스트 워시드 원두"
        ),
        "bean_type": "100% arabica",
        "origin_country": "Ethiopia",
        "country_code": "ET",
        "roast_level": "light roast",
        "processing_method": "washed process",
        "weight": "200g",
        "grind_type": "whole bean",
        "product_form": "원두",
        "decaf": False,
        "certifications": [
            "Organic",
            "Fair Trade",
        ],
        "flavor_notes": [
            "자스민",
            "레몬",
            "베르가못",
        ],
        "altitude": "1,900m",
        "roast_date": "2026-08-01",
        "quality_score": 80,
        "price_score": 70,
        "trust_score": 90,
    }


def test_provider_contract() -> None:
    provider = CoffeeKnowledgeProvider()

    assert isinstance(
        provider,
        FoodKnowledgeProvider,
    )
    assert provider.category_id == "coffee"
    assert provider.category_name == "커피"
    assert provider.aliases


def test_provider_parser_injection() -> None:
    parser = CoffeeParser()

    provider = CoffeeKnowledgeProvider(
        parser=parser
    )

    assert provider.parser is parser


@pytest.mark.parametrize(
    "category_id",
    [
        "coffee",
        "COFFEE",
        " coffee ",
        "커피",
        "원두",
        "아라비카",
        "arabica",
    ],
)
def test_provider_supports_category_id(
    category_id: str,
) -> None:
    assert CoffeeKnowledgeProvider().supports(
        category_id=category_id
    )


@pytest.mark.parametrize(
    "product_name",
    [
        "에티오피아 아라비카 원두",
        "프리미엄 커피 200g",
        "100% Arabica Coffee",
        "콜드브루 커피",
        "디카페인 커피 원두",
    ],
)
def test_provider_supports_product_name(
    product_name: str,
) -> None:
    assert CoffeeKnowledgeProvider().supports(
        product_name=product_name
    )


@pytest.mark.parametrize(
    "product_name",
    [
        "국내산 한우 등심",
        "프랑스 브리 치즈",
        "훈제오리 슬라이스",
        "토종닭 가슴살",
        "",
    ],
)
def test_provider_rejects_other_products(
    product_name: str,
) -> None:
    assert not CoffeeKnowledgeProvider().supports(
        product_name=product_name
    )


def test_provider_returns_result() -> None:
    result = CoffeeKnowledgeProvider().analyze(
        _complete_product()
    )

    assert isinstance(
        result,
        FoodKnowledgeResult,
    )

    assert result.category_id == "coffee"
    assert result.category_name == "커피"

    assert result.attributes["bean"] == (
        "아라비카"
    )
    assert result.attributes["origin"] == (
        "에티오피아"
    )
    assert result.attributes["roast"] == (
        "라이트 로스트"
    )
    assert result.attributes["process"] == (
        "워시드"
    )

    assert result.scores["knowledge"] == (
        92.55
    )
    assert result.final_score == 86.28
    assert result.confidence > 0.0
    assert result.reasons
    assert result.warnings == []


def test_provider_orchestration_metadata() -> None:
    result = CoffeeKnowledgeProvider().analyze(
        _complete_product()
    )

    assert result.metadata[
        "provider_id"
    ] == "coffee"

    assert result.metadata[
        "provider"
    ] == "CoffeeKnowledgeProvider"

    assert result.metadata[
        "parser"
    ] == "CoffeeParser"

    assert result.metadata[
        "matched_field_count"
    ] == 4

    assert result.metadata[
        "expected_field_count"
    ] == 4

    assert result.metadata[
        "is_complete"
    ] is True

    assert result.metadata[
        "is_usable"
    ] is True


def test_provider_context_metadata() -> None:
    context = FoodKnowledgeContext(
        query="에티오피아 원두 추천",
        priority="quality",
        user_mode="expert",
        season="summer",
        region="KR",
    )

    result = CoffeeKnowledgeProvider().analyze(
        _complete_product(),
        context=context,
    )

    assert result.metadata["query"] == (
        "에티오피아 원두 추천"
    )
    assert result.metadata["priority"] == (
        "quality"
    )
    assert result.metadata["user_mode"] == (
        "expert"
    )
    assert result.metadata["season"] == (
        "summer"
    )
    assert result.metadata["region"] == "KR"


def test_provider_partial_product() -> None:
    result = CoffeeKnowledgeProvider().analyze(
        {
            "product_name": (
                "에티오피아 워시드 커피"
            ),
        }
    )

    assert result.attributes["bean"] is None
    assert result.attributes["origin"] == (
        "에티오피아"
    )
    assert result.attributes["process"] == (
        "워시드"
    )
    assert result.metadata[
        "matched_field_count"
    ] == 2
    assert result.metadata[
        "is_complete"
    ] is False
    assert result.metadata[
        "is_usable"
    ] is True
    assert result.warnings


def test_provider_unknown_product() -> None:
    result = CoffeeKnowledgeProvider().analyze(
        {
            "product_name": "일반 식품 상품",
        }
    )

    assert result.attributes["bean"] is None
    assert result.scores["knowledge"] == 0.0
    assert result.final_score == 0.0
    assert result.metadata["is_usable"] is False
    assert result.reasons == []
    assert result.warnings


def test_provider_uses_title_as_product_name() -> None:
    result = CoffeeKnowledgeProvider().analyze(
        {
            "title": "에티오피아 아라비카 원두",
        }
    )

    assert result.product_name == (
        "에티오피아 아라비카 원두"
    )
    assert result.attributes["bean"] == (
        "아라비카"
    )


def test_provider_preserves_raw_product_copy() -> None:
    product = _complete_product()

    result = CoffeeKnowledgeProvider().analyze(
        product
    )

    assert result.raw_product == product
    assert result.raw_product is not product


def test_provider_does_not_mutate_product() -> None:
    product = _complete_product()
    product_before = deepcopy(product)

    CoffeeKnowledgeProvider().analyze(
        product
    )

    assert product == product_before


def test_provider_result_is_serializable() -> None:
    result = CoffeeKnowledgeProvider().analyze(
        _complete_product()
    )

    payload = result.to_dict()

    assert payload["category_id"] == "coffee"
    assert payload["category_name"] == "커피"
    assert payload["attributes"]["bean"] == (
        "아라비카"
    )
    assert payload["scores"]["knowledge"] == (
        92.55
    )
    assert payload["final_score"] == 86.28


def test_provider_is_deterministic() -> None:
    provider = CoffeeKnowledgeProvider()
    product = _complete_product()

    first = provider.analyze(product)
    second = provider.analyze(product)

    assert first.to_dict() == second.to_dict()
    assert first is not second

    assert first.attributes is not second.attributes
    assert first.scores is not second.scores
    assert first.reasons is not second.reasons
    assert first.warnings is not second.warnings


def test_provider_rejects_non_mapping() -> None:
    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        CoffeeKnowledgeProvider().analyze(
            "아라비카 원두"  # type: ignore[arg-type]
        )


def test_provider_rejects_empty_mapping() -> None:
    with pytest.raises(
        ValueError,
        match="product must not be empty",
    ):
        CoffeeKnowledgeProvider().analyze({})


def test_provider_rejects_mapping_without_usable_text() -> None:
    with pytest.raises(
        ValueError,
        match="usable text field",
    ):
        CoffeeKnowledgeProvider().analyze(
            {
                "price": 10000,
                "review_count": 10,
            }
        )
