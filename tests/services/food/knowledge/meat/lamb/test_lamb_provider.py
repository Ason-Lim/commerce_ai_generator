from __future__ import annotations

import pytest

from app.services.food.knowledge.meat.lamb import (
    LambKnowledgeProvider,
    LambParser,
    apply_lamb_rules,
    build_lamb_attributes,
    calculate_lamb_final_score,
    calculate_lamb_scores,
)
from app.services.food.knowledge.models import (
    FoodKnowledgeContext,
    FoodKnowledgeResult,
)
from app.services.food.knowledge.registry import (
    get_food_provider,
    resolve_food_provider,
)


@pytest.fixture
def provider() -> LambKnowledgeProvider:
    return LambKnowledgeProvider()


@pytest.fixture
def complete_product() -> dict[str, object]:
    return {
        "product_name": (
            "호주산 도퍼 어린양 프렌치랙 500g"
        ),
        "country": "호주",
        "country_code": "AU",
        "weight": "500g",
        "storage_type": "냉동",
        "certifications": [
            "할랄",
        ],
        "quality_score": 80,
        "price_score": 70,
        "trust_score": 90,
    }


def test_lamb_provider_is_registered() -> None:
    provider = get_food_provider(
        "lamb"
    )

    assert provider is not None
    assert provider.category_id == "lamb"
    assert provider.category_name == "양고기"


def test_lamb_provider_resolves_by_product_name() -> None:
    provider = resolve_food_provider(
        product_name=(
            "호주산 프렌치랙 어린양"
        )
    )

    assert provider is not None
    assert provider.category_id == "lamb"


@pytest.mark.parametrize(
    (
        "category_id",
        "product_name",
        "expected",
    ),
    [
        (
            "lamb",
            None,
            True,
        ),
        (
            "양고기",
            None,
            True,
        ),
        (
            None,
            "뉴질랜드 어린양 램랙",
            True,
        ),
        (
            None,
            "도퍼 프렌치랙",
            True,
        ),
        (
            "beef",
            None,
            False,
        ),
        (
            None,
            "국내산 한우 등심",
            False,
        ),
    ],
)
def test_lamb_provider_supports(
    provider: LambKnowledgeProvider,
    category_id: str | None,
    product_name: str | None,
    expected: bool,
) -> None:
    assert (
        provider.supports(
            category_id=category_id,
            product_name=product_name,
        )
        is expected
    )


def test_lamb_parser_complete_product(
    complete_product: dict[str, object],
) -> None:
    result = LambParser().parse_product(
        complete_product
    )

    assert result.age == "램"
    assert result.breed == "도퍼"
    assert result.cut == "램랙"
    assert result.confidence > 0.0
    assert result.is_complete is True

    assert (
        result.metadata[
            "matched_field_count"
        ]
        == 3
    )


def test_lamb_scoring_complete_product(
    complete_product: dict[str, object],
) -> None:
    parse_result = (
        LambParser().parse_product(
            complete_product
        )
    )

    scores = calculate_lamb_scores(
        product=complete_product,
        parse_result=parse_result,
    )

    assert scores == {
        "quality": 80.0,
        "price": 70.0,
        "trust": 90.0,
        "age": 90.0,
        "breed": 88.0,
        "cut": 95.0,
        "tenderness": 90.0,
        "flavor": 86.0,
        "knowledge": 91.5,
    }

    assert (
        calculate_lamb_final_score(
            scores
        )
        == 85.75
    )


def test_lamb_rules_complete_product(
    complete_product: dict[str, object],
) -> None:
    parse_result = (
        LambParser().parse_product(
            complete_product
        )
    )

    attributes = build_lamb_attributes(
        product=complete_product,
        parse_result=parse_result,
    )

    scores = calculate_lamb_scores(
        product=complete_product,
        parse_result=parse_result,
    )

    reasons, warnings = apply_lamb_rules(
        attributes=attributes,
        scores=scores,
        parse_result=parse_result,
    )

    assert reasons
    assert warnings == []

    assert any(
        "연령 분류는 램" in reason
        for reason in reasons
    )
    assert any(
        "품종은 도퍼" in reason
        for reason in reasons
    )
    assert any(
        "램랙 부위" in reason
        for reason in reasons
    )


def test_lamb_provider_complete_analysis(
    provider: LambKnowledgeProvider,
    complete_product: dict[str, object],
) -> None:
    context = FoodKnowledgeContext(
        query="프리미엄 양갈비",
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

    assert result.category_id == "lamb"
    assert result.category_name == "양고기"

    assert result.attributes["age"] == "램"
    assert result.attributes["breed"] == "도퍼"
    assert result.attributes["cut"] == "램랙"

    assert result.scores["knowledge"] == 91.5
    assert result.final_score == 85.75
    assert result.warnings == []

    assert (
        result.metadata["provider_id"]
        == "lamb"
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


def test_lamb_provider_incomplete_analysis(
    provider: LambKnowledgeProvider,
) -> None:
    product = {
        "product_name": (
            "수입산 양고기 냉동 1kg"
        ),
    }

    result = provider.analyze(
        product
    )

    assert result.attributes["age"] is None
    assert result.attributes["breed"] is None
    assert result.attributes["cut"] is None

    assert result.scores["knowledge"] == 0.0
    assert result.final_score == 0.0
    assert result.confidence == 0.0

    assert result.reasons == []
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


def test_lamb_provider_rejects_invalid_input(
    provider: LambKnowledgeProvider,
) -> None:
    with pytest.raises(
        TypeError,
        match=(
            "product must be a Mapping"
        ),
    ):
        provider.analyze(
            "양고기"  # type: ignore[arg-type]
        )
