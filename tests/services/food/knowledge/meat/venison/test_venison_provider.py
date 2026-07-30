from __future__ import annotations

from collections.abc import Mapping

import pytest

from app.services.food.knowledge import (
    FoodKnowledgeResult,
)
from app.services.food.knowledge.meat.venison import (
    VenisonKnowledgeProvider,
)


@pytest.fixture
def complete_product() -> dict[str, object]:
    return {
        "product_name": (
            "뉴질랜드산 어린사슴 "
            "레드디어 사슴가슴살 500g"
        ),
        "venison_type": "어린 사슴",
        "deer_species": "Red Deer",
        "cut": "venison breast",
        "country": "뉴질랜드",
        "country_code": "NZ",
        "weight": "500g",
        "storage_type": "냉동",
        "certifications": ["HACCP"],
        "quality_score": 80,
        "price_score": 70,
        "trust_score": 90,
    }


def test_provider_identity() -> None:
    provider = VenisonKnowledgeProvider()

    assert provider.category_id == "venison"
    assert provider.parent_category_id == "meat"
    assert provider.provider_id == "venison"


def test_provider_analyzes_complete_product(
    complete_product: dict[str, object],
) -> None:
    provider = VenisonKnowledgeProvider()

    result = provider.analyze(
        complete_product
    )

    assert isinstance(
        result,
        FoodKnowledgeResult,
    )

    assert result.category_id == "venison"

    assert result.attributes[
        "venison_type"
    ] == "어린사슴"

    assert result.attributes[
        "breed"
    ] == "레드디어"

    assert result.attributes[
        "cut"
    ] == "사슴가슴살"

    assert result.attributes[
        "cut_registry_key"
    ] == "breast"

    assert result.scores[
        "venison_type"
    ] == 92.0

    assert result.scores["breed"] == 90.0
    assert result.scores["cut"] == 83.0
    assert result.scores["knowledge"] == 87.1
    assert result.final_score == 83.55

    assert result.reasons
    assert result.warnings == []

    assert result.metadata[
        "provider_id"
    ] == "venison"


def test_provider_preserves_breast_contract() -> None:
    provider = VenisonKnowledgeProvider()

    result = provider.analyze(
        {
            "product_name": "사슴가슴살",
            "cut": "deer breast",
            "country": "뉴질랜드",
        }
    )

    assert result.attributes[
        "cut"
    ] == "사슴가슴살"

    assert result.attributes[
        "cut_registry_key"
    ] == "breast"

    assert result.attributes[
        "cut_score"
    ] == 83.0

    assert result.scores["cut"] == 83.0
    assert result.scores["knowledge"] == 83.0

    assert any(
        "사슴가슴살 부위 상품입니다."
        == reason
        for reason in result.reasons
    )


def test_provider_supports_cut_only_product() -> None:
    provider = VenisonKnowledgeProvider()

    result = provider.analyze(
        {
            "product_name": "사슴 안심 1kg",
            "cut": "venison tenderloin",
            "country": "뉴질랜드",
        }
    )

    assert result.attributes[
        "venison_type"
    ] is None

    assert result.attributes[
        "breed"
    ] is None

    assert result.attributes[
        "cut"
    ] == "사슴안심"

    assert result.attributes[
        "cut_registry_key"
    ] == "tenderloin"

    assert result.scores["cut"] == 96.0
    assert result.scores["knowledge"] == 96.0


def test_provider_returns_mapping_fields(
    complete_product: dict[str, object],
) -> None:
    result = VenisonKnowledgeProvider().analyze(
        complete_product
    )

    assert isinstance(
        result.attributes,
        Mapping,
    )

    assert isinstance(
        result.scores,
        Mapping,
    )

    assert isinstance(result.reasons, list)
    assert isinstance(result.warnings, list)
    assert isinstance(result.metadata, Mapping)


def test_provider_rejects_non_mapping() -> None:
    provider = VenisonKnowledgeProvider()

    with pytest.raises(TypeError):
        provider.analyze(
            "사슴가슴살"  # type: ignore[arg-type]
        )


def test_provider_rejects_empty_product() -> None:
    provider = VenisonKnowledgeProvider()

    with pytest.raises(ValueError):
        provider.analyze({})


def test_provider_creates_independent_results(
    complete_product: dict[str, object],
) -> None:
    provider = VenisonKnowledgeProvider()

    first = provider.analyze(
        complete_product
    )

    second = provider.analyze(
        complete_product
    )

    assert first is not second
    assert first.attributes is not second.attributes
    assert first.scores is not second.scores
    assert first.reasons is not second.reasons
    assert first.warnings is not second.warnings


def test_provider_complete_result_metadata(
    complete_product: dict[str, object],
) -> None:
    result = VenisonKnowledgeProvider().analyze(
        complete_product
    )

    assert result.metadata[
        "provider_id"
    ] == "venison"

    assert result.metadata[
        "category_id"
    ] == "venison"

    assert result.metadata[
        "parent_category_id"
    ] == "meat"
