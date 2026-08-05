from __future__ import annotations

from copy import deepcopy

import pytest

from app.services.food.knowledge.base import (
    FoodKnowledgeProvider,
)
from app.services.food.knowledge.models import (
    FoodKnowledgeContext,
    FoodKnowledgeResult,
)
from app.services.food.knowledge.tea.parser import (
    TeaParser,
)
from app.services.food.knowledge.tea.provider import (
    TeaKnowledgeProvider,
)


def _complete_product() -> dict[str, object]:
    return {
        "product_name": (
            "제주 야부키타 증제 "
            "비산화 감칠맛 녹차"
        ),
        "tea_type": "green tea",
        "origin": "Jeju",
        "country": "South Korea",
        "country_code": "KR",
        "cultivar": "Yabukita",
        "processing_method": "steamed tea",
        "oxidation_level": "unoxidized",
        "flavor_notes": [
            "감칠맛",
            "풀향",
        ],
        "weight": "100g",
        "packaging_type": "loose leaf",
        "harvest_year": 2026,
        "grade": "premium",
        "leaf_style": "whole leaf",
        "caffeine_status": "regular",
        "certifications": [
            "Organic",
            "HACCP",
        ],
        "quality_score": 80,
        "price_score": 70,
        "trust_score": 90,
    }


def test_provider_contract() -> None:
    provider = TeaKnowledgeProvider()

    assert isinstance(
        provider,
        FoodKnowledgeProvider,
    )
    assert provider.category_id == "tea"
    assert provider.category_name == "차"
    assert provider.aliases
    assert isinstance(
        provider.parser,
        TeaParser,
    )


def test_provider_parser_injection() -> None:
    parser = TeaParser()

    provider = TeaKnowledgeProvider(
        parser=parser
    )

    assert provider.parser is parser


@pytest.mark.parametrize(
    "category_id",
    [
        "tea",
        "TEA",
        " tea ",
        "차",
        "티",
        "녹차",
        "black tea",
        "oolong",
        "matcha",
        "darjeeling",
    ],
)
def test_provider_supports_category_id(
    category_id: str,
) -> None:
    assert TeaKnowledgeProvider().supports(
        category_id=category_id
    )


@pytest.mark.parametrize(
    "product_name",
    [
        "제주 녹차 100g",
        "프리미엄 다즐링 홍차",
        "Japanese Sencha Green Tea",
        "Matcha Powder 50g",
        "대만 우롱차",
        "Yunnan Pu-erh Tea",
        "얼그레이 티백",
        "자스민티 20개입",
    ],
)
def test_provider_supports_product_name(
    product_name: str,
) -> None:
    assert TeaKnowledgeProvider().supports(
        product_name=product_name
    )


@pytest.mark.parametrize(
    "product_name",
    [
        "국내산 한우 등심",
        "프랑스 브리 치즈",
        "에티오피아 아라비카 원두",
        "카베르네 소비뇽 레드 와인",
        "훈제오리 슬라이스",
        "사과 5kg",
        "",
    ],
)
def test_provider_rejects_unrelated_product(
    product_name: str,
) -> None:
    assert not TeaKnowledgeProvider().supports(
        product_name=product_name
    )


def test_provider_supports_returns_false_without_input() -> None:
    assert TeaKnowledgeProvider().supports() is False


def test_provider_analyzes_complete_product() -> None:
    result = TeaKnowledgeProvider().analyze(
        _complete_product()
    )

    assert isinstance(
        result,
        FoodKnowledgeResult,
    )

    assert result.category_id == "tea"
    assert result.category_name == "차"
    assert result.product_name == (
        "제주 야부키타 증제 "
        "비산화 감칠맛 녹차"
    )

    assert result.attributes["tea_type"] == "green"
    assert result.attributes["origin"] == "jeju"
    assert result.attributes["variety"] == "yabukita"
    assert result.attributes["processing"] == "steamed"
    assert result.attributes["oxidation"] == "unoxidized"
    assert result.attributes["flavor"] == "umami"

    assert result.scores["quality"] == 80.0
    assert result.scores["price"] == 70.0
    assert result.scores["trust"] == 90.0

    # 현재 Tea Registry YAML score는 모두 0이다.
    assert result.scores["knowledge"] == 0.0

    # 80*0.20 + 70*0.15 + 90*0.15
    assert result.final_score == 40.0

    assert 0.0 <= result.confidence <= 1.0
    assert result.reasons

    assert (
        "Tea Registry 기반 평가 점수가 "
        "아직 설정되지 않았거나 "
        "계산할 수 없습니다."
        in result.warnings
    )


def test_provider_orchestration_metadata() -> None:
    result = TeaKnowledgeProvider().analyze(
        _complete_product()
    )

    assert result.metadata == {
        "provider_id": "tea",
        "provider": "TeaKnowledgeProvider",
        "parser": "TeaParser",
        "priority": None,
        "query": None,
        "user_mode": None,
        "season": None,
        "region": None,
        "matched_field_count": 6,
        "expected_field_count": 6,
        "is_complete": True,
        "is_usable": True,
    }


def test_provider_context_metadata() -> None:
    context = FoodKnowledgeContext(
        query="제주 녹차 추천",
        priority="quality",
        user_mode="expert",
        season="summer",
        region="Seoul",
        metadata={
            "request_id": "tea-test",
        },
    )

    result = TeaKnowledgeProvider().analyze(
        _complete_product(),
        context=context,
    )

    assert result.metadata["query"] == (
        "제주 녹차 추천"
    )
    assert result.metadata["priority"] == "quality"
    assert result.metadata["user_mode"] == "expert"
    assert result.metadata["season"] == "summer"
    assert result.metadata["region"] == "Seoul"


def test_provider_analyzes_partial_product() -> None:
    result = TeaKnowledgeProvider().analyze(
        {
            "product_name": (
                "다즐링 꽃향 차 100g"
            ),
            "weight": "100g",
            "quality_score": 80,
        }
    )

    assert result.attributes["tea_type"] is None
    assert result.attributes["origin"] == "darjeeling"
    assert result.attributes["flavor"] == "floral"
    assert result.attributes["weight"] == "100g"

    assert result.metadata[
        "matched_field_count"
    ] == 2
    assert result.metadata["is_complete"] is False
    assert result.metadata["is_usable"] is True

    assert result.scores["quality"] == 80.0
    assert result.scores["knowledge"] == 0.0

    # 80 * 0.20
    assert result.final_score == 16.0

    assert result.reasons
    assert result.warnings


def test_provider_analyzes_unknown_product() -> None:
    result = TeaKnowledgeProvider().analyze(
        {
            "product_name": "일반 식품 상품",
        }
    )

    assert result.attributes["tea_type"] is None
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
    result = TeaKnowledgeProvider().analyze(
        {
            "title": "제주 녹차",
        }
    )

    assert result.product_name == "제주 녹차"
    assert result.attributes["tea_type"] == "green"
    assert result.attributes["origin"] == "jeju"


def test_provider_preserves_raw_product_copy() -> None:
    product = _complete_product()

    result = TeaKnowledgeProvider().analyze(
        product
    )

    assert result.raw_product == product
    assert result.raw_product is not product


def test_provider_does_not_mutate_product() -> None:
    product = _complete_product()
    product_before = deepcopy(product)

    TeaKnowledgeProvider().analyze(
        product
    )

    assert product == product_before


def test_provider_result_collections_are_independent() -> None:
    provider = TeaKnowledgeProvider()
    product = _complete_product()

    first = provider.analyze(product)
    second = provider.analyze(product)

    assert first.to_dict() == second.to_dict()
    assert first is not second

    assert first.attributes is not second.attributes
    assert first.scores is not second.scores
    assert first.reasons is not second.reasons
    assert first.warnings is not second.warnings
    assert first.raw_product is not second.raw_product


def test_provider_result_is_serializable() -> None:
    result = TeaKnowledgeProvider().analyze(
        _complete_product()
    )

    payload = result.to_dict()

    assert payload["category_id"] == "tea"
    assert payload["category_name"] == "차"
    assert payload["attributes"]["tea_type"] == "green"
    assert payload["attributes"]["origin"] == "jeju"
    assert payload["scores"]["knowledge"] == 0.0
    assert payload["final_score"] == 40.0


def test_provider_is_deterministic() -> None:
    provider = TeaKnowledgeProvider()
    product = _complete_product()

    first = provider.analyze(product)
    second = provider.analyze(product)

    assert first.to_dict() == second.to_dict()


def test_provider_rejects_non_mapping() -> None:
    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        TeaKnowledgeProvider().analyze(
            "제주 녹차"  # type: ignore[arg-type]
        )


def test_provider_rejects_empty_mapping() -> None:
    with pytest.raises(
        ValueError,
        match="product must not be empty",
    ):
        TeaKnowledgeProvider().analyze({})


def test_provider_rejects_mapping_without_usable_text() -> None:
    with pytest.raises(
        ValueError,
        match="usable text field",
    ):
        TeaKnowledgeProvider().analyze(
            {
                "price": 10000,
                "review_count": 10,
            }
        )


@pytest.mark.parametrize(
    (
        "product_name",
        "expected",
    ),
    [
        (
            "Japanese Green Tea",
            True,
        ),
        (
            "Premium Black Tea",
            True,
        ),
        (
            "에티오피아 아라비카 원두",
            False,
        ),
        (
            "Steak Seasoning",
            False,
        ),
        (
            "Teak Wood Table",
            False,
        ),
    ],
)
def test_provider_alias_matching_respects_token_boundaries(
    product_name: str,
    expected: bool,
) -> None:
    observed = TeaKnowledgeProvider().supports(
        product_name=product_name
    )

    assert observed is expected
