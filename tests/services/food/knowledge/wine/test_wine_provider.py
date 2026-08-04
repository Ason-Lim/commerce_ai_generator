from __future__ import annotations

import pytest

from app.services.food.knowledge.base import (
    FoodKnowledgeProvider,
)
from app.services.food.knowledge.models import (
    FoodKnowledgeContext,
    FoodKnowledgeResult,
)
from app.services.food.knowledge.wine.parser import (
    WineParser,
)
from app.services.food.knowledge.wine.provider import (
    WineKnowledgeProvider,
)


def test_wine_provider_contract() -> None:
    provider = WineKnowledgeProvider()

    assert isinstance(
        provider,
        FoodKnowledgeProvider,
    )
    assert provider.category_id == "wine"
    assert provider.category_name == "와인"
    assert provider.aliases
    assert isinstance(
        provider.parser,
        WineParser,
    )


@pytest.mark.parametrize(
    "category_id",
    [
        "wine",
        "WINE",
        " wine ",
        "와인",
        "보르도",
        "chardonnay",
    ],
)
def test_wine_provider_supports_category_id(
    category_id: str,
) -> None:
    provider = WineKnowledgeProvider()

    assert provider.supports(
        category_id=category_id
    ) is True


@pytest.mark.parametrize(
    "product_name",
    [
        "2020 보르도 레드 와인",
        "부르고뉴 샤르도네 화이트와인",
        "Napa Valley Cabernet Sauvignon Wine",
        "리슬링 스파클링 와인",
    ],
)
def test_wine_provider_supports_product_name(
    product_name: str,
) -> None:
    provider = WineKnowledgeProvider()

    assert provider.supports(
        product_name=product_name
    ) is True


@pytest.mark.parametrize(
    "product_name",
    [
        "국산 사과 5kg",
        "한우 등심 1++",
        "모차렐라 치즈 200g",
        "",
    ],
)
def test_wine_provider_rejects_unrelated_product(
    product_name: str,
) -> None:
    provider = WineKnowledgeProvider()

    assert provider.supports(
        product_name=product_name
    ) is False


def test_wine_provider_rejects_empty_inputs() -> None:
    provider = WineKnowledgeProvider()

    assert provider.supports() is False


def test_wine_provider_analyze_full_pipeline() -> None:
    provider = WineKnowledgeProvider()

    product = {
        "product_name": (
            "2020 보르도 카베르네 소비뇽 "
            "레드 와인 드라이 풀 바디 "
            "높은 산도 13.5%"
        ),
        "producer": "Example Winery",
        "country": "France",
        "volume": "750ml",
        "closure_type": "cork",
        "certifications": ["AOC"],
        "price_score": 75,
    }

    result = provider.analyze(product)

    assert isinstance(
        result,
        FoodKnowledgeResult,
    )
    assert result.category_id == "wine"
    assert result.category_name == "와인"
    assert (
        result.product_name
        == product["product_name"]
    )

    assert result.attributes["wine_type"] == "red"
    assert (
        result.attributes["grape"]
        == "cabernet_sauvignon"
    )
    assert result.attributes["region"] == "bordeaux"
    assert result.attributes["vintage"] == 2020
    assert (
        result.attributes["alcohol_percent"]
        == 13.5
    )

    assert result.scores["price"] == 75.0
    assert result.scores["knowledge"] == 88.5
    assert result.final_score is not None
    assert 0.0 <= result.final_score <= 100.0
    assert result.confidence > 0.0
    assert result.reasons
    assert result.warnings == []
    assert result.raw_product == product


def test_wine_provider_metadata() -> None:
    provider = WineKnowledgeProvider()

    result = provider.analyze(
        {
            "product_name": (
                "2020 보르도 카베르네 소비뇽 "
                "레드 와인 드라이 풀 바디 "
                "높은 산도 13.5%"
            ),
            "producer": "Example Winery",
            "volume": "750ml",
        }
    )

    assert (
        result.metadata["provider_id"]
        == "wine"
    )
    assert (
        result.metadata["provider"]
        == "WineKnowledgeProvider"
    )
    assert (
        result.metadata["parser"]
        == "WineParser"
    )
    assert (
        result.metadata["matched_field_count"]
        == 6
    )
    assert (
        result.metadata["expected_field_count"]
        == 6
    )
    assert result.metadata["is_complete"] is True
    assert result.metadata["is_usable"] is True


def test_wine_provider_context_metadata() -> None:
    provider = WineKnowledgeProvider()

    context = FoodKnowledgeContext(
        query="보르도 와인 추천",
        priority="quality",
        user_mode="expert",
        season="winter",
        region="Seoul",
    )

    result = provider.analyze(
        {
            "product_name": (
                "보르도 카베르네 소비뇽 "
                "레드 와인"
            ),
        },
        context=context,
    )

    assert result.metadata["query"] == (
        "보르도 와인 추천"
    )
    assert result.metadata["priority"] == "quality"
    assert result.metadata["user_mode"] == "expert"
    assert result.metadata["season"] == "winter"
    assert result.metadata["region"] == "Seoul"


def test_wine_provider_unknown_product() -> None:
    provider = WineKnowledgeProvider()

    result = provider.analyze(
        {
            "product_name": (
                "등록되지 않은 임의의 상품"
            ),
        }
    )

    assert result.category_id == "wine"
    assert result.confidence == 0.0
    assert result.final_score == 0.0
    assert result.attributes["is_usable"] is False
    assert result.warnings


def test_wine_provider_rejects_non_mapping() -> None:
    provider = WineKnowledgeProvider()

    with pytest.raises(TypeError):
        provider.analyze(  # type: ignore[arg-type]
            "invalid"
        )


def test_wine_provider_rejects_empty_mapping() -> None:
    provider = WineKnowledgeProvider()

    with pytest.raises(ValueError):
        provider.analyze({})


def test_wine_provider_is_deterministic() -> None:
    provider = WineKnowledgeProvider()

    product = {
        "product_name": (
            "2020 보르도 카베르네 소비뇽 "
            "레드 와인 드라이 13.5%"
        ),
        "price_score": 70,
    }

    first = provider.analyze(product)
    second = provider.analyze(product)

    assert first.to_dict() == second.to_dict()


def test_wine_provider_supports_parser_injection() -> None:
    parser = WineParser()
    provider = WineKnowledgeProvider(
        parser=parser
    )

    assert provider.parser is parser
