from __future__ import annotations

from copy import deepcopy

import pytest

from app.services.food.knowledge.base import (
    FoodKnowledgeProvider,
)
from app.services.food.knowledge.herb_spice.parser import (
    HerbSpiceParser,
)
from app.services.food.knowledge.herb_spice.provider import (
    HerbSpiceKnowledgeProvider,
)
from app.services.food.knowledge.models import (
    FoodKnowledgeContext,
    FoodKnowledgeResult,
    FoodRuleResult,
)


def _complete_product() -> dict[str, object]:
    return {
        "product_name": (
            "프랑스산 건조 로즈마리 "
            "오븐 구이용"
        ),
        "classification": "herb",
        "ingredient": "rosemary",
        "origin": "France",
        "country": "France",
        "country_code": "FR",
        "product_form": "dried herb",
        "recommended_usage": "roasting",
        "weight": "50g",
        "packaging_type": "zip pouch",
        "organic": True,
        "certifications": [
            "Organic",
            "HACCP",
        ],
        "additives": [],
        "salt_added": False,
        "quality_score": 80,
        "price_score": 70,
        "trust_score": 90,
    }


def test_provider_contract() -> None:
    provider = HerbSpiceKnowledgeProvider()

    assert isinstance(
        provider,
        FoodKnowledgeProvider,
    )
    assert provider.category_id == "herb_spice"
    assert provider.category_name == "허브·향신료"
    assert provider.aliases
    assert isinstance(
        provider.parser,
        HerbSpiceParser,
    )


def test_provider_parser_injection() -> None:
    parser = HerbSpiceParser()

    provider = HerbSpiceKnowledgeProvider(
        parser=parser
    )

    assert provider.parser is parser


@pytest.mark.parametrize(
    "category_id",
    [
        "herb_spice",
        "HERB_SPICE",
        " herb spice ",
        "herb & spice",
        "허브",
        "향신료",
        "허브·향신료",
    ],
)
def test_supports_category_aliases(
    category_id: str,
) -> None:
    assert HerbSpiceKnowledgeProvider().supports(
        category_id=category_id
    )


@pytest.mark.parametrize(
    "product_name",
    [
        "프랑스산 건조 로즈마리",
        "이탈리아산 바질 잎",
        "인도산 큐민 파우더",
        "베트남 통후추",
        "스페인산 파프리카 파우더",
        "국내산 고춧가루",
        "일본산 와사비 분말",
        "Cardamom Pod",
        "Cinnamon Bark",
    ],
)
def test_supports_product_names(
    product_name: str,
) -> None:
    assert HerbSpiceKnowledgeProvider().supports(
        product_name=product_name
    )


@pytest.mark.parametrize(
    "product_name",
    [
        "국내산 한우 등심",
        "프랑스 브리 치즈",
        "에티오피아 아라비카 원두",
        "카베르네 소비뇽 레드 와인",
        "제주 녹차",
        "훈제오리 슬라이스",
        "고당도 사과",
        "",
    ],
)
def test_rejects_unrelated_products(
    product_name: str,
) -> None:
    assert not HerbSpiceKnowledgeProvider().supports(
        product_name=product_name
    )


@pytest.mark.parametrize(
    "product_name",
    [
        "양조 간장 500ml",
        "사과 식초",
        "전통 된장",
        "고추장 1kg",
        "와사비 소스",
        "튜브 와사비 페이스트",
        "페퍼민트 허브티",
        "Herbal Infusion Tea",
    ],
)
def test_rejects_condiment_and_tea_products(
    product_name: str,
) -> None:
    assert not HerbSpiceKnowledgeProvider().supports(
        product_name=product_name
    )


def test_supports_returns_false_without_input() -> None:
    assert (
        HerbSpiceKnowledgeProvider().supports()
        is False
    )


def test_analyze_returns_common_result() -> None:
    result = HerbSpiceKnowledgeProvider().analyze(
        _complete_product()
    )

    assert isinstance(
        result,
        FoodKnowledgeResult,
    )
    assert result.category_id == "herb_spice"
    assert result.category_name == "허브·향신료"
    assert result.product_name == (
        _complete_product()["product_name"]
    )


def test_analyze_complete_product_contract() -> None:
    result = HerbSpiceKnowledgeProvider().analyze(
        _complete_product()
    )

    assert result.attributes["classification"] == (
        "herb"
    )
    assert result.attributes["ingredient"] == (
        "rosemary"
    )
    assert result.attributes["origin"] == "france"
    assert result.attributes["form"] == "dried"
    assert result.attributes["usage"] == "roasting"

    assert result.scores["quality"] == 80.0
    assert result.scores["price"] == 70.0
    assert result.scores["trust"] == 90.0
    assert result.scores["knowledge"] == 0.0

    assert result.final_score == 40.0
    assert result.confidence > 0.0

    assert result.reasons
    assert result.warnings == []
    assert result.rules
    assert all(
        isinstance(rule, FoodRuleResult)
        for rule in result.rules
    )


def test_analyze_metadata_contract() -> None:
    context = FoodKnowledgeContext(
        query="유기농 로즈마리",
        priority="quality",
        user_mode="expert",
        season="summer",
        region="KR",
        metadata={
            "session_id": "test-session",
        },
    )

    result = HerbSpiceKnowledgeProvider().analyze(
        _complete_product(),
        context=context,
    )

    assert result.metadata["provider_id"] == (
        "herb_spice"
    )
    assert result.metadata["provider"] == (
        "HerbSpiceKnowledgeProvider"
    )
    assert result.metadata["parser"] == (
        "HerbSpiceParser"
    )
    assert result.metadata["priority"] == "quality"
    assert result.metadata["query"] == (
        "유기농 로즈마리"
    )
    assert result.metadata["user_mode"] == "expert"
    assert result.metadata["season"] == "summer"
    assert result.metadata["region"] == "KR"
    assert result.metadata["context_metadata"] == {
        "session_id": "test-session",
    }

    assert (
        result.metadata["matched_field_count"]
        == 4
    )
    assert (
        result.metadata["expected_field_count"]
        == 4
    )
    assert result.metadata["is_complete"] is True
    assert result.metadata["is_usable"] is True
    assert (
        result.metadata["classification"]
        == "herb"
    )
    assert (
        result.metadata["ingredient"]
        == "rosemary"
    )
    assert result.metadata["rule_flags"]
    assert result.metadata["rule_metadata"]
    assert result.metadata[
        "activated_rule_ids"
    ]


def test_analyze_spice_product() -> None:
    result = HerbSpiceKnowledgeProvider().analyze(
        {
            "product_name": (
                "인도산 큐민 파우더 스튜용"
            ),
            "classification": "spice",
            "ingredient": "cumin",
            "origin": "India",
            "product_form": "powder",
            "recommended_usage": "stew",
            "quality_score": 75,
            "price_score": 65,
            "trust_score": 85,
        }
    )

    assert result.attributes["classification"] == (
        "spice"
    )
    assert result.attributes["ingredient"] == (
        "cumin"
    )
    assert result.attributes["spice_heat_level"] == (
        1.0
    )
    assert (
        "herb_fresh_available"
        not in result.attributes
    )


def test_analyze_partial_product() -> None:
    result = HerbSpiceKnowledgeProvider().analyze(
        {
            "product_name": (
                "프랑스산 건조 로즈마리"
            ),
        }
    )

    assert result.attributes["ingredient"] == (
        "rosemary"
    )
    assert result.attributes["origin"] == "france"
    assert result.attributes["form"] == "dried"
    assert result.metadata["is_complete"] is False
    assert result.metadata["is_usable"] is True
    assert result.warnings


def test_analyze_unknown_product() -> None:
    result = HerbSpiceKnowledgeProvider().analyze(
        {
            "product_name": "일반 식품 상품",
        }
    )

    assert result.attributes["classification"] is None
    assert result.attributes["ingredient"] is None
    assert result.attributes["origin"] is None
    assert result.attributes["form"] is None
    assert result.attributes["usage"] is None

    assert result.metadata["is_complete"] is False
    assert result.metadata["is_usable"] is False
    assert result.final_score == 0.0
    assert result.reasons == []
    assert result.warnings


def test_analyze_conflict_product() -> None:
    result = HerbSpiceKnowledgeProvider().analyze(
        {
            "product_name": (
                "생고수 고수씨 혼합 향신료"
            ),
        }
    )

    assert (
        result.metadata["ingredient_conflict"]
        is True
    )
    assert any(
        rule.rule_id
        == "herb_spice.ingredient_conflict"
        for rule in result.rules
    )
    assert any(
        "동시에 탐지" in warning
        for warning in result.warnings
    )


def test_warning_rules_use_warning_severity() -> None:
    result = HerbSpiceKnowledgeProvider().analyze(
        {
            "product_name": "로즈마리",
            "additives": [
                "소금",
            ],
            "salt_added": True,
        }
    )

    warning_rules = {
        rule.rule_id: rule.severity
        for rule in result.rules
        if rule.severity == "warning"
    }

    assert (
        warning_rules[
            "herb_spice.additives_present"
        ]
        == "warning"
    )
    assert (
        warning_rules[
            "herb_spice.salt_added"
        ]
        == "warning"
    )


def test_raw_product_is_a_copy() -> None:
    product = _complete_product()

    result = HerbSpiceKnowledgeProvider().analyze(
        product
    )

    assert result.raw_product == product
    assert result.raw_product is not product


def test_analyze_does_not_mutate_input() -> None:
    product = _complete_product()
    before = deepcopy(product)

    HerbSpiceKnowledgeProvider().analyze(
        product
    )

    assert product == before


def test_analysis_is_deterministic() -> None:
    provider = HerbSpiceKnowledgeProvider()
    product = _complete_product()

    first = provider.analyze(product)
    second = provider.analyze(product)

    assert first.to_dict() == second.to_dict()
    assert first is not second
    assert first.attributes is not second.attributes
    assert first.scores is not second.scores
    assert first.reasons is not second.reasons
    assert first.warnings is not second.warnings
    assert first.rules is not second.rules


def test_analyze_rejects_non_mapping() -> None:
    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        HerbSpiceKnowledgeProvider().analyze(
            "로즈마리"  # type: ignore[arg-type]
        )


def test_analyze_rejects_empty_mapping() -> None:
    with pytest.raises(
        ValueError,
        match="product must not be empty",
    ):
        HerbSpiceKnowledgeProvider().analyze({})


def test_analyze_rejects_invalid_context() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "context must be "
            "FoodKnowledgeContext or None"
        ),
    ):
        HerbSpiceKnowledgeProvider().analyze(
            {
                "product_name": "로즈마리",
            },
            context={},  # type: ignore[arg-type]
        )
