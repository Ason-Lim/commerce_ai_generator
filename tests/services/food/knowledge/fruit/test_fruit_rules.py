from __future__ import annotations

from app.services.food.knowledge.fruit.rules import (
    build_fruit_rules,
    evaluate_fruit_rules,
)


def _rule_ids(
    attributes: dict,
    scores: dict[str, float],
) -> set[str]:
    return {
        rule.rule_id
        for rule in evaluate_fruit_rules(
            attributes,
            scores,
        )
    }


def test_missing_brix_rule() -> None:
    ids = _rule_ids(
        {},
        {},
    )

    assert "fruit.missing_brix" in ids


def test_normal_brix_rule() -> None:
    ids = _rule_ids(
        {
            "brix": 10.0,
        },
        {},
    )

    assert "fruit.normal_brix" in ids


def test_good_brix_rule() -> None:
    ids = _rule_ids(
        {
            "brix": 12.0,
        },
        {},
    )

    assert "fruit.good_brix" in ids


def test_high_brix_rule() -> None:
    ids = _rule_ids(
        {
            "brix": 14.0,
        },
        {},
    )

    assert "fruit.high_brix" in ids


def test_missing_origin_rule() -> None:
    ids = _rule_ids(
        {},
        {},
    )

    assert "fruit.missing_origin" in ids


def test_origin_available_rule() -> None:
    ids = _rule_ids(
        {
            "origin": "제주",
        },
        {},
    )

    assert "fruit.origin_available" in ids


def test_missing_grade_rule() -> None:
    ids = _rule_ids(
        {},
        {},
    )

    assert "fruit.missing_grade" in ids


def test_grade_available_rule() -> None:
    ids = _rule_ids(
        {
            "grade": "특품",
        },
        {},
    )

    assert "fruit.grade_available" in ids


def test_high_quality_score_rule() -> None:
    ids = _rule_ids(
        {},
        {
            "quality": 80.0,
        },
    )

    assert "fruit.high_quality_score" in ids


def test_high_price_score_rule() -> None:
    ids = _rule_ids(
        {},
        {
            "price": 80.0,
        },
    )

    assert "fruit.high_price_value" in ids


def test_high_trust_score_rule() -> None:
    ids = _rule_ids(
        {},
        {
            "trust": 80.0,
        },
    )

    assert "fruit.high_trust_score" in ids


def test_low_information_rule() -> None:
    ids = _rule_ids(
        {},
        {
            "information": 49.99,
        },
    )

    assert "fruit.low_information" in ids


def test_information_boundary_does_not_warn() -> None:
    ids = _rule_ids(
        {},
        {
            "information": 50.0,
        },
    )

    assert "fruit.low_information" not in ids


def test_keyword_rules() -> None:
    ids = _rule_ids(
        {
            "detected_keywords": [
                "고당도",
                "산지직송",
                "유기농",
            ],
        },
        {},
    )

    assert "fruit.keyword.고당도" in ids
    assert "fruit.keyword.산지직송" in ids
    assert "fruit.keyword.유기농" in ids


def test_build_fruit_rules_splits_messages() -> None:
    rules, reasons, warnings = (
        build_fruit_rules(
            {
                "brix": None,
                "origin": None,
                "grade": None,
            },
            {
                "information": 0.0,
            },
        )
    )

    assert rules
    assert warnings
    assert isinstance(reasons, list)
