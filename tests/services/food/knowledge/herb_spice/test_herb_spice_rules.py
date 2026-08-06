from __future__ import annotations

from copy import deepcopy

import pytest

from app.services.food.knowledge.herb_spice.attributes import (
    build_herb_spice_attributes,
)
from app.services.food.knowledge.herb_spice.parser import (
    HerbSpiceParser,
)
from app.services.food.knowledge.herb_spice.rules import (
    HERB_SPICE_RULE_IDS,
    build_herb_spice_reasons,
    build_herb_spice_rule_flags,
    build_herb_spice_warnings,
    evaluate_herb_spice_rules,
)
from app.services.food.knowledge.herb_spice.scoring import (
    calculate_herb_spice_scores,
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
        "product_form": "dried herb",
        "recommended_usage": "roasting",
        "quality_score": 80,
        "price_score": 70,
        "trust_score": 90,
        "organic": True,
        "certifications": [
            "Organic",
            "HACCP",
        ],
        "additives": [],
        "salt_added": False,
    }


def _pipeline(
    product: dict[str, object],
) -> tuple[
    object,
    dict[str, object],
    dict[str, float],
]:
    parse_result = (
        HerbSpiceParser().parse_product(
            product
        )
    )

    attributes = build_herb_spice_attributes(
        product=product,
        parse_result=parse_result,
    )

    scores = calculate_herb_spice_scores(
        product=product,
        parse_result=parse_result,
    )

    return (
        parse_result,
        attributes,
        scores,
    )


def test_rule_ids_are_unique() -> None:
    assert len(HERB_SPICE_RULE_IDS) == len(
        set(HERB_SPICE_RULE_IDS)
    )

    assert all(
        rule_id.startswith(
            "herb_spice."
        )
        for rule_id in HERB_SPICE_RULE_IDS
    )


def test_complete_product_rules() -> None:
    product = _complete_product()
    parse_result, attributes, scores = (
        _pipeline(product)
    )

    result = evaluate_herb_spice_rules(
        product=product,
        parse_result=parse_result,
        attributes=attributes,
        scores=scores,
    )

    assert (
        "herb_spice.ingredient_identified"
        in result["rules"]
    )
    assert (
        "herb_spice.complete_profile"
        in result["rules"]
    )
    assert (
        "herb_spice.origin_identified"
        in result["rules"]
    )
    assert (
        "herb_spice.form_identified"
        in result["rules"]
    )
    assert (
        "herb_spice.usage_identified"
        in result["rules"]
    )
    assert (
        "herb_spice.organic_declared"
        in result["rules"]
    )
    assert (
        "herb_spice.certification_present"
        in result["rules"]
    )

    assert (
        result["flags"]["complete_profile"]
        is True
    )
    assert (
        result["flags"]["partial_profile"]
        is False
    )
    assert (
        result["flags"][
            "ingredient_conflict"
        ]
        is False
    )
    assert (
        result["flags"][
            "product_information_missing"
        ]
        is False
    )

    assert result["reasons"]
    assert result["warnings"] == []


def test_partial_product_rules() -> None:
    product = {
        "product_name": "프랑스산 건조 상품",
    }

    parse_result, attributes, scores = (
        _pipeline(product)
    )

    result = evaluate_herb_spice_rules(
        product=product,
        parse_result=parse_result,
        attributes=attributes,
        scores=scores,
    )

    assert (
        "herb_spice.partial_profile"
        in result["rules"]
    )
    assert (
        "herb_spice.complete_profile"
        not in result["rules"]
    )

    assert (
        result["flags"]["partial_profile"]
        is True
    )
    assert (
        result["flags"]["complete_profile"]
        is False
    )
    assert result["warnings"]


def test_unknown_product_rules() -> None:
    product = {
        "product_name": "일반 상품",
    }

    parse_result, attributes, scores = (
        _pipeline(product)
    )

    result = evaluate_herb_spice_rules(
        product=product,
        parse_result=parse_result,
        attributes=attributes,
        scores=scores,
    )

    assert (
        "herb_spice.product_information_missing"
        in result["rules"]
    )
    assert (
        result["flags"][
            "product_information_missing"
        ]
        is True
    )
    assert result["reasons"] == []
    assert result["warnings"]


def test_conflict_rule() -> None:
    product = {
        "product_name": (
            "생고수 고수씨 혼합 향신료"
        ),
    }

    parse_result, attributes, scores = (
        _pipeline(product)
    )

    result = evaluate_herb_spice_rules(
        product=product,
        parse_result=parse_result,
        attributes=attributes,
        scores=scores,
    )

    assert (
        parse_result.has_ingredient_conflict
        is True
    )
    assert (
        "herb_spice.ingredient_conflict"
        in result["rules"]
    )
    assert (
        result["flags"][
            "ingredient_conflict"
        ]
        is True
    )
    assert any(
        "동시에 탐지" in warning
        for warning in result["warnings"]
    )


def test_additives_rule() -> None:
    product = _complete_product()
    product["additives"] = [
        "소금",
        "향료",
    ]

    parse_result, attributes, scores = (
        _pipeline(product)
    )

    result = evaluate_herb_spice_rules(
        product=product,
        parse_result=parse_result,
        attributes=attributes,
        scores=scores,
    )

    assert (
        "herb_spice.additives_present"
        in result["rules"]
    )
    assert (
        result["flags"]["additives_present"]
        is True
    )
    assert any(
        "소금" in warning
        for warning in result["warnings"]
    )


def test_salt_added_rule() -> None:
    product = _complete_product()
    product["salt_added"] = True

    parse_result, attributes, scores = (
        _pipeline(product)
    )

    result = evaluate_herb_spice_rules(
        product=product,
        parse_result=parse_result,
        attributes=attributes,
        scores=scores,
    )

    assert (
        "herb_spice.salt_added"
        in result["rules"]
    )
    assert (
        result["flags"]["salt_added"]
        is True
    )
    assert any(
        "소금 첨가" in warning
        for warning in result["warnings"]
    )


def test_premium_ingredient_rule() -> None:
    product = {
        "product_name": (
            "일본산 와사비 분말"
        ),
        "classification": "spice",
        "ingredient": "wasabi",
        "origin": "Japan",
        "product_form": "powder",
    }

    parse_result, attributes, scores = (
        _pipeline(product)
    )

    result = evaluate_herb_spice_rules(
        product=product,
        parse_result=parse_result,
        attributes=attributes,
        scores=scores,
    )

    assert (
        attributes["ingredient_premium"]
        is True
    )
    assert (
        "herb_spice.premium_ingredient"
        in result["rules"]
    )
    assert (
        result["flags"]["premium_ingredient"]
        is True
    )


def test_rule_metadata_contract() -> None:
    product = _complete_product()
    parse_result, attributes, scores = (
        _pipeline(product)
    )

    result = evaluate_herb_spice_rules(
        product=product,
        parse_result=parse_result,
        attributes=attributes,
        scores=scores,
    )

    metadata = result["metadata"]

    assert metadata["category_id"] == (
        "herb_spice"
    )
    assert metadata["classification"] == "herb"
    assert metadata["ingredient"] == "rosemary"
    assert metadata["matched_field_count"] == 4
    assert metadata["knowledge_score"] == 0.0
    assert (
        metadata["evaluated_rule_count"]
        == len(HERB_SPICE_RULE_IDS)
    )
    assert (
        metadata["activated_rule_count"]
        == len(result["rules"])
    )


def test_helper_functions_match_full_result() -> None:
    product = _complete_product()
    parse_result, attributes, scores = (
        _pipeline(product)
    )

    result = evaluate_herb_spice_rules(
        product=product,
        parse_result=parse_result,
        attributes=attributes,
        scores=scores,
    )

    assert build_herb_spice_reasons(
        product=product,
        parse_result=parse_result,
        attributes=attributes,
        scores=scores,
    ) == result["reasons"]

    assert build_herb_spice_warnings(
        product=product,
        parse_result=parse_result,
        attributes=attributes,
        scores=scores,
    ) == result["warnings"]

    assert build_herb_spice_rule_flags(
        product=product,
        parse_result=parse_result,
        attributes=attributes,
        scores=scores,
    ) == result["flags"]


def test_rule_results_are_deduplicated() -> None:
    product = _complete_product()
    product["certifications"] = [
        "Organic",
        "organic",
        "Organic",
    ]

    parse_result, attributes, scores = (
        _pipeline(product)
    )

    result = evaluate_herb_spice_rules(
        product=product,
        parse_result=parse_result,
        attributes=attributes,
        scores=scores,
    )

    assert len(result["rules"]) == len(
        set(result["rules"])
    )
    assert len(result["reasons"]) == len(
        {
            reason.casefold()
            for reason in result["reasons"]
        }
    )
    assert len(result["warnings"]) == len(
        {
            warning.casefold()
            for warning in result["warnings"]
        }
    )


def test_rules_do_not_mutate_inputs() -> None:
    product = _complete_product()
    product_before = deepcopy(product)

    parse_result, attributes, scores = (
        _pipeline(product)
    )

    parse_result_before = (
        parse_result.to_dict()
    )
    attributes_before = deepcopy(
        attributes
    )
    scores_before = deepcopy(scores)

    evaluate_herb_spice_rules(
        product=product,
        parse_result=parse_result,
        attributes=attributes,
        scores=scores,
    )

    assert product == product_before
    assert (
        parse_result.to_dict()
        == parse_result_before
    )
    assert attributes == attributes_before
    assert scores == scores_before


def test_rules_are_deterministic() -> None:
    product = _complete_product()
    parse_result, attributes, scores = (
        _pipeline(product)
    )

    first = evaluate_herb_spice_rules(
        product=product,
        parse_result=parse_result,
        attributes=attributes,
        scores=scores,
    )
    second = evaluate_herb_spice_rules(
        product=product,
        parse_result=parse_result,
        attributes=attributes,
        scores=scores,
    )

    assert first == second
    assert first is not second
    assert first["rules"] is not second["rules"]
    assert (
        first["reasons"]
        is not second["reasons"]
    )
    assert (
        first["warnings"]
        is not second["warnings"]
    )
    assert first["flags"] is not second["flags"]


def test_rules_reject_invalid_product() -> None:
    product = _complete_product()
    parse_result, attributes, scores = (
        _pipeline(product)
    )

    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        evaluate_herb_spice_rules(
            product="로즈마리",  # type: ignore[arg-type]
            parse_result=parse_result,
            attributes=attributes,
            scores=scores,
        )


def test_rules_reject_wrong_parse_result() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "parse_result must be "
            "HerbSpiceParseResult"
        ),
    ):
        evaluate_herb_spice_rules(
            product={
                "product_name": "로즈마리",
            },
            parse_result=object(),  # type: ignore[arg-type]
            attributes={},
            scores={},
        )


def test_rules_reject_invalid_attributes() -> None:
    product = _complete_product()
    parse_result, _, scores = (
        _pipeline(product)
    )

    with pytest.raises(
        TypeError,
        match="attributes must be a Mapping",
    ):
        evaluate_herb_spice_rules(
            product=product,
            parse_result=parse_result,
            attributes=[],  # type: ignore[arg-type]
            scores=scores,
        )


def test_rules_reject_invalid_scores() -> None:
    product = _complete_product()
    parse_result, attributes, _ = (
        _pipeline(product)
    )

    with pytest.raises(
        TypeError,
        match="scores must be a Mapping",
    ):
        evaluate_herb_spice_rules(
            product=product,
            parse_result=parse_result,
            attributes=attributes,
            scores=[],  # type: ignore[arg-type]
        )
