from __future__ import annotations

import pytest

from app.services.food.knowledge.herb_spice.form_registry import (
    HerbSpiceFormRegistry,
)
from app.services.food.knowledge.herb_spice.herb_registry import (
    HerbRegistry,
)
from app.services.food.knowledge.herb_spice.origin_registry import (
    HerbSpiceOriginRegistry,
)
from app.services.food.knowledge.herb_spice.parser import (
    HerbSpiceParser,
)
from app.services.food.knowledge.herb_spice.parser_models import (
    HerbSpiceParseResult,
)
from app.services.food.knowledge.herb_spice.spice_registry import (
    SpiceRegistry,
)
from app.services.food.knowledge.herb_spice.usage_registry import (
    HerbSpiceUsageRegistry,
)


def test_parser_registry_injection() -> None:
    herb_registry = HerbRegistry()
    spice_registry = SpiceRegistry()
    origin_registry = HerbSpiceOriginRegistry()
    form_registry = HerbSpiceFormRegistry()
    usage_registry = HerbSpiceUsageRegistry()

    parser = HerbSpiceParser(
        herb_registry=herb_registry,
        spice_registry=spice_registry,
        origin_registry=origin_registry,
        form_registry=form_registry,
        usage_registry=usage_registry,
    )

    assert parser.herb_registry is herb_registry
    assert parser.spice_registry is spice_registry
    assert parser.origin_registry is origin_registry
    assert parser.form_registry is form_registry
    assert parser.usage_registry is usage_registry


def test_parse_complete_herb_text() -> None:
    result = HerbSpiceParser().parse(
        "프랑스산 건조 로즈마리 오븐 구이용"
    )

    assert isinstance(
        result,
        HerbSpiceParseResult,
    )
    assert result.classification == "herb"
    assert result.ingredient == "rosemary"
    assert result.origin == "france"
    assert result.form == "dried"
    assert result.usage == "roasting"

    assert result.matched_field_count == 4
    assert result.is_complete is True
    assert result.is_usable is True
    assert result.confidence > 0.0
    assert result.has_ingredient_conflict is False
    assert result.warnings == []


def test_parse_complete_spice_text() -> None:
    result = HerbSpiceParser().parse(
        "인도산 큐민 파우더 스튜용"
    )

    assert result.classification == "spice"
    assert result.ingredient == "cumin"
    assert result.origin == "india"
    assert result.form == "powder"
    assert result.usage == "stew"
    assert result.is_complete is True
    assert result.is_usable is True


def test_parse_product_uses_structured_fields() -> None:
    result = HerbSpiceParser().parse_product(
        {
            "product_name": "프리미엄 시즈닝",
            "classification": "herb",
            "ingredient": "rosemary",
            "origin": "France",
            "product_form": "dried herb",
            "recommended_usage": "roasting",
        }
    )

    assert result.classification == "herb"
    assert result.ingredient == "rosemary"
    assert result.origin == "france"
    assert result.form == "dried"
    assert result.usage == "roasting"

    assert result.metadata["source_type"] == "mapping"
    assert (
        result.metadata[
            "structured_field_priority"
        ]
        is True
    )
    assert (
        result.metadata["classification_hint"]
        == "herb"
    )


def test_classification_hint_limits_fallback_registry() -> None:
    result = HerbSpiceParser().parse_product(
        {
            "product_name": "로즈마리 큐민 혼합",
            "classification": "spice",
            "ingredient": "cumin",
        }
    )

    assert result.classification == "spice"
    assert result.ingredient == "cumin"
    assert result.spice_match is not None


def test_parser_detects_each_dimension() -> None:
    parser = HerbSpiceParser()

    herb = parser.parse("로즈마리")
    spice = parser.parse("큐민")
    origin = parser.parse("프랑스산 상품")
    form = parser.parse("건조 허브")
    usage = parser.parse("구이용 시즈닝")

    assert herb.ingredient == "rosemary"
    assert herb.classification == "herb"

    assert spice.ingredient == "cumin"
    assert spice.classification == "spice"

    assert origin.origin == "france"
    assert form.form == "dried"
    assert usage.usage == "roasting"


def test_ingredient_only_is_usable() -> None:
    result = HerbSpiceParser().parse(
        "로즈마리"
    )

    assert result.ingredient == "rosemary"
    assert result.is_usable is True
    assert result.is_complete is False
    assert result.warnings


def test_origin_only_is_not_usable() -> None:
    result = HerbSpiceParser().parse(
        "프랑스산 일반 상품"
    )

    assert result.origin == "france"
    assert result.ingredient is None
    assert result.is_usable is False
    assert result.warnings


def test_two_supporting_fields_are_usable() -> None:
    result = HerbSpiceParser().parse(
        "프랑스산 건조 상품"
    )

    assert result.origin == "france"
    assert result.form == "dried"
    assert result.matched_field_count == 2
    assert result.is_usable is True


def test_herb_spice_conflict_is_preserved() -> None:
    parser = HerbSpiceParser()
    text = "생고수 고수씨 혼합 향신료"

    first = parser.parse(text)
    second = parser.parse(text)

    assert first.herb_match is not None
    assert first.spice_match is not None
    assert first.has_ingredient_conflict is True
    assert first.metadata[
        "ingredient_conflict"
    ] is True

    assert first.classification in {
        "herb",
        "spice",
    }
    assert first.ingredient in {
        "cilantro",
        "coriander_seed",
    }
    assert first.warnings
    assert first.to_dict() == second.to_dict()


def test_detected_keywords_are_preserved() -> None:
    result = HerbSpiceParser().parse(
        "프랑스산 건조 로즈마리 오븐 구이"
    )

    assert "프랑스산" in result.detected_keywords
    assert "건조 허브" not in result.detected_keywords
    assert "로즈마리" in result.detected_keywords
    assert "오븐 구이" in result.detected_keywords


def test_unknown_text_returns_unusable() -> None:
    result = HerbSpiceParser().parse(
        "상품 정보가 없는 일반 문자열"
    )

    assert result.classification is None
    assert result.ingredient is None
    assert result.origin is None
    assert result.form is None
    assert result.usage is None

    assert result.matched_field_count == 0
    assert result.confidence == 0.0
    assert result.has_match is False
    assert result.is_usable is False
    assert result.warnings


@pytest.mark.parametrize(
    "text",
    [
        "국내산 한우 등심",
        "프랑스 브리 치즈",
        "에티오피아 아라비카 원두",
        "카베르네 소비뇽 레드 와인",
        "훈제오리 슬라이스",
        "간장 500ml",
        "사과 식초",
    ],
)
def test_parser_domain_boundary(
    text: str,
) -> None:
    result = HerbSpiceParser().parse(text)

    assert result.ingredient is None


def test_parser_metadata_contract() -> None:
    result = HerbSpiceParser().parse(
        "프랑스산 건조 로즈마리"
    )

    assert (
        result.metadata["category_id"]
        == "herb_spice"
    )
    assert result.metadata["source_type"] == "text"
    assert (
        result.metadata[
            "structured_field_priority"
        ]
        is False
    )
    assert (
        result.metadata[
            "expected_field_count"
        ]
        == 4
    )
    assert (
        result.metadata[
            "matched_field_count"
        ]
        == 3
    )
    assert result.metadata["is_complete"] is False


def test_confidences_are_bounded() -> None:
    result = HerbSpiceParser().parse(
        "프랑스산 건조 로즈마리 구이용"
    )

    for confidence in (
        result.confidence,
        result.classification_confidence,
        result.ingredient_confidence,
        result.origin_confidence,
        result.form_confidence,
        result.usage_confidence,
    ):
        assert 0.0 <= confidence <= 1.0


def test_parse_rejects_empty_text() -> None:
    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        HerbSpiceParser().parse("")


def test_parse_product_rejects_non_mapping() -> None:
    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        HerbSpiceParser().parse_product(
            "로즈마리"  # type: ignore[arg-type]
        )


def test_parse_product_rejects_empty_mapping() -> None:
    with pytest.raises(
        ValueError,
        match="product must not be empty",
    ):
        HerbSpiceParser().parse_product({})


def test_parse_product_rejects_no_usable_fields() -> None:
    with pytest.raises(
        ValueError,
        match="usable text field",
    ):
        HerbSpiceParser().parse_product(
            {
                "price": 10000,
                "review_count": 10,
            }
        )


def test_parsing_is_deterministic() -> None:
    parser = HerbSpiceParser()
    text = (
        "프랑스산 건조 로즈마리 "
        "오븐 구이용"
    )

    first = parser.parse(text)
    second = parser.parse(text)

    assert first.to_dict() == second.to_dict()
    assert first is not second
